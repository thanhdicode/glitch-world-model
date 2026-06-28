from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .evaluate import auroc, average_precision, binary_metrics
from .kaggle_automation import FingerprintBuilder
from .lewm_adapter import sha256_file
from .lewm_lance_eval import MANIFEST_FIELDS, read_csv_rows, runtime_provenance, write_csv_rows
from .r5_tempglitch_eval import load_verified_r5_metrics_artifact, refuse_locked_test_path
from .statistics import bootstrap_metric_ci

FOLLOWUP_PROTOCOL = "tempglitch_followup_pair_disjoint_nonlocked"
FOLLOWUP_STATUS = "followup_complete"
FOLLOWUP_VALIDATOR_STATUS = "followup_validated"
CALIBRATION_NORMAL_EPISODE_IDS = (
    "Godot_Blinking_Normal_106",
    "Godot_Frozen_Animation_Platformer_Normal_107",
    "Godot_Shooting_Error_Normal_101",
    "Godot_Teleportation_TPS_Normal_1",
)
EXPECTED_EVALUATION_NORMAL_COUNT = 10
EXPECTED_EVALUATION_BUGGY_COUNT = 22
EXPECTED_CONFIG_COUNT = 60
FOLLOWUP_REQUIRED_FILES = (
    "followup_manifest.csv",
    "followup_manifest.sha256",
    "followup_episode_scores.csv",
    "followup_comparison.csv",
    "followup_metrics.json",
    "followup_provenance.json",
    "FOLLOWUP_REPORT.md",
    "followup_command.txt",
    "followup_validator_receipt.json",
)
FOLLOWUP_EPISODE_SCORE_FIELDS = (
    "method_family",
    "method",
    "window_scorer",
    "seed",
    "episode_aggregation",
    "source_episode_id",
    "source",
    "pair_id",
    "category",
    "label",
    "dataset_name",
    "evaluation_role",
    "window_count",
    "score",
)
FOLLOWUP_COMPARISON_FIELDS = (
    "method_family",
    "method",
    "window_scorer",
    "seed",
    "episode_aggregation",
    "raw_score_path",
    "raw_score_sha256",
    "checkpoint_sha256",
    "threshold",
    "threshold_source",
    "auroc",
    "auprc",
    "f1",
    "precision",
    "recall",
    "balanced_accuracy",
    "fpr_at_95_tpr",
    "true_positive",
    "false_positive",
    "false_negative",
    "true_negative",
    "calibration_episode_count",
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
    "calibration_episode_ids",
    "confidence_interval_group_key",
    "auroc_ci_lower",
    "auroc_ci_upper",
    "auroc_ci_valid_bootstrap_count",
    "f1_ci_lower",
    "f1_ci_upper",
    "f1_ci_valid_bootstrap_count",
)
FOLLOWUP_FLAGS = (
    "validation_buggy_used_for_fit_select",
    "locked_test_materialized",
    "locked_test_scored",
)
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_sha256(path: Path, output_path: Path | None = None) -> Path:
    sha_path = output_path or (
        path.with_suffix(path.suffix + ".sha256")
        if path.suffix
        else path.with_name(path.name + ".sha256")
    )
    sha_path.write_text(sha256_file(path) + "\n", encoding="utf-8")
    return sha_path


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _float_text(value: float | None) -> str:
    return "" if value is None else f"{float(value):.12g}"


def _config_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["method_family"],
        row["method"],
        row["window_scorer"],
        row["seed"],
        row["episode_aggregation"],
    )


def _resolve_repo_relative_path(path_text: str) -> Path:
    candidate = Path(path_text)
    return candidate if candidate.is_absolute() else (_REPO_ROOT / candidate)


def _retag_role(label: str, episode_id: str, calibration_episode_ids: set[str]) -> str:
    if label.lower() == "normal" and episode_id in calibration_episode_ids:
        return "calibration_normal"
    return "evaluation"


def _role_overlap(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    calibration_episode_ids: set[str] = set()
    evaluation_episode_ids: set[str] = set()
    calibration_pairs: set[str] = set()
    evaluation_pairs: set[str] = set()
    calibration_sources: set[str] = set()
    evaluation_sources: set[str] = set()
    for row in rows:
        target_episode_ids = (
            calibration_episode_ids
            if row["evaluation_role"] == "calibration_normal"
            else evaluation_episode_ids
        )
        target_pairs = (
            calibration_pairs
            if row["evaluation_role"] == "calibration_normal"
            else evaluation_pairs
        )
        target_sources = (
            calibration_sources
            if row["evaluation_role"] == "calibration_normal"
            else evaluation_sources
        )
        target_episode_ids.add(row["source_episode_id"])
        target_pairs.add(row["pair_id"])
        target_sources.add(row["source"])
    return {
        "source_episode_id_overlap": len(calibration_episode_ids & evaluation_episode_ids),
        "pair_id_overlap": len(calibration_pairs & evaluation_pairs),
        "source_overlap": len(calibration_sources & evaluation_sources),
    }


def build_followup_manifest_rows(
    r5_manifest_rows: list[dict[str, str]],
    *,
    calibration_episode_ids: tuple[str, ...] = CALIBRATION_NORMAL_EPISODE_IDS,
    expected_evaluation_normal_count: int = EXPECTED_EVALUATION_NORMAL_COUNT,
    expected_evaluation_buggy_count: int = EXPECTED_EVALUATION_BUGGY_COUNT,
) -> list[dict[str, str]]:
    calibration_set = set(calibration_episode_ids)
    normal_episodes = {
        row["source_episode_id"] for row in r5_manifest_rows if row["label"].lower() == "normal"
    }
    missing = sorted(calibration_set - normal_episodes)
    if missing:
        raise ValueError(f"Missing required calibration episode(s): {missing}")

    followup_rows: list[dict[str, str]] = []
    for row in r5_manifest_rows:
        followup_row = dict(row)
        followup_row["evaluation_role"] = _retag_role(
            row["label"], row["source_episode_id"], calibration_set
        )
        followup_rows.append(followup_row)
    validate_followup_manifest_rows(
        followup_rows,
        calibration_episode_ids=calibration_episode_ids,
        expected_evaluation_normal_count=expected_evaluation_normal_count,
        expected_evaluation_buggy_count=expected_evaluation_buggy_count,
    )
    return followup_rows


def build_followup_episode_rows(
    r5_episode_rows: list[dict[str, str]],
    *,
    calibration_episode_ids: tuple[str, ...] = CALIBRATION_NORMAL_EPISODE_IDS,
    expected_evaluation_normal_count: int = EXPECTED_EVALUATION_NORMAL_COUNT,
    expected_evaluation_buggy_count: int = EXPECTED_EVALUATION_BUGGY_COUNT,
    expected_config_count: int = EXPECTED_CONFIG_COUNT,
) -> list[dict[str, str]]:
    calibration_set = set(calibration_episode_ids)
    rows: list[dict[str, str]] = []
    for row in r5_episode_rows:
        updated = dict(row)
        updated["evaluation_role"] = _retag_role(
            row["label"], row["source_episode_id"], calibration_set
        )
        rows.append(updated)
    validate_followup_episode_rows(
        rows,
        calibration_episode_ids=calibration_episode_ids,
        expected_evaluation_normal_count=expected_evaluation_normal_count,
        expected_evaluation_buggy_count=expected_evaluation_buggy_count,
        expected_config_count=expected_config_count,
    )
    return rows


def validate_followup_manifest_rows(
    rows: list[dict[str, str]],
    *,
    calibration_episode_ids: tuple[str, ...] = CALIBRATION_NORMAL_EPISODE_IDS,
    expected_evaluation_normal_count: int = EXPECTED_EVALUATION_NORMAL_COUNT,
    expected_evaluation_buggy_count: int = EXPECTED_EVALUATION_BUGGY_COUNT,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("Follow-up manifest is empty.")
    seen_window_ids: set[str] = set()
    for row in rows:
        window_id = row["window_id"]
        if window_id in seen_window_ids:
            raise ValueError("Follow-up manifest contains duplicate window_id values.")
        seen_window_ids.add(window_id)
        if row["split"].lower() == "test" or "locked" in row["split"].lower():
            raise ValueError("Follow-up manifest must not contain locked-test rows.")
        if row["label"].lower() not in {"normal", "buggy"}:
            raise ValueError(f"Unexpected follow-up label: {row['label']}")
        if row["evaluation_role"] not in {"calibration_normal", "evaluation"}:
            raise ValueError(f"Unexpected follow-up role: {row['evaluation_role']}")

    calibration_set = set(calibration_episode_ids)
    calibration_episodes = {
        row["source_episode_id"] for row in rows if row["evaluation_role"] == "calibration_normal"
    }
    if calibration_episodes != calibration_set:
        raise ValueError(
            "Follow-up manifest calibration episodes do not match the frozen protocol: "
            f"{sorted(calibration_episodes)}"
        )

    if any(
        row["label"].lower() != "normal"
        for row in rows
        if row["evaluation_role"] == "calibration_normal"
    ):
        raise ValueError("Follow-up manifest calibration rows must all be normal.")

    evaluation_normal_episodes = {
        row["source_episode_id"]
        for row in rows
        if row["evaluation_role"] == "evaluation" and row["label"].lower() == "normal"
    }
    evaluation_buggy_episodes = {
        row["source_episode_id"]
        for row in rows
        if row["evaluation_role"] == "evaluation" and row["label"].lower() == "buggy"
    }
    if len(evaluation_normal_episodes) != expected_evaluation_normal_count:
        raise ValueError(
            "Follow-up manifest has the wrong normal-negative evaluation support: "
            f"{len(evaluation_normal_episodes)}"
        )
    if len(evaluation_buggy_episodes) != expected_evaluation_buggy_count:
        raise ValueError(
            "Follow-up manifest has the wrong buggy-positive evaluation support: "
            f"{len(evaluation_buggy_episodes)}"
        )

    overlap = _role_overlap(rows)
    if any(overlap.values()):
        raise ValueError(f"Follow-up manifest has cross-role overlap: {overlap}")

    return {
        "calibration_episode_ids": sorted(calibration_episodes),
        "calibration_episode_count": len(calibration_episodes),
        "evaluation_normal_episode_count": len(evaluation_normal_episodes),
        "evaluation_buggy_episode_count": len(evaluation_buggy_episodes),
        "role_overlap": overlap,
        "window_count": len(rows),
    }


def validate_followup_episode_rows(
    rows: list[dict[str, str]],
    *,
    calibration_episode_ids: tuple[str, ...] = CALIBRATION_NORMAL_EPISODE_IDS,
    expected_evaluation_normal_count: int = EXPECTED_EVALUATION_NORMAL_COUNT,
    expected_evaluation_buggy_count: int = EXPECTED_EVALUATION_BUGGY_COUNT,
    expected_config_count: int = EXPECTED_CONFIG_COUNT,
) -> dict[tuple[str, str, str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_config_key(row)].append(row)
    if len(grouped) != expected_config_count:
        raise ValueError(
            f"Follow-up episode scores expose {len(grouped)} configs; expected {expected_config_count}."
        )

    expected_calibration = set(calibration_episode_ids)
    for key, config_rows in grouped.items():
        calibration_episodes = {
            row["source_episode_id"]
            for row in config_rows
            if row["evaluation_role"] == "calibration_normal"
        }
        evaluation_normal_episodes = {
            row["source_episode_id"]
            for row in config_rows
            if row["evaluation_role"] == "evaluation" and row["label"].lower() == "normal"
        }
        evaluation_buggy_episodes = {
            row["source_episode_id"]
            for row in config_rows
            if row["evaluation_role"] == "evaluation" and row["label"].lower() == "buggy"
        }
        if calibration_episodes != expected_calibration:
            raise ValueError(f"Config {key} has inconsistent calibration episodes.")
        if len(evaluation_normal_episodes) != expected_evaluation_normal_count:
            raise ValueError(f"Config {key} has inconsistent normal evaluation support.")
        if len(evaluation_buggy_episodes) != expected_evaluation_buggy_count:
            raise ValueError(f"Config {key} has inconsistent buggy evaluation support.")
        overlap = _role_overlap(config_rows)
        if any(overlap.values()):
            raise ValueError(f"Config {key} has cross-role overlap: {overlap}")
    return grouped


def _balanced_accuracy(metrics: dict[str, float]) -> float | None:
    negatives = metrics["true_negative"] + metrics["false_positive"]
    if negatives == 0:
        return None
    specificity = metrics["true_negative"] / negatives
    return (metrics["recall"] + specificity) / 2.0


def _fpr_at_95_tpr(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    best: float | None = None
    for threshold in sorted(set(scores), reverse=True):
        predictions = [int(score >= threshold) for score in scores]
        metrics = binary_metrics(labels, predictions)
        if metrics["recall"] >= 0.95:
            fpr = metrics["false_positive"] / negatives
            best = fpr if best is None else min(best, fpr)
    return best


def evaluate_followup_configuration(
    episode_rows: list[dict[str, str]],
    *,
    bootstrap_seed: int = 42,
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    calibration_rows = [
        row for row in episode_rows if row["evaluation_role"] == "calibration_normal"
    ]
    evaluation_rows = [row for row in episode_rows if row["evaluation_role"] == "evaluation"]
    if not calibration_rows or not evaluation_rows:
        raise ValueError("Follow-up evaluation requires both calibration and evaluation rows.")

    calibration_scores = [float(row["score"]) for row in calibration_rows]
    threshold = _percentile(calibration_scores, 0.95)
    labels = [1 if row["label"].lower() == "buggy" else 0 for row in evaluation_rows]
    scores = [float(row["score"]) for row in evaluation_rows]
    predictions = [int(score >= threshold) for score in scores]
    confusion = binary_metrics(labels, predictions)
    metrics = {
        **confusion,
        "balanced_accuracy": _balanced_accuracy(confusion),
        "auroc": auroc(labels, scores),
        "auprc": average_precision(labels, scores),
        "fpr_at_95_tpr": _fpr_at_95_tpr(labels, scores),
        "evaluation_episode_count": len(evaluation_rows),
        "positive_episode_count": sum(labels),
        "negative_episode_count": len(evaluation_rows) - sum(labels),
        "calibration_episode_count": len({row["source_episode_id"] for row in calibration_rows}),
    }
    bootstrap_rows = [
        {
            "pair_id": row["pair_id"],
            "source_episode_id": row["source_episode_id"],
            "label": 1 if row["label"].lower() == "buggy" else 0,
            "score": float(row["score"]),
        }
        for row in evaluation_rows
    ]
    ci_group_key = (
        "pair_id" if all(row["pair_id"] for row in bootstrap_rows) else "source_episode_id"
    )
    confidence_intervals = {
        "auroc": bootstrap_metric_ci(
            bootstrap_rows,
            "auroc",
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
            group_key=ci_group_key,
        ),
        "f1": bootstrap_metric_ci(
            bootstrap_rows,
            "f1",
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
            group_key=ci_group_key,
            threshold=threshold,
        ),
    }
    return {
        "threshold": threshold,
        "threshold_source": "calibration_normal_p95",
        "calibration_episode_ids": sorted({row["source_episode_id"] for row in calibration_rows}),
        "metrics": metrics,
        "confidence_intervals": confidence_intervals,
        "confidence_interval_group_key": ci_group_key,
    }


def _best_row(rows: list[dict[str, str]], *, family: str | None = None) -> dict[str, str]:
    candidates = rows if family is None else [row for row in rows if row["method_family"] == family]
    if not candidates:
        raise ValueError("No comparison rows available for summary.")
    return max(candidates, key=lambda row: float(row["auroc"]))


def build_followup_report(
    comparison_rows: list[dict[str, str]],
    *,
    manifest_summary: dict[str, Any],
    source_r5_manifest_sha256: str,
    followup_manifest_sha256: str,
    followup_metrics_sha256: str,
    locked_test_materialized: bool,
    locked_test_scored: bool,
) -> str:
    best_overall = _best_row(comparison_rows)
    best_baseline = _best_row(comparison_rows, family="baseline")
    lines = [
        "# TempGlitch Follow-up Pair-Disjoint Evaluation",
        "",
        f"- Protocol: `{FOLLOWUP_PROTOCOL}`",
        f"- Source R5 manifest SHA256: `{source_r5_manifest_sha256}`",
        f"- Follow-up manifest SHA256: `{followup_manifest_sha256}`",
        f"- Follow-up metrics SHA256: `{followup_metrics_sha256}`",
        f"- locked_test_materialized: `{str(locked_test_materialized).lower()}`",
        f"- locked_test_scored: `{str(locked_test_scored).lower()}`",
        "- This is an artifact-only bounded non-locked TempGlitch follow-up.",
        "",
        "## Frozen Support",
        "",
        f"- Calibration normals: `{', '.join(manifest_summary['calibration_episode_ids'])}`",
        f"- Calibration episode count: `{manifest_summary['calibration_episode_count']}`",
        f"- Evaluation normal-negative episodes: `{manifest_summary['evaluation_normal_episode_count']}`",
        f"- Evaluation buggy-positive episodes: `{manifest_summary['evaluation_buggy_episode_count']}`",
        f"- Cross-role overlap: `{manifest_summary['role_overlap']}`",
        "",
        "## Best Rows",
        "",
        f"- Best overall AUROC row: `{best_overall['method_family']}/{best_overall['window_scorer']}` "
        f"seed `{best_overall['seed'] or 'n/a'}` aggregation `{best_overall['episode_aggregation']}` "
        f"with AUROC `{best_overall['auroc']}`, AUPRC `{best_overall['auprc']}`, "
        f"F1 `{best_overall['f1']}`, balanced accuracy `{best_overall['balanced_accuracy']}`",
        f"- Best baseline AUROC row: `{best_baseline['method']}` aggregation "
        f"`{best_baseline['episode_aggregation']}` with AUROC `{best_baseline['auroc']}`",
        "",
        "## Claim Boundary",
        "",
        "- Safe wording: bounded non-locked TempGlitch follow-up within the frozen split.",
        "- Forbidden: broad glitch-detection, SOTA, cross-game generalization, temporal localization, "
        "SIGReg benefit, or locked-test performance.",
    ]
    return "\n".join(lines) + "\n"


def _load_source_bundle(
    *,
    r5_output_dir: Path,
    train_lance: Path,
    validation_normal_lance: Path,
    validation_buggy_lance: Path,
) -> dict[str, Any]:
    for path, description in (
        (r5_output_dir, "R5 output directory"),
        (train_lance, "train-normal Lance"),
        (validation_normal_lance, "validation-normal Lance"),
        (validation_buggy_lance, "validation-buggy Lance"),
    ):
        refuse_locked_test_path(path, description=description)
        if not path.exists():
            raise FileNotFoundError(f"Missing required follow-up input: {path}")

    r5_metrics_path = r5_output_dir / "r5_metrics.json"
    r5_provenance_path = r5_output_dir / "r5_provenance.json"
    r5_manifest_path = r5_output_dir / "r5_manifest.csv"
    r5_episode_path = r5_output_dir / "episode_scores.csv"
    r5_comparison_path = r5_output_dir / "r5_comparison.csv"
    r5_metrics = load_verified_r5_metrics_artifact(r5_metrics_path)
    r5_provenance = _read_json(r5_provenance_path)
    if r5_provenance.get("status") != "r5_complete":
        raise ValueError("R5 provenance artifact is not marked complete.")

    for flag in FOLLOWUP_FLAGS:
        if bool(r5_metrics.get(flag)):
            raise ValueError(f"R5 metrics flag must remain false: {flag}")
        if bool(r5_provenance.get(flag)):
            raise ValueError(f"R5 provenance flag must remain false: {flag}")

    source_file_hashes = {
        str(r5_manifest_path): r5_metrics["manifest_sha256"],
        str(r5_episode_path): r5_metrics["episode_score_sha256"],
        str(r5_comparison_path): r5_metrics["comparison_sha256"],
    }
    source_file_hashes[str(r5_output_dir / "baseline_scores.csv")] = r5_metrics[
        "baseline_score_sha256"
    ]
    for seed_output in r5_metrics["seed_outputs"]:
        source_file_hashes[str(_resolve_repo_relative_path(seed_output["raw_score_path"]))] = (
            seed_output["raw_score_sha256"]
        )

    for path_text, expected_hash in source_file_hashes.items():
        actual_path = Path(path_text)
        if not actual_path.exists():
            raise FileNotFoundError(f"Missing required source artifact: {actual_path}")
        actual_hash = sha256_file(actual_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Source artifact hash mismatch for {actual_path}: expected {expected_hash}, found {actual_hash}."
            )

    expected_train = str(r5_provenance["train_lance_fingerprint"])
    expected_validation_normal = str(r5_provenance["validation_normal_lance_fingerprint"])
    expected_validation_buggy = str(r5_provenance["validation_buggy_lance_fingerprint"])
    actual_train = FingerprintBuilder.inventory_sha256(train_lance)
    actual_validation_normal = FingerprintBuilder.inventory_sha256(validation_normal_lance)
    actual_validation_buggy = FingerprintBuilder.inventory_sha256(validation_buggy_lance)
    if actual_train != expected_train:
        raise ValueError(
            "Train-normal Lance fingerprint no longer matches the validated R5 provenance."
        )
    if actual_validation_normal != expected_validation_normal:
        raise ValueError(
            "Validation-normal Lance fingerprint no longer matches the validated R5 provenance."
        )
    if actual_validation_buggy != expected_validation_buggy:
        raise ValueError(
            "Validation-buggy Lance fingerprint no longer matches the validated R5 provenance."
        )

    comparison_registry = {_config_key(row): row for row in read_csv_rows(r5_comparison_path)}
    if len(comparison_registry) != EXPECTED_CONFIG_COUNT:
        raise ValueError(
            f"Validated R5 comparison registry exposes {len(comparison_registry)} configs; "
            f"expected {EXPECTED_CONFIG_COUNT}."
        )

    return {
        "r5_metrics": r5_metrics,
        "r5_provenance": r5_provenance,
        "r5_manifest_rows": read_csv_rows(r5_manifest_path),
        "r5_episode_rows": read_csv_rows(r5_episode_path),
        "r5_comparison_rows": read_csv_rows(r5_comparison_path),
        "comparison_registry": comparison_registry,
        "source_hashes": source_file_hashes,
        "lance_fingerprints": {
            "train": actual_train,
            "validation_normal": actual_validation_normal,
            "validation_buggy": actual_validation_buggy,
        },
        "source_paths": {
            "r5_metrics": r5_metrics_path,
            "r5_provenance": r5_provenance_path,
            "r5_manifest": r5_manifest_path,
            "r5_episode_scores": r5_episode_path,
            "r5_comparison": r5_comparison_path,
        },
    }


def run_tempglitch_followup_pair_disjoint(
    *,
    r5_output_dir: Path,
    train_lance: Path,
    validation_normal_lance: Path,
    validation_buggy_lance: Path,
    output_dir: Path,
    bootstrap_seed: int = 42,
    n_bootstrap: int = 1000,
    command_text: str,
) -> dict[str, Any]:
    source_bundle = _load_source_bundle(
        r5_output_dir=r5_output_dir,
        train_lance=train_lance,
        validation_normal_lance=validation_normal_lance,
        validation_buggy_lance=validation_buggy_lance,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    followup_manifest_rows = build_followup_manifest_rows(source_bundle["r5_manifest_rows"])
    manifest_summary = validate_followup_manifest_rows(followup_manifest_rows)
    followup_manifest_path = write_csv_rows(
        output_dir / "followup_manifest.csv",
        followup_manifest_rows,
        MANIFEST_FIELDS,
    )
    followup_manifest_sha_path = _write_sha256(
        followup_manifest_path,
        output_dir / "followup_manifest.sha256",
    )

    followup_episode_rows = build_followup_episode_rows(source_bundle["r5_episode_rows"])
    grouped_episode_rows = validate_followup_episode_rows(followup_episode_rows)
    followup_episode_path = write_csv_rows(
        output_dir / "followup_episode_scores.csv",
        followup_episode_rows,
        FOLLOWUP_EPISODE_SCORE_FIELDS,
    )

    followup_comparison_rows: list[dict[str, str]] = []
    for source_row in source_bundle["r5_comparison_rows"]:
        key = _config_key(source_row)
        episode_rows = grouped_episode_rows[key]
        evaluation = evaluate_followup_configuration(
            episode_rows,
            bootstrap_seed=bootstrap_seed,
            n_bootstrap=n_bootstrap,
        )
        metrics = evaluation["metrics"]
        ci = evaluation["confidence_intervals"]
        followup_comparison_rows.append(
            {
                "method_family": source_row["method_family"],
                "method": source_row["method"],
                "window_scorer": source_row["window_scorer"],
                "seed": source_row["seed"],
                "episode_aggregation": source_row["episode_aggregation"],
                "raw_score_path": source_row["raw_score_path"],
                "raw_score_sha256": source_row["raw_score_sha256"],
                "checkpoint_sha256": source_row["checkpoint_sha256"],
                "threshold": _float_text(evaluation["threshold"]),
                "threshold_source": str(evaluation["threshold_source"]),
                "auroc": _float_text(metrics["auroc"]),
                "auprc": _float_text(metrics["auprc"]),
                "f1": _float_text(metrics["f1"]),
                "precision": _float_text(metrics["precision"]),
                "recall": _float_text(metrics["recall"]),
                "balanced_accuracy": _float_text(metrics["balanced_accuracy"]),
                "fpr_at_95_tpr": _float_text(metrics["fpr_at_95_tpr"]),
                "true_positive": _float_text(metrics["true_positive"]),
                "false_positive": _float_text(metrics["false_positive"]),
                "false_negative": _float_text(metrics["false_negative"]),
                "true_negative": _float_text(metrics["true_negative"]),
                "calibration_episode_count": str(metrics["calibration_episode_count"]),
                "evaluation_episode_count": str(metrics["evaluation_episode_count"]),
                "positive_episode_count": str(metrics["positive_episode_count"]),
                "negative_episode_count": str(metrics["negative_episode_count"]),
                "calibration_episode_ids": ",".join(evaluation["calibration_episode_ids"]),
                "confidence_interval_group_key": str(evaluation["confidence_interval_group_key"]),
                "auroc_ci_lower": _float_text(ci["auroc"]["lower"]),
                "auroc_ci_upper": _float_text(ci["auroc"]["upper"]),
                "auroc_ci_valid_bootstrap_count": str(ci["auroc"]["valid_bootstrap_count"]),
                "f1_ci_lower": _float_text(ci["f1"]["lower"]),
                "f1_ci_upper": _float_text(ci["f1"]["upper"]),
                "f1_ci_valid_bootstrap_count": str(ci["f1"]["valid_bootstrap_count"]),
            }
        )

    followup_comparison_path = write_csv_rows(
        output_dir / "followup_comparison.csv",
        followup_comparison_rows,
        FOLLOWUP_COMPARISON_FIELDS,
    )

    command_path = output_dir / "followup_command.txt"
    command_path.write_text(command_text.strip() + "\n", encoding="utf-8")
    command_sha256 = sha256_file(command_path)

    followup_metrics_path = output_dir / "followup_metrics.json"
    metrics_payload = {
        "status": FOLLOWUP_STATUS,
        "protocol": FOLLOWUP_PROTOCOL,
        "source_r5_output_dir": str(r5_output_dir),
        "source_r5_manifest_sha256": source_bundle["r5_metrics"]["manifest_sha256"],
        "source_r5_metrics_sha256": sha256_file(source_bundle["source_paths"]["r5_metrics"]),
        "source_r5_provenance_sha256": sha256_file(source_bundle["source_paths"]["r5_provenance"]),
        "calibration_episode_ids": list(CALIBRATION_NORMAL_EPISODE_IDS),
        "manifest_path": str(followup_manifest_path),
        "manifest_sha256": sha256_file(followup_manifest_path),
        "manifest_summary": manifest_summary,
        "episode_score_path": str(followup_episode_path),
        "episode_score_sha256": sha256_file(followup_episode_path),
        "comparison_path": str(followup_comparison_path),
        "comparison_sha256": sha256_file(followup_comparison_path),
        "results": followup_comparison_rows,
        "source_score_hashes": source_bundle["source_hashes"],
        "command_path": str(command_path),
        "command_sha256": command_sha256,
        "confidence_interval_metrics": ["auroc", "f1"],
        "confidence_interval_group_key": "pair_id",
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    _write_json(followup_metrics_path, metrics_payload)

    followup_report_path = output_dir / "FOLLOWUP_REPORT.md"
    followup_report_path.write_text(
        build_followup_report(
            followup_comparison_rows,
            manifest_summary=manifest_summary,
            source_r5_manifest_sha256=source_bundle["r5_metrics"]["manifest_sha256"],
            followup_manifest_sha256=sha256_file(followup_manifest_path),
            followup_metrics_sha256=sha256_file(followup_metrics_path),
            locked_test_materialized=False,
            locked_test_scored=False,
        ),
        encoding="utf-8",
    )

    followup_provenance_path = output_dir / "followup_provenance.json"
    provenance_payload = {
        "status": FOLLOWUP_STATUS,
        "protocol": FOLLOWUP_PROTOCOL,
        "source_r5_artifacts": {
            "r5_metrics_path": str(source_bundle["source_paths"]["r5_metrics"]),
            "r5_metrics_sha256": sha256_file(source_bundle["source_paths"]["r5_metrics"]),
            "r5_provenance_path": str(source_bundle["source_paths"]["r5_provenance"]),
            "r5_provenance_sha256": sha256_file(source_bundle["source_paths"]["r5_provenance"]),
            "r5_manifest_path": str(source_bundle["source_paths"]["r5_manifest"]),
            "r5_manifest_sha256": source_bundle["r5_metrics"]["manifest_sha256"],
            "r5_episode_scores_path": str(source_bundle["source_paths"]["r5_episode_scores"]),
            "r5_episode_scores_sha256": source_bundle["r5_metrics"]["episode_score_sha256"],
            "r5_comparison_path": str(source_bundle["source_paths"]["r5_comparison"]),
            "r5_comparison_sha256": source_bundle["r5_metrics"]["comparison_sha256"],
            "source_score_hashes": source_bundle["source_hashes"],
        },
        "input_lance_paths": {
            "train_lance": str(train_lance),
            "validation_normal_lance": str(validation_normal_lance),
            "validation_buggy_lance": str(validation_buggy_lance),
        },
        "input_lance_fingerprints": source_bundle["lance_fingerprints"],
        "calibration_episode_ids": list(CALIBRATION_NORMAL_EPISODE_IDS),
        "outputs": {
            "followup_manifest.csv": sha256_file(followup_manifest_path),
            "followup_manifest.sha256": sha256_file(followup_manifest_sha_path),
            "followup_episode_scores.csv": sha256_file(followup_episode_path),
            "followup_comparison.csv": sha256_file(followup_comparison_path),
            "followup_metrics.json": sha256_file(followup_metrics_path),
            "FOLLOWUP_REPORT.md": sha256_file(followup_report_path),
            "followup_command.txt": command_sha256,
        },
        "manifest_summary": manifest_summary,
        "environment": runtime_provenance(include_lewm=False),
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    _write_json(followup_provenance_path, provenance_payload)

    receipt_path = output_dir / "followup_validator_receipt.json"
    receipt = validate_tempglitch_followup_output(output_dir=output_dir, receipt_path=receipt_path)
    return {
        "status": FOLLOWUP_STATUS,
        "output_dir": str(output_dir),
        "manifest_path": str(followup_manifest_path),
        "manifest_sha256": sha256_file(followup_manifest_path),
        "comparison_path": str(followup_comparison_path),
        "comparison_sha256": sha256_file(followup_comparison_path),
        "metrics_path": str(followup_metrics_path),
        "metrics_sha256": sha256_file(followup_metrics_path),
        "provenance_path": str(followup_provenance_path),
        "provenance_sha256": sha256_file(followup_provenance_path),
        "report_path": str(followup_report_path),
        "report_sha256": sha256_file(followup_report_path),
        "receipt_path": str(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
        "validator_status": receipt["status"],
    }


# Frozen pair-disjoint protocol support tuple:
# (calibration_episode_count, evaluation_episode_count, positive_episode_count,
#  negative_episode_count). The expanded-support Phase P1 runs may override this
# with a larger tuple while keeping leakage = 0; the frozen default is preserved
# so historical evidence keeps validating exactly as before.
FROZEN_FOLLOWUP_SUPPORT_TUPLE = ("4", "32", "22", "10")


def validate_tempglitch_followup_output(
    *,
    output_dir: Path,
    receipt_path: Path | None = None,
    expected_support: tuple[str, str, str, str] = FROZEN_FOLLOWUP_SUPPORT_TUPLE,
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    refuse_locked_test_path(output_dir, description="follow-up output directory")
    for name in FOLLOWUP_REQUIRED_FILES:
        if receipt_path is not None and name == receipt_path.name:
            continue
        if not (output_dir / name).exists():
            raise FileNotFoundError(f"Missing required follow-up output: {output_dir / name}")

    manifest_path = output_dir / "followup_manifest.csv"
    manifest_sha_path = output_dir / "followup_manifest.sha256"
    episode_path = output_dir / "followup_episode_scores.csv"
    comparison_path = output_dir / "followup_comparison.csv"
    metrics_path = output_dir / "followup_metrics.json"
    provenance_path = output_dir / "followup_provenance.json"
    command_path = output_dir / "followup_command.txt"

    expected_manifest_sha = manifest_sha_path.read_text(encoding="utf-8-sig").strip()
    actual_manifest_sha = sha256_file(manifest_path)
    if actual_manifest_sha != expected_manifest_sha:
        raise ValueError("Follow-up manifest SHA256 sidecar does not match the manifest bytes.")
    manifest_rows = read_csv_rows(manifest_path)
    manifest_summary = validate_followup_manifest_rows(manifest_rows)

    episode_rows = read_csv_rows(episode_path)
    grouped_episode_rows = validate_followup_episode_rows(episode_rows)
    comparison_rows = read_csv_rows(comparison_path)
    if len(comparison_rows) != len(grouped_episode_rows):
        raise ValueError(
            "Follow-up comparison row count does not match the episode-score config count."
        )

    support_tuples = {
        (
            row["calibration_episode_count"],
            row["evaluation_episode_count"],
            row["positive_episode_count"],
            row["negative_episode_count"],
        )
        for row in comparison_rows
    }
    expected_support_set = {tuple(str(part) for part in expected_support)}
    if support_tuples != expected_support_set:
        raise ValueError(
            f"Follow-up support mismatch: {support_tuples}; expected {expected_support_set}"
        )

    calibration_text = ",".join(CALIBRATION_NORMAL_EPISODE_IDS)
    required_fields = [
        "auroc",
        "auprc",
        "f1",
        "precision",
        "recall",
        "balanced_accuracy",
        "fpr_at_95_tpr",
    ]
    for row in comparison_rows:
        key = _config_key(row)
        if key not in grouped_episode_rows:
            raise ValueError(f"Follow-up comparison row does not map to episode rows: {key}")
        if row["threshold_source"] != "calibration_normal_p95":
            raise ValueError("Follow-up threshold source must remain calibration_normal_p95.")
        if row["calibration_episode_ids"] != calibration_text:
            raise ValueError("Follow-up comparison row uses unexpected calibration episode IDs.")
        if row["confidence_interval_group_key"] != "pair_id":
            raise ValueError("Follow-up confidence intervals must be grouped by pair_id.")
        for field in required_fields:
            if row[field] == "":
                raise ValueError(
                    f"Follow-up comparison row is missing required metric field {field}."
                )
        raw_score_path = _resolve_repo_relative_path(row["raw_score_path"])
        if not raw_score_path.exists():
            raise FileNotFoundError(f"Follow-up raw score source is missing: {raw_score_path}")
        if sha256_file(raw_score_path) != row["raw_score_sha256"]:
            raise ValueError(f"Follow-up raw score hash mismatch for {raw_score_path}.")

    baseline_methods = {
        row["method"] for row in comparison_rows if row["method_family"] == "baseline"
    }
    lewm_seeds = {row["seed"] for row in comparison_rows if row["method_family"] == "lewm"}
    if baseline_methods != {"frame_diff", "feature_distance"}:
        raise ValueError(f"Unexpected baseline coverage: {sorted(baseline_methods)}")
    if lewm_seeds != {"42", "43", "44"}:
        raise ValueError(f"Unexpected LeWM seed coverage: {sorted(lewm_seeds)}")

    metrics_payload = _read_json(metrics_path)
    provenance_payload = _read_json(provenance_path)
    for payload_name, payload in (("metrics", metrics_payload), ("provenance", provenance_payload)):
        if payload.get("status") != FOLLOWUP_STATUS:
            raise ValueError(f"Follow-up {payload_name} status is not {FOLLOWUP_STATUS}.")
        if payload.get("protocol") != FOLLOWUP_PROTOCOL:
            raise ValueError(f"Follow-up {payload_name} protocol is not {FOLLOWUP_PROTOCOL}.")
        for flag in FOLLOWUP_FLAGS:
            if bool(payload.get(flag)):
                raise ValueError(f"Follow-up {payload_name} flag must remain false: {flag}")

    if metrics_payload["manifest_sha256"] != actual_manifest_sha:
        raise ValueError("Follow-up metrics manifest SHA256 does not match the manifest bytes.")
    if metrics_payload["comparison_sha256"] != sha256_file(comparison_path):
        raise ValueError("Follow-up metrics comparison SHA256 does not match the comparison bytes.")
    if provenance_payload["outputs"]["followup_metrics.json"] != sha256_file(metrics_path):
        raise ValueError("Follow-up provenance does not match the metrics JSON hash.")
    if provenance_payload["outputs"]["followup_manifest.csv"] != actual_manifest_sha:
        raise ValueError("Follow-up provenance does not match the manifest hash.")
    if not command_path.read_text(encoding="utf-8-sig").strip():
        raise ValueError("Follow-up command log must not be empty.")

    receipt = {
        "status": FOLLOWUP_VALIDATOR_STATUS,
        "protocol": FOLLOWUP_PROTOCOL,
        "output_dir": str(output_dir),
        "manifest_sha256": actual_manifest_sha,
        "comparison_sha256": sha256_file(comparison_path),
        "metrics_sha256": sha256_file(metrics_path),
        "provenance_sha256": sha256_file(provenance_path),
        "manifest_summary": manifest_summary,
        "comparison_row_count": len(comparison_rows),
        "baseline_methods": sorted(baseline_methods),
        "lewm_seeds": sorted(lewm_seeds),
        "support_tuple": {
            "calibration_episode_count": 4,
            "evaluation_episode_count": 32,
            "positive_episode_count": 22,
            "negative_episode_count": 10,
        },
        "calibration_episode_ids": list(CALIBRATION_NORMAL_EPISODE_IDS),
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "command_sha256": sha256_file(command_path),
        "python_version": sys.version.split()[0],
    }
    if receipt_path is not None:
        _write_json(receipt_path, receipt)
    return receipt
