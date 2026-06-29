from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Sequence

from .evaluate import auroc, average_precision, binary_metrics
from .kaggle_automation import FingerprintBuilder
from .lewm_adapter import sha256_file
from .lewm_lance_eval import (
    MANIFEST_FIELDS,
    build_canonical_manifest,
    read_csv_rows,
    run_gate7_scoring,
    runtime_provenance,
    validate_manifest_rows,
    write_csv_rows,
)
from .statistics import bootstrap_metric_ci

MANIFEST_SEED = 42
CALIBRATION_EPISODE_COUNT = 2
EPISODE_AGGREGATIONS = ("mean", "max", "top2_mean")
LEWM_WINDOW_SCORERS = (
    "lewm_mse_mean",
    "lewm_mse_max",
    "lewm_mse_top2_mean",
    "lewm_l2_mean",
    "lewm_l2_max",
    "lewm_l2_top2_mean",
)
BASELINE_WINDOW_SCORERS = ("frame_diff", "feature_distance")
EPISODE_SCORE_FIELDS = (
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
COMPARISON_FIELDS = (
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
    "fpr_at_95_tpr",
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
    "calibration_episode_ids",
    "auroc_ci_lower",
    "auroc_ci_upper",
    "f1_ci_lower",
    "f1_ci_upper",
)
R5_OUTPUT_FILES = (
    "r5_manifest.csv",
    "r5_manifest.sha256",
    "baseline_scores.csv",
    "episode_scores.csv",
    "r5_metrics.json",
    "r5_comparison.csv",
    "r5_provenance.json",
    "R5_REPORT.md",
)
LOCKED_PATH_TOKEN_RE = re.compile(r"[\\/._-]+")
_SCRIPT_MODULE_CACHE: dict[str, Any] = {}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_script_module(stem: str) -> Any:
    if stem in _SCRIPT_MODULE_CACHE:
        return _SCRIPT_MODULE_CACHE[stem]
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(f"_r5_{stem}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load script module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _SCRIPT_MODULE_CACHE[stem] = module
    return module


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


def _percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _aggregate(values: Sequence[float], aggregation: str) -> float:
    if not values:
        raise ValueError("Episode aggregation requires at least one score.")
    if aggregation == "mean":
        return float(mean(values))
    if aggregation == "max":
        return float(max(values))
    if aggregation == "top2_mean":
        return float(mean(sorted(values, reverse=True)[:2]))
    raise ValueError(
        f"Unsupported episode aggregation: {aggregation}. Expected one of {EPISODE_AGGREGATIONS}."
    )


def _float_text(value: float | None) -> str:
    return "" if value is None else f"{float(value):.12g}"


def _fpr_at_95_tpr(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    best: float | None = None
    for threshold in sorted(set(float(score) for score in scores), reverse=True):
        predictions = [int(float(score) >= threshold) for score in scores]
        metrics = binary_metrics(list(labels), predictions)
        tpr = metrics["recall"]
        if tpr >= 0.95:
            fpr = metrics["false_positive"] / negatives
            best = fpr if best is None else min(best, fpr)
    return best


def refuse_locked_test_path(path: Path, *, description: str) -> None:
    tokens = [token for token in LOCKED_PATH_TOKEN_RE.split(path.as_posix().lower()) if token]
    for token in tokens:
        if token in {"locked", "lock", "lockedtest"}:
            raise ValueError(f"R5 refuses locked-test-looking {description}: {path}")
    for left, right in zip(tokens, tokens[1:]):
        if left in {"locked", "lock"} and right == "test":
            raise ValueError(f"R5 refuses locked-test-looking {description}: {path}")


def parse_seed_artifact_roots(values: Sequence[str]) -> list[Path]:
    roots: list[Path] = []
    for value in values:
        for piece in value.split(","):
            stripped = piece.strip()
            if stripped:
                roots.append(Path(stripped))
    if not roots:
        raise ValueError("At least one --seed-artifact-root path is required.")
    return roots


def resolve_seed_artifact(root: Path) -> dict[str, Any]:
    refuse_locked_test_path(root, description="seed artifact root")
    metadata = _read_json(root / "training_metadata.json")
    config = metadata["config"]
    seed = int(config["seed"])
    target_updates = int(metadata["target_optimizer_updates"])
    _load_script_module("validate_lewm_r3_seed_artifacts").validate_artifacts(
        root,
        expected_seed=seed,
        expected_target_updates=target_updates,
    )
    weights_path = root / "best_weights.pt"
    expected_sha256 = str(metadata["best_weights_sha256"])
    config_path = root / "config.json"
    if not weights_path.is_file():
        raise FileNotFoundError(f"Missing best checkpoint weights for seed {seed}: {weights_path}")
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing config for seed {seed}: {config_path}")
    actual_sha256 = sha256_file(weights_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Best checkpoint hash mismatch for seed {seed}: "
            f"expected {expected_sha256}, found {actual_sha256}."
        )
    return {
        "seed": seed,
        "artifact_root": str(root),
        "weights_path": str(weights_path),
        "config_path": str(config_path),
        "checkpoint_sha256": actual_sha256,
        "checkpoint_resume_sha256": str(metadata["checkpoint_sha256"]),
        "config_hash": str(metadata["config_hash"]),
        "dataset_hashes": dict(metadata["dataset_hashes"]),
        "best_update": int(metadata["best_update"]),
        "best_validation_loss": float(metadata["best_validation_loss"]),
        "updates_completed": int(metadata["updates_completed"]),
        "target_optimizer_updates": target_updates,
        "stopped_early": bool(metadata["stopped_early"]),
        "validation_buggy_used_for_fit_select": bool(
            metadata["validation_buggy_used_for_fit_select"]
        ),
        "locked_test_materialized": bool(metadata["locked_test_materialized"]),
        "locked_test_scored": bool(metadata["locked_test_scored"]),
    }


def planned_output_paths(output_dir: Path, seeds: Sequence[int]) -> list[str]:
    lewm_files = [f"lewm_scores_seed{seed}.csv" for seed in sorted(seeds)]
    return [
        str(output_dir / name) for name in (*R5_OUTPUT_FILES[:2], *lewm_files, *R5_OUTPUT_FILES[2:])
    ]


def _lewm_window_scores(row: dict[str, str]) -> dict[str, float]:
    mse = [float(row[field]) for field in ("mse_t1", "mse_t2", "mse_t3")]
    l2 = [float(row[field]) for field in ("l2_t1", "l2_t2", "l2_t3")]
    return {
        "lewm_mse_mean": float(mean(mse)),
        "lewm_mse_max": float(max(mse)),
        "lewm_mse_top2_mean": float(mean(sorted(mse, reverse=True)[:2])),
        "lewm_l2_mean": float(mean(l2)),
        "lewm_l2_max": float(max(l2)),
        "lewm_l2_top2_mean": float(mean(sorted(l2, reverse=True)[:2])),
    }


def aggregate_episode_scores(
    manifest_rows: Sequence[dict[str, str]],
    score_rows: Sequence[dict[str, str]],
    *,
    window_scorer: str,
    episode_aggregation: str,
    method_family: str,
    method: str,
    seed: int | None,
) -> list[dict[str, str]]:
    if [row["window_id"] for row in manifest_rows] != [row["window_id"] for row in score_rows]:
        raise ValueError("All methods must align to the exact ordered R5 manifest.")
    grouped: dict[str, list[tuple[dict[str, str], float]]] = defaultdict(list)
    for manifest_row, score_row in zip(manifest_rows, score_rows):
        grouped[manifest_row["source_episode_id"]].append((manifest_row, float(score_row["score"])))
    rows: list[dict[str, str]] = []
    for episode_id, items in sorted(grouped.items()):
        first = items[0][0]
        sources = {row["source"] for row, _score in items}
        pair_ids = {row["pair_id"] for row, _score in items}
        categories = {row["category"] for row, _score in items}
        labels = {row["label"] for row, _score in items}
        datasets = {row["dataset_name"] for row, _score in items}
        roles = {row["evaluation_role"] for row, _score in items}
        if not all(
            len(values) == 1 for values in (sources, pair_ids, categories, labels, datasets, roles)
        ):
            raise ValueError(f"Episode metadata drift detected for {episode_id}.")
        rows.append(
            {
                "method_family": method_family,
                "method": method,
                "window_scorer": window_scorer,
                "seed": "" if seed is None else str(seed),
                "episode_aggregation": episode_aggregation,
                "source_episode_id": episode_id,
                "source": first["source"],
                "pair_id": first["pair_id"],
                "category": first["category"],
                "label": first["label"],
                "dataset_name": first["dataset_name"],
                "evaluation_role": first["evaluation_role"],
                "window_count": str(len(items)),
                "score": f"{_aggregate([score for _row, score in items], episode_aggregation):.12g}",
            }
        )
    return rows


def _episode_metric_summary(rows: Sequence[dict[str, str]], threshold: float) -> dict[str, Any]:
    labels = [1 if row["label"].lower() == "buggy" else 0 for row in rows]
    scores = [float(row["score"]) for row in rows]
    predictions = [int(score >= threshold) for score in scores]
    positives = sum(labels)
    return {
        **binary_metrics(labels, predictions),
        "auroc": auroc(labels, scores),
        "auprc": average_precision(labels, scores),
        "pr_auc": average_precision(labels, scores),
        "fpr_at_95_tpr": _fpr_at_95_tpr(labels, scores),
        "evaluation_episode_count": len(rows),
        "positive_episode_count": positives,
        "negative_episode_count": len(rows) - positives,
    }


def evaluate_episode_configuration(
    episode_rows: Sequence[dict[str, str]],
    *,
    bootstrap_seed: int = 42,
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    calibration_rows = [
        row for row in episode_rows if row["evaluation_role"] == "calibration_normal"
    ]
    evaluation_rows = [row for row in episode_rows if row["evaluation_role"] == "evaluation"]
    if not calibration_rows:
        raise ValueError("R5 episode evaluation requires calibration-normal episodes.")
    if not evaluation_rows:
        raise ValueError("R5 episode evaluation requires evaluation episodes.")
    calibration_scores = [float(row["score"]) for row in calibration_rows]
    threshold = _percentile(calibration_scores, 0.95)
    metrics = _episode_metric_summary(evaluation_rows, threshold)
    bootstrap_rows = [
        {
            "source_episode_id": row["source_episode_id"],
            "label": 1 if row["label"].lower() == "buggy" else 0,
            "score": float(row["score"]),
        }
        for row in evaluation_rows
    ]
    ci = {
        "auroc": bootstrap_metric_ci(
            bootstrap_rows,
            "auroc",
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
            group_key="source_episode_id",
        ),
        "f1": bootstrap_metric_ci(
            bootstrap_rows,
            "f1",
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
            group_key="source_episode_id",
            threshold=threshold,
        ),
    }
    return {
        "threshold": threshold,
        "threshold_source": "calibration_normal_p95",
        "calibration_episode_ids": sorted(row["source_episode_id"] for row in calibration_rows),
        "metrics": metrics,
        "confidence_intervals": ci,
    }


def build_r5_report(
    comparison_rows: Sequence[dict[str, str]],
    *,
    manifest_sha256: str,
    metrics_sha256: str,
    locked_test_materialized: bool,
    locked_test_scored: bool,
) -> str:
    lines = [
        "# R5 TempGlitch Identical-Episode Evaluation",
        "",
        f"- Manifest SHA256: `{manifest_sha256}`",
        f"- Metrics SHA256: `{metrics_sha256}`",
        f"- locked_test_materialized: `{str(locked_test_materialized).lower()}`",
        f"- locked_test_scored: `{str(locked_test_scored).lower()}`",
        "- Evaluation unit: episode/video. Window and transition scores are diagnostic only.",
        "- Threshold policy: 95th percentile of calibration-normal episode scores.",
        "",
        "| Method | Seed | Window scorer | Episode aggregation | AUROC | AUPRC | F1 | FPR@95TPR |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in comparison_rows:
        lines.append(
            f"| {row['method']} | {row['seed'] or 'n/a'} | {row['window_scorer']} | "
            f"{row['episode_aggregation']} | {row['auroc'] or 'n/a'} | {row['auprc'] or 'n/a'} | "
            f"{row['f1'] or 'n/a'} | {row['fpr_at_95_tpr'] or 'n/a'} |"
        )
    lines.extend(
        [
            "",
            "Claim boundary: these are non-locked TempGlitch identical-episode results only.",
            "Do not generalize to locked test, WOB, or broad glitch-detection capability.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_verified_r5_metrics_artifact(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing R5 metrics artifact required for claim updates: {path}")
    payload = _read_json(path)
    if payload.get("status") != "r5_complete":
        raise ValueError("R5 metrics artifact is not marked complete.")
    if "manifest_sha256" not in payload or "results" not in payload:
        raise ValueError("R5 metrics artifact is missing required provenance fields.")
    return payload


def run_r5_tempglitch_identical_episode_evaluation(
    *,
    train_lance: Path,
    validation_normal_lance: Path,
    validation_buggy_lance: Path,
    seed_artifact_roots: Sequence[Path],
    output_dir: Path,
    device: str = "cpu",
    batch_size: int = 16,
    include_conv3d: bool = False,
    include_frozen_video_rep: bool = False,
    dry_run: bool = False,
    bootstrap_seed: int = 42,
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    if include_conv3d:
        raise NotImplementedError("Conv3D is not yet protocol-compatible for the first R5 run.")
    if include_frozen_video_rep:
        raise NotImplementedError(
            "Frozen video-representation baseline is still planning-only for R5."
        )
    for path, description in (
        (train_lance, "train-normal Lance"),
        (validation_normal_lance, "validation-normal Lance"),
        (validation_buggy_lance, "validation-buggy Lance"),
    ):
        refuse_locked_test_path(path, description=description)
        if not path.exists():
            raise FileNotFoundError(f"Missing required R5 input: {path}")

    seed_infos = [resolve_seed_artifact(path) for path in seed_artifact_roots]
    seed_infos.sort(key=lambda item: int(item["seed"]))

    plan = {
        "status": "dry-run" if dry_run else "planned",
        "train_lance": str(train_lance),
        "validation_normal_lance": str(validation_normal_lance),
        "validation_buggy_lance": str(validation_buggy_lance),
        "seed_artifacts": seed_infos,
        "output_dir": str(output_dir),
        "device": device,
        "batch_size": batch_size,
        "manifest_seed": MANIFEST_SEED,
        "calibration_episode_count": CALIBRATION_EPISODE_COUNT,
        "episode_aggregations": list(EPISODE_AGGREGATIONS),
        "baseline_window_scorers": list(BASELINE_WINDOW_SCORERS),
        "lewm_window_scorers": list(LEWM_WINDOW_SCORERS),
        "planned_outputs": planned_output_paths(
            output_dir, [int(item["seed"]) for item in seed_infos]
        ),
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    if dry_run:
        return plan

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows, manifest_fingerprints = build_canonical_manifest(
        validation_normal_lance,
        validation_buggy_lance,
        seed=MANIFEST_SEED,
        calibration_episode_count=CALIBRATION_EPISODE_COUNT,
    )
    validate_manifest_rows(
        manifest_rows,
        expected_calibration_episode_count=CALIBRATION_EPISODE_COUNT,
    )
    manifest_path = write_csv_rows(output_dir / "r5_manifest.csv", manifest_rows, MANIFEST_FIELDS)
    manifest_hash_path = _write_sha256(manifest_path, output_dir / "r5_manifest.sha256")

    gate8_module = _load_script_module("run_gate8_baselines_from_lance")
    baseline_metadata = gate8_module.run_gate8_baselines(
        manifest_path=manifest_path,
        train_lance=train_lance,
        normal_lance=validation_normal_lance,
        buggy_lance=validation_buggy_lance,
        output_dir=output_dir,
        batch_size=batch_size,
        expected_calibration_episode_count=CALIBRATION_EPISODE_COUNT,
    )
    baseline_score_path = output_dir / "baseline_scores.csv"
    baseline_rows = read_csv_rows(baseline_score_path)
    gate8_module.validate_baseline_alignment(manifest_rows, baseline_rows)

    per_method_rows: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    lewm_outputs: list[dict[str, Any]] = []

    for info in seed_infos:
        seed = int(info["seed"])
        seed_output_dir = output_dir / f"_lewm_seed{seed}"
        metadata = run_gate7_scoring(
            checkpoint=Path(info["weights_path"]),
            config=Path(info["config_path"]),
            normal_lance=validation_normal_lance,
            buggy_lance=validation_buggy_lance,
            output_dir=seed_output_dir,
            expected_sha256=str(info["checkpoint_sha256"]),
            device=device,
            batch_size=batch_size,
            seed=MANIFEST_SEED,
        )
        seed_manifest_path = seed_output_dir / "window_manifest.csv"
        if sha256_file(seed_manifest_path) != sha256_file(manifest_path):
            raise ValueError(f"Seed {seed} produced a non-identical manifest.")
        root_score_path = output_dir / f"lewm_scores_seed{seed}.csv"
        shutil.copyfile(seed_output_dir / "lewm_transition_scores.csv", root_score_path)
        lewm_rows = read_csv_rows(root_score_path)
        if [row["window_id"] for row in manifest_rows] != [row["window_id"] for row in lewm_rows]:
            raise ValueError(f"LeWM scores for seed {seed} do not align to the R5 manifest.")
        lewm_outputs.append(
            {
                **info,
                "raw_score_path": str(root_score_path),
                "raw_score_sha256": sha256_file(root_score_path),
                "gate7_metadata": metadata,
            }
        )
        scorer_rows: dict[str, list[dict[str, str]]] = {
            scorer: [] for scorer in LEWM_WINDOW_SCORERS
        }
        for row in lewm_rows:
            for scorer, value in _lewm_window_scores(row).items():
                scorer_rows[scorer].append(
                    {"window_id": row["window_id"], "score": f"{value:.12g}"}
                )
        for window_scorer, aligned_rows in scorer_rows.items():
            for aggregation in EPISODE_AGGREGATIONS:
                episode_rows = aggregate_episode_scores(
                    manifest_rows,
                    aligned_rows,
                    window_scorer=window_scorer,
                    episode_aggregation=aggregation,
                    method_family="lewm",
                    method="lewm",
                    seed=seed,
                )
                evaluation = evaluate_episode_configuration(
                    episode_rows,
                    bootstrap_seed=bootstrap_seed,
                    n_bootstrap=n_bootstrap,
                )
                per_method_rows.extend(episode_rows)
                comparison_rows.append(
                    {
                        "method_family": "lewm",
                        "method": "lewm",
                        "window_scorer": window_scorer,
                        "seed": str(seed),
                        "episode_aggregation": aggregation,
                        "raw_score_path": str(root_score_path),
                        "raw_score_sha256": sha256_file(root_score_path),
                        "checkpoint_sha256": str(info["checkpoint_sha256"]),
                        "threshold": _float_text(evaluation["threshold"]),
                        "threshold_source": str(evaluation["threshold_source"]),
                        "auroc": _float_text(evaluation["metrics"]["auroc"]),
                        "auprc": _float_text(evaluation["metrics"]["auprc"]),
                        "f1": _float_text(evaluation["metrics"]["f1"]),
                        "fpr_at_95_tpr": _float_text(evaluation["metrics"]["fpr_at_95_tpr"]),
                        "evaluation_episode_count": str(
                            evaluation["metrics"]["evaluation_episode_count"]
                        ),
                        "positive_episode_count": str(
                            evaluation["metrics"]["positive_episode_count"]
                        ),
                        "negative_episode_count": str(
                            evaluation["metrics"]["negative_episode_count"]
                        ),
                        "calibration_episode_ids": ",".join(evaluation["calibration_episode_ids"]),
                        "auroc_ci_lower": _float_text(
                            evaluation["confidence_intervals"]["auroc"]["lower"]
                        ),
                        "auroc_ci_upper": _float_text(
                            evaluation["confidence_intervals"]["auroc"]["upper"]
                        ),
                        "f1_ci_lower": _float_text(
                            evaluation["confidence_intervals"]["f1"]["lower"]
                        ),
                        "f1_ci_upper": _float_text(
                            evaluation["confidence_intervals"]["f1"]["upper"]
                        ),
                    }
                )

    for baseline_name in BASELINE_WINDOW_SCORERS:
        aligned_rows = [
            {"window_id": row["window_id"], "score": row[baseline_name]} for row in baseline_rows
        ]
        for aggregation in EPISODE_AGGREGATIONS:
            episode_rows = aggregate_episode_scores(
                manifest_rows,
                aligned_rows,
                window_scorer=baseline_name,
                episode_aggregation=aggregation,
                method_family="baseline",
                method=baseline_name,
                seed=None,
            )
            evaluation = evaluate_episode_configuration(
                episode_rows,
                bootstrap_seed=bootstrap_seed,
                n_bootstrap=n_bootstrap,
            )
            per_method_rows.extend(episode_rows)
            comparison_rows.append(
                {
                    "method_family": "baseline",
                    "method": baseline_name,
                    "window_scorer": baseline_name,
                    "seed": "",
                    "episode_aggregation": aggregation,
                    "raw_score_path": str(baseline_score_path),
                    "raw_score_sha256": sha256_file(baseline_score_path),
                    "checkpoint_sha256": "",
                    "threshold": _float_text(evaluation["threshold"]),
                    "threshold_source": str(evaluation["threshold_source"]),
                    "auroc": _float_text(evaluation["metrics"]["auroc"]),
                    "auprc": _float_text(evaluation["metrics"]["auprc"]),
                    "f1": _float_text(evaluation["metrics"]["f1"]),
                    "fpr_at_95_tpr": _float_text(evaluation["metrics"]["fpr_at_95_tpr"]),
                    "evaluation_episode_count": str(
                        evaluation["metrics"]["evaluation_episode_count"]
                    ),
                    "positive_episode_count": str(evaluation["metrics"]["positive_episode_count"]),
                    "negative_episode_count": str(evaluation["metrics"]["negative_episode_count"]),
                    "calibration_episode_ids": ",".join(evaluation["calibration_episode_ids"]),
                    "auroc_ci_lower": _float_text(
                        evaluation["confidence_intervals"]["auroc"]["lower"]
                    ),
                    "auroc_ci_upper": _float_text(
                        evaluation["confidence_intervals"]["auroc"]["upper"]
                    ),
                    "f1_ci_lower": _float_text(evaluation["confidence_intervals"]["f1"]["lower"]),
                    "f1_ci_upper": _float_text(evaluation["confidence_intervals"]["f1"]["upper"]),
                }
            )

    episode_scores_path = write_csv_rows(
        output_dir / "episode_scores.csv",
        per_method_rows,
        EPISODE_SCORE_FIELDS,
    )
    comparison_path = write_csv_rows(
        output_dir / "r5_comparison.csv",
        comparison_rows,
        COMPARISON_FIELDS,
    )
    metrics_payload = {
        "status": "r5_complete",
        "protocol": "tempglitch_identical_episode_nonlocked",
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "manifest_fingerprints": manifest_fingerprints,
        "episode_score_path": str(episode_scores_path),
        "episode_score_sha256": sha256_file(episode_scores_path),
        "comparison_path": str(comparison_path),
        "comparison_sha256": sha256_file(comparison_path),
        "baseline_score_path": str(baseline_score_path),
        "baseline_score_sha256": sha256_file(baseline_score_path),
        "seed_outputs": lewm_outputs,
        "results": comparison_rows,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    metrics_path = _write_json(output_dir / "r5_metrics.json", metrics_payload)
    metrics_sha256 = sha256_file(metrics_path)
    report_text = build_r5_report(
        comparison_rows,
        manifest_sha256=sha256_file(manifest_path),
        metrics_sha256=metrics_sha256,
        locked_test_materialized=False,
        locked_test_scored=False,
    )
    report_path = output_dir / "R5_REPORT.md"
    report_path.write_text(report_text, encoding="utf-8")
    provenance_payload = {
        "status": "r5_complete",
        "manifest_seed": MANIFEST_SEED,
        "calibration_episode_count": CALIBRATION_EPISODE_COUNT,
        "episode_aggregations": list(EPISODE_AGGREGATIONS),
        "device": device,
        "batch_size": batch_size,
        "train_lance": str(train_lance),
        "validation_normal_lance": str(validation_normal_lance),
        "validation_buggy_lance": str(validation_buggy_lance),
        "train_lance_fingerprint": FingerprintBuilder.inventory_sha256(train_lance),
        "validation_normal_lance_fingerprint": FingerprintBuilder.inventory_sha256(
            validation_normal_lance
        ),
        "validation_buggy_lance_fingerprint": FingerprintBuilder.inventory_sha256(
            validation_buggy_lance
        ),
        "seed_artifacts": seed_infos,
        "outputs": {
            "r5_manifest.csv": sha256_file(manifest_path),
            "r5_manifest.sha256": sha256_file(manifest_hash_path),
            "baseline_scores.csv": sha256_file(baseline_score_path),
            "episode_scores.csv": sha256_file(episode_scores_path),
            "r5_metrics.json": metrics_sha256,
            "r5_comparison.csv": sha256_file(comparison_path),
            "R5_REPORT.md": sha256_file(report_path),
        },
        "baseline_metadata": baseline_metadata,
        "environment": runtime_provenance(include_lewm=True),
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    provenance_path = _write_json(output_dir / "r5_provenance.json", provenance_payload)
    return {
        "status": "r5_complete",
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "metrics_path": str(metrics_path),
        "metrics_sha256": metrics_sha256,
        "comparison_path": str(comparison_path),
        "comparison_sha256": sha256_file(comparison_path),
        "provenance_path": str(provenance_path),
        "provenance_sha256": sha256_file(provenance_path),
        "report_path": str(report_path),
        "report_sha256": sha256_file(report_path),
        "episode_score_path": str(episode_scores_path),
        "episode_score_sha256": sha256_file(episode_scores_path),
        "baseline_score_path": str(baseline_score_path),
        "baseline_score_sha256": sha256_file(baseline_score_path),
        "seed_outputs": lewm_outputs,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the non-locked TempGlitch R5 identical-episode evaluation bundle."
    )
    parser.add_argument("--train-lance", required=True, type=Path)
    parser.add_argument("--validation-normal-lance", required=True, type=Path)
    parser.add_argument("--validation-buggy-lance", required=True, type=Path)
    parser.add_argument(
        "--seed-artifact-root",
        action="append",
        default=[],
        help="Repeat the flag or pass a comma-separated list of artifact roots.",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--include-conv3d", action="store_true")
    parser.add_argument("--include-frozen-video-rep", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    return parser
