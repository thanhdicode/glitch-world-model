from __future__ import annotations

import argparse
import csv
import gc
import json
import tarfile
from pathlib import Path
from typing import Any, Callable

from .kaggle_automation import FingerprintBuilder
from .lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec, sha256_file
from .lewm_data import episode_from_wob_tar, write_lance_dataset
from .lewm_lance_eval import (
    BUGGY_DATASET_NAME,
    MANIFEST_FIELDS,
    NORMAL_DATASET_NAME,
    _score_dataset,
    canonical_rows_from_samples,
    iter_metadata_samples,
    open_metadata_dataset,
    read_csv_rows,
    runtime_provenance,
    validate_manifest_rows,
    validate_score_alignment,
    write_csv_rows,
)
from .r5_tempglitch_eval import (
    BASELINE_WINDOW_SCORERS,
    COMPARISON_FIELDS,
    EPISODE_AGGREGATIONS,
    EPISODE_SCORE_FIELDS,
    LEWM_WINDOW_SCORERS,
    _float_text,
    _lewm_window_scores,
    aggregate_episode_scores,
    evaluate_episode_configuration,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_READINESS_JSON = ROOT / "configs" / "wob_protocol" / "wob_expansion_readiness.json"
DEFAULT_EVAL_MANIFEST = ROOT / "configs" / "wob_protocol" / "wob_expansion_eval_manifest.csv"
DEFAULT_SPLIT_CSV = ROOT / "configs" / "wob_protocol" / "split.csv"
SUPPORTED_SEEDS = (42, 43, 44)
R5_WOB_OUTPUT_FILES = (
    "r5_wob_manifest.csv",
    "episode_scores.csv",
    "baseline_scores.csv",
    "r5_wob_metrics.json",
    "r5_wob_comparison.csv",
    "r5_wob_provenance.json",
    "R5_WOB_REPORT.md",
)
R5_WOB_WINDOW_MANIFEST = "_window_manifest.csv"


def _load_script_module(stem: str) -> Any:
    import importlib.util

    module_path = ROOT / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(f"_r5_wob_{stem}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load script module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_report(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _parse_keyed_paths(values: list[str]) -> dict[int, Path]:
    parsed: dict[int, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected SEED=PATH, got: {value}")
        seed_text, path_text = value.split("=", 1)
        seed = int(seed_text)
        if seed not in SUPPORTED_SEEDS:
            raise ValueError(f"Unsupported seed {seed}; expected one of {SUPPORTED_SEEDS}.")
        parsed[seed] = Path(path_text)
    return parsed


def _render_eval_manifest(eval_rows: list[dict[str, str]]) -> str:
    if not eval_rows:
        raise ValueError("Frozen WOB evaluation manifest is empty.")
    fieldnames = list(eval_rows[0].keys())
    lines = [",".join(fieldnames)]
    for row in eval_rows:
        lines.append(",".join(row[name] for name in fieldnames))
    return "\n".join(lines) + "\n"


def _validate_readiness_and_manifest(
    readiness_json: Path,
    eval_manifest: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    readiness_module = _load_script_module("validate_wob_expansion_readiness")
    readiness_module.validate_readiness(readiness_json, repo_root=ROOT)
    readiness = _read_json(readiness_json)
    rows = _read_csv_rows(eval_manifest)
    manifest_hash = sha256_file(eval_manifest)
    if manifest_hash != readiness["eval_manifest_sha256"]:
        raise ValueError("WOB eval manifest hash no longer matches the readiness freeze.")
    if len(rows) != readiness["eval_manifest_row_count"]:
        raise ValueError("WOB eval manifest row count no longer matches readiness metadata.")
    return readiness, rows


def _load_train_rows(split_csv: Path) -> list[dict[str, str]]:
    rows = _read_csv_rows(split_csv)
    train_rows = [
        row
        for row in rows
        if row["split"] == "train"
        and row["label"] == "Normal"
        and row["materialize"].lower() == "true"
    ]
    if len(train_rows) != 48:
        raise ValueError(f"Expected 48 WOB train-normal rows, found {len(train_rows)}.")
    return train_rows


def _resolve_source_path(row: dict[str, str], *, normal_root: Path, test_root: Path) -> Path:
    root = normal_root if row["label"] == "Normal" else test_root
    return root / Path(row["source"])


def summarize_source_coverage(
    rows: list[dict[str, str]],
    *,
    normal_root: Path,
    test_root: Path,
) -> dict[str, Any]:
    missing: list[str] = []
    for row in rows:
        path = _resolve_source_path(row, normal_root=normal_root, test_root=test_root)
        if not path.is_file():
            missing.append(str(path))
    return {
        "required_count": len(rows),
        "resolved_count": len(rows) - len(missing),
        "missing_count": len(missing),
        "missing_examples": missing[:5],
    }


def _build_lance_from_rows(
    rows: list[dict[str, str]],
    *,
    normal_root: Path,
    test_root: Path,
    output_path: Path,
    max_steps: int | None = None,
    write_batch_size: int = 1,
    progress: Callable[[str], None] | None = None,
    progress_label: str | None = None,
    progress_every: int = 10,
) -> Path:
    dataset_ids = {
        "Normal": "benedictwilkinsai/world-of-bugs-normal",
        "Buggy": "benedictwilkinsai/world-of-bugs-test",
    }
    if progress_every < 1:
        raise ValueError("progress_every must be positive.")

    row_count = len(rows)
    label = progress_label or output_path.name

    def iter_episodes():
        for row in rows:
            tar_path = _resolve_source_path(row, normal_root=normal_root, test_root=test_root)
            if not tar_path.is_file():
                raise FileNotFoundError(f"Missing WOB tar required for evaluation: {tar_path}")
            yield episode_from_wob_tar(
                tar_path,
                dataset_id=dataset_ids[row["label"]],
                source=row["source"],
                episode_id=row["episode_id"],
                category=row["category"],
                label=row["label"],
                split=row["split"],
                pair_id=row["pair_id"],
                action_dim=4,
                max_steps=max_steps,
            )

    def on_progress(written_count: int) -> None:
        if progress is None:
            return
        if written_count == row_count or written_count % progress_every == 0:
            progress(f"{label}: wrote {written_count}/{row_count} episodes to {output_path}")

    return write_lance_dataset(
        iter_episodes(),
        output_path,
        batch_size=write_batch_size,
        progress=on_progress if progress is not None else None,
    )


def _build_window_manifest(
    *,
    normal_lance: Path,
    buggy_lance: Path,
    eval_rows: list[dict[str, str]],
    output_path: Path,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    role_by_episode = {row["episode_id"]: row["evaluation_role"] for row in eval_rows}
    calibration_episodes = {
        row["episode_id"] for row in eval_rows if row["evaluation_role"] == "calibration_normal"
    }
    normal_dataset, _normal_metadata_only = open_metadata_dataset(normal_lance)
    try:
        normal_samples = list(iter_metadata_samples(normal_dataset))
    finally:
        del normal_dataset
        gc.collect()
    buggy_dataset, _buggy_metadata_only = open_metadata_dataset(buggy_lance)
    try:
        buggy_samples = list(iter_metadata_samples(buggy_dataset))
    finally:
        del buggy_dataset
        gc.collect()
    for sample in [*normal_samples, *buggy_samples]:
        episode_id = sample["source_episode_id"]
        if episode_id not in role_by_episode:
            raise ValueError(
                f"Window manifest episode not present in frozen eval manifest: {episode_id}"
            )
    fingerprints = {
        NORMAL_DATASET_NAME: FingerprintBuilder.inventory_sha256(normal_lance),
        BUGGY_DATASET_NAME: FingerprintBuilder.inventory_sha256(buggy_lance),
    }
    manifest_rows = [
        *canonical_rows_from_samples(
            dataset_name=NORMAL_DATASET_NAME,
            dataset_fingerprint=fingerprints[NORMAL_DATASET_NAME],
            samples=normal_samples,
            calibration_episodes=calibration_episodes,
        ),
        *canonical_rows_from_samples(
            dataset_name=BUGGY_DATASET_NAME,
            dataset_fingerprint=fingerprints[BUGGY_DATASET_NAME],
            samples=buggy_samples,
            calibration_episodes=calibration_episodes,
        ),
    ]
    validate_manifest_rows(manifest_rows, expected_calibration_episode_count=12)
    write_csv_rows(output_path, manifest_rows, MANIFEST_FIELDS)
    return manifest_rows, fingerprints


def _resolve_seed_artifacts(
    *,
    seed_tarballs: dict[int, Path],
    seed_sidecars: dict[int, Path],
    extract_root: Path,
    progress: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    validator_module = _load_script_module("validate_wob_seed_artifacts")
    artifacts: list[dict[str, Any]] = []
    for seed in SUPPORTED_SEEDS:
        if progress is not None:
            progress(f"preflight: validating seed{seed} artifact bundle")
        tarball = seed_tarballs.get(seed)
        sidecar = seed_sidecars.get(seed)
        if tarball is None or sidecar is None:
            raise ValueError(f"Missing seed artifact tarball/sidecar for seed {seed}.")
        validator_module.validate_artifact_tarball(
            tarball,
            sidecar,
            expected_seed=seed,
            expected_target_updates=15000,
        )
        seed_extract_root = extract_root / f"seed{seed}"
        seed_extract_root.mkdir(parents=True, exist_ok=True)
        if progress is not None:
            progress(f"preflight: extracting seed{seed} artifact bundle")
        with tarfile.open(tarball, "r:gz") as archive:
            archive.extractall(seed_extract_root)
        artifact_root = seed_extract_root / "wob_outputs" / f"wob_seed{seed}"
        if progress is not None:
            progress(f"preflight: validating extracted seed{seed} artifact tree")
        validator_module.validate_artifacts(
            artifact_root,
            expected_seed=seed,
            expected_target_updates=15000,
        )
        metadata = _read_json(artifact_root / "training_metadata.json")
        best_weights = artifact_root / "best_weights.pt"
        best_weights_sha256 = sha256_file(best_weights)
        recorded_best_weights_sha256 = str(metadata["best_weights_sha256"])
        if best_weights_sha256 != recorded_best_weights_sha256:
            raise ValueError(
                f"Extracted best_weights hash mismatch for seed {seed}; "
                f"expected {recorded_best_weights_sha256} from training metadata, "
                f"found {best_weights_sha256}."
            )
        artifacts.append(
            {
                "seed": seed,
                "tarball": str(tarball),
                "sidecar": str(sidecar),
                "artifact_root": str(artifact_root),
                "weights_path": str(best_weights),
                "config_path": str(artifact_root / "config.json"),
                "checkpoint_sha256": best_weights_sha256,
                "best_weights_sha256": best_weights_sha256,
                "updates_completed": int(metadata["updates_completed"]),
                "best_update": int(metadata["best_update"]),
                "best_validation_loss": float(metadata["best_validation_loss"]),
                "target_optimizer_updates": int(metadata["target_optimizer_updates"]),
                "validation_buggy_used_for_fit_select": bool(
                    metadata["validation_buggy_used_for_fit_select"]
                ),
                "locked_test_materialized": bool(metadata["locked_test_materialized"]),
                "locked_test_scored": bool(metadata["locked_test_scored"]),
            }
        )
    return artifacts


def build_r5_wob_report(
    comparison_rows: list[dict[str, str]],
    *,
    eval_manifest_sha256: str,
    readiness_sha256: str,
    metrics_sha256: str,
) -> str:
    lines = [
        "# R5-WOB Non-Locked Identical-Episode Evaluation",
        "",
        f"- Frozen eval manifest SHA256: `{eval_manifest_sha256}`",
        f"- Readiness JSON SHA256: `{readiness_sha256}`",
        f"- Metrics SHA256: `{metrics_sha256}`",
        "- Evaluation rows: 12 calibration-normal episodes + 60 evaluation-buggy episodes.",
        "- Train rows: excluded.",
        "- Locked rows: excluded and unscored.",
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
            "Claim boundary: these are non-locked WOB validation-family results only.",
            "Do not claim locked-test performance, cross-game generalization, or action-conditioning benefit from this report alone.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_r5_wob_identical_episode_evaluation(
    *,
    readiness_json: Path,
    eval_manifest: Path,
    split_csv: Path,
    normal_root: Path,
    test_root: Path,
    output_dir: Path,
    seed_tarballs: dict[int, Path],
    seed_sidecars: dict[int, Path],
    device: str = "cpu",
    batch_size: int = 8,
    n_bootstrap: int = 1000,
    bootstrap_seed: int = 42,
    dry_run: bool = False,
) -> dict[str, Any]:
    readiness, eval_rows = _validate_readiness_and_manifest(readiness_json, eval_manifest)
    train_rows = _load_train_rows(split_csv)
    train_coverage = summarize_source_coverage(
        train_rows,
        normal_root=normal_root,
        test_root=test_root,
    )
    eval_coverage = summarize_source_coverage(
        eval_rows,
        normal_root=normal_root,
        test_root=test_root,
    )
    artifact_infos = _resolve_seed_artifacts(
        seed_tarballs=seed_tarballs,
        seed_sidecars=seed_sidecars,
        extract_root=output_dir / "_seed_artifacts",
    )
    plan = {
        "status": "dry_run" if dry_run else "planned",
        "readiness_json": str(readiness_json),
        "eval_manifest": str(eval_manifest),
        "eval_manifest_sha256": readiness["eval_manifest_sha256"],
        "split_csv": str(split_csv),
        "normal_root": str(normal_root),
        "test_root": str(test_root),
        "train_coverage": train_coverage,
        "eval_coverage": eval_coverage,
        "seed_artifacts": artifact_infos,
        "output_dir": str(output_dir),
        "device": device,
        "batch_size": batch_size,
        "bootstrap_seed": bootstrap_seed,
        "n_bootstrap": n_bootstrap,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "planned_outputs": [str(output_dir / name) for name in R5_WOB_OUTPUT_FILES],
    }
    if dry_run:
        return plan
    if train_coverage["missing_count"] > 0 or eval_coverage["missing_count"] > 0:
        raise ValueError(
            "Full WOB raw coverage is required for a real R5-WOB run. "
            f"train_missing={train_coverage['missing_count']} eval_missing={eval_coverage['missing_count']}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_manifest_path = output_dir / "r5_wob_manifest.csv"
    frozen_manifest_path.write_text(_render_eval_manifest(eval_rows), encoding="utf-8")

    train_lance = _build_lance_from_rows(
        train_rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / "_wob_train_normal.lance",
    )
    normal_eval_rows = [row for row in eval_rows if row["evaluation_role"] == "calibration_normal"]
    buggy_eval_rows = [row for row in eval_rows if row["evaluation_role"] == "evaluation_buggy"]
    normal_lance = _build_lance_from_rows(
        normal_eval_rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / "_wob_validation_normal.lance",
    )
    buggy_lance = _build_lance_from_rows(
        buggy_eval_rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / "_wob_validation_buggy.lance",
    )
    window_manifest_path = output_dir / R5_WOB_WINDOW_MANIFEST
    manifest_rows, dataset_fingerprints = _build_window_manifest(
        normal_lance=normal_lance,
        buggy_lance=buggy_lance,
        eval_rows=eval_rows,
        output_path=window_manifest_path,
    )

    gate8_module = _load_script_module("run_gate8_baselines_from_lance")
    baseline_metadata = gate8_module.run_gate8_baselines(
        manifest_path=window_manifest_path,
        train_lance=train_lance,
        normal_lance=normal_lance,
        buggy_lance=buggy_lance,
        output_dir=output_dir,
        batch_size=max(batch_size, 16),
    )
    baseline_score_path = output_dir / "baseline_scores.csv"
    baseline_rows = read_csv_rows(baseline_score_path)
    gate8_module.validate_baseline_alignment(manifest_rows, baseline_rows)

    per_method_rows: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    lewm_outputs: list[dict[str, Any]] = []

    for artifact in artifact_infos:
        seed = int(artifact["seed"])
        adapter = LeWMAdapter(
            LeWMCheckpointSpec(
                weights_path=Path(artifact["weights_path"]),
                config_path=Path(artifact["config_path"]),
                action_mode=ActionMode.REAL,
                expected_sha256=str(artifact["checkpoint_sha256"]),
                device=device,
            )
        ).load()
        normal_ids = [
            row["window_id"] for row in manifest_rows if row["dataset_name"] == NORMAL_DATASET_NAME
        ]
        buggy_ids = [
            row["window_id"] for row in manifest_rows if row["dataset_name"] == BUGGY_DATASET_NAME
        ]
        raw_score_rows = [
            *_score_dataset(
                normal_lance, normal_ids, adapter, batch_size=batch_size, device=device
            ),
            *_score_dataset(buggy_lance, buggy_ids, adapter, batch_size=batch_size, device=device),
        ]
        validate_score_alignment(manifest_rows, raw_score_rows)
        raw_score_path = write_csv_rows(
            output_dir / f"lewm_scores_seed{seed}.csv",
            raw_score_rows,
            ("window_id", "mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3"),
        )
        lewm_outputs.append(
            {
                **artifact,
                "raw_score_path": str(raw_score_path),
                "raw_score_sha256": sha256_file(raw_score_path),
            }
        )
        scorer_rows: dict[str, list[dict[str, str]]] = {name: [] for name in LEWM_WINDOW_SCORERS}
        for row in raw_score_rows:
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
                        "raw_score_path": str(raw_score_path),
                        "raw_score_sha256": sha256_file(raw_score_path),
                        "checkpoint_sha256": str(artifact["checkpoint_sha256"]),
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
        output_dir / "r5_wob_comparison.csv",
        comparison_rows,
        COMPARISON_FIELDS,
    )
    metrics_payload = {
        "status": "r5_wob_complete",
        "protocol": "wob_identical_episode_nonlocked",
        "readiness_json": str(readiness_json),
        "readiness_sha256": sha256_file(readiness_json),
        "frozen_eval_manifest_path": str(frozen_manifest_path),
        "frozen_eval_manifest_sha256": sha256_file(frozen_manifest_path),
        "window_manifest_path": str(window_manifest_path),
        "window_manifest_sha256": sha256_file(window_manifest_path),
        "episode_score_path": str(episode_scores_path),
        "episode_score_sha256": sha256_file(episode_scores_path),
        "baseline_score_path": str(baseline_score_path),
        "baseline_score_sha256": sha256_file(baseline_score_path),
        "comparison_path": str(comparison_path),
        "comparison_sha256": sha256_file(comparison_path),
        "results": comparison_rows,
        "seed_outputs": lewm_outputs,
        "bootstrap": {
            "seed": bootstrap_seed,
            "n_bootstrap": n_bootstrap,
            "group_key": "source_episode_id",
        },
        "dataset_fingerprints": dataset_fingerprints,
        "baseline_metadata": baseline_metadata,
        "train_coverage": train_coverage,
        "eval_coverage": eval_coverage,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": True,
    }
    metrics_path = _write_json(output_dir / "r5_wob_metrics.json", metrics_payload)
    report_path = _write_report(
        output_dir / "R5_WOB_REPORT.md",
        build_r5_wob_report(
            comparison_rows,
            eval_manifest_sha256=sha256_file(frozen_manifest_path),
            readiness_sha256=sha256_file(readiness_json),
            metrics_sha256=sha256_file(metrics_path),
        ),
    )
    provenance_payload = {
        "status": "r5_wob_complete",
        "environment": runtime_provenance(include_lewm=True),
        "outputs": {
            "r5_wob_manifest.csv": sha256_file(frozen_manifest_path),
            "episode_scores.csv": sha256_file(episode_scores_path),
            "baseline_scores.csv": sha256_file(baseline_score_path),
            "r5_wob_metrics.json": sha256_file(metrics_path),
            "r5_wob_comparison.csv": sha256_file(comparison_path),
            "r5_wob_provenance.json": "",
            "R5_WOB_REPORT.md": sha256_file(report_path),
        },
        "readiness_json_sha256": sha256_file(readiness_json),
        "eval_manifest_sha256": sha256_file(frozen_manifest_path),
        "window_manifest_sha256": sha256_file(window_manifest_path),
        "seed_artifacts": artifact_infos,
        "baseline_metadata": baseline_metadata,
        "dataset_fingerprints": dataset_fingerprints,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    provenance_path = _write_json(output_dir / "r5_wob_provenance.json", provenance_payload)
    provenance_payload["outputs"]["r5_wob_provenance.json"] = sha256_file(provenance_path)
    _write_json(provenance_path, provenance_payload)
    return {
        "status": "r5_wob_complete",
        "frozen_eval_manifest_path": str(frozen_manifest_path),
        "frozen_eval_manifest_sha256": sha256_file(frozen_manifest_path),
        "metrics_path": str(metrics_path),
        "metrics_sha256": sha256_file(metrics_path),
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
        "evaluation_run": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the non-locked WOB R5 identical-episode evaluation bundle."
    )
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS_JSON)
    parser.add_argument("--eval-manifest", type=Path, default=DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--split-csv", type=Path, default=DEFAULT_SPLIT_CSV)
    parser.add_argument("--normal-root", type=Path, required=True)
    parser.add_argument("--test-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed-artifact-tar", action="append", default=[])
    parser.add_argument("--seed-artifact-sha256", action="append", default=[])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_r5_wob_identical_episode_evaluation(
        readiness_json=args.readiness_json,
        eval_manifest=args.eval_manifest,
        split_csv=args.split_csv,
        normal_root=args.normal_root,
        test_root=args.test_root,
        output_dir=args.output_dir,
        seed_tarballs=_parse_keyed_paths(args.seed_artifact_tar),
        seed_sidecars=_parse_keyed_paths(args.seed_artifact_sha256),
        device=args.device,
        batch_size=args.batch_size,
        n_bootstrap=args.n_bootstrap,
        bootstrap_seed=args.bootstrap_seed,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
