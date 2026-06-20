from __future__ import annotations

import argparse
import gc
import json
import tarfile
from pathlib import Path
from typing import Any

from cloud.wob_kaggle_native.common import detect_kaggle_roots

from .lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec, sha256_file
from .lewm_lance_eval import (
    BUGGY_DATASET_NAME,
    MANIFEST_FIELDS,
    NORMAL_DATASET_NAME,
    read_csv_rows,
    runtime_provenance,
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
from .r5_wob_eval import (
    DEFAULT_EVAL_MANIFEST,
    DEFAULT_READINESS_JSON,
    DEFAULT_SPLIT_CSV,
    ROOT,
    SUPPORTED_SEEDS,
    _build_lance_from_rows,
    _load_script_module,
    _load_train_rows,
    _read_json,
    _render_eval_manifest,
    _resolve_seed_artifacts,
    _validate_readiness_and_manifest,
    _write_json,
    _write_report,
    build_r5_wob_report,
    summarize_source_coverage,
)

DEFAULT_INPUT_ROOT = Path("/kaggle/input")
DEFAULT_SUCCESS_TAR = Path("/kaggle/working/r5_wob_identical_episode_outputs.tar.gz")
DEFAULT_FAILURE_TAR = Path("/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz")
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "r5_wob_identical_episode"
WINDOW_MANIFEST_NAME = "_window_manifest.csv"
TRAIN_LANCE_NAME = "_wob_train_normal.lance"
NORMAL_LANCE_NAME = "_wob_validation_normal.lance"
BUGGY_LANCE_NAME = "_wob_validation_buggy.lance"
REPACK_ROOT_NAME = "_repacked_seed_artifacts"
EXTRACT_ROOT_NAME = "_seed_artifacts"
STAGE_ORDER = (
    "preflight",
    "materialize_lance",
    "baseline_scores",
    "lewm_seed42",
    "lewm_seed43",
    "lewm_seed44",
    "aggregate_metrics",
    "validate_package",
)


def _stage_marker_path(output_dir: Path, stage: str) -> Path:
    return output_dir / f"stage_{stage}.json"


def _file_record(path: Path) -> dict[str, str]:
    return {
        "path": str(path),
        "sha256": sha256_file(path),
    }


def _check_runtime_imports() -> dict[str, str]:
    from hydra.utils import instantiate
    from stable_worldmodel.data import LanceDataset, LanceWriter

    return {
        "stable_worldmodel_data": f"{LanceWriter.__module__}:{LanceWriter.__name__}",
        "stable_worldmodel_dataset": f"{LanceDataset.__module__}:{LanceDataset.__name__}",
        "hydra_instantiate": f"{instantiate.__module__}:{instantiate.__name__}",
    }


def _find_unique(root: Path, pattern: str) -> Path | None:
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    return matches[0] if matches else None


def _find_extracted_seed_root(input_root: Path, seed: int) -> Path | None:
    expected = f"wob_seed{seed}_artifacts"
    candidates = sorted(path for path in input_root.rglob(expected) if path.is_dir())
    for candidate in candidates:
        if (candidate / "wob_outputs" / f"wob_seed{seed}").is_dir():
            return candidate
    return None


def _repack_seed_artifact(
    extracted_root: Path, *, seed: int, repack_root: Path
) -> tuple[Path, Path]:
    repack_root.mkdir(parents=True, exist_ok=True)
    tar_path = repack_root / f"wob_seed{seed}_artifacts.tar.gz"
    sha_path = repack_root / f"wob_seed{seed}_artifacts.tar.gz.sha256"
    with tarfile.open(tar_path, "w:gz") as archive:
        for path in sorted(extracted_root.rglob("*")):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(extracted_root).as_posix())
    sha_path.write_text(f"{sha256_file(tar_path)}  {tar_path.name}\n", encoding="utf-8")
    return tar_path, sha_path


def _resolve_seed_inputs(input_root: Path, *, seed: int, repack_root: Path) -> dict[str, str]:
    tarball = _find_unique(input_root, f"wob_seed{seed}_artifacts.tar.gz")
    sidecar = _find_unique(input_root, f"wob_seed{seed}_artifacts.tar.gz.sha256")
    if tarball is not None and sidecar is not None:
        return {
            "seed": str(seed),
            "mode": "direct_tarball",
            "tarball": str(tarball),
            "sidecar": str(sidecar),
        }
    extracted_root = _find_extracted_seed_root(input_root, seed)
    if extracted_root is None:
        raise FileNotFoundError(
            f"Could not locate wob_seed{seed} artifact tarball or extracted artifact folder under {input_root}."
        )
    repacked_tarball, repacked_sidecar = _repack_seed_artifact(
        extracted_root,
        seed=seed,
        repack_root=repack_root,
    )
    return {
        "seed": str(seed),
        "mode": "repacked_extracted_folder",
        "source_root": str(extracted_root),
        "tarball": str(repacked_tarball),
        "sidecar": str(repacked_sidecar),
    }


def _build_window_manifest(
    *,
    normal_lance: Path,
    buggy_lance: Path,
    eval_rows: list[dict[str, str]],
    output_path: Path,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    lance_module = _load_script_module("run_gate8_baselines_from_lance")
    lewm_eval_module = _load_script_module("run_gate7_lance_scoring")
    normal_dataset = lewm_eval_module._lance_dataset(normal_lance, include_metadata=True)
    buggy_dataset = lewm_eval_module._lance_dataset(buggy_lance, include_metadata=True)
    normal_samples = [
        {key: str(normal_dataset[index][key]) for key in lewm_eval_module.METADATA_KEYS}
        for index in range(len(normal_dataset))
    ]
    buggy_samples = [
        {key: str(buggy_dataset[index][key]) for key in lewm_eval_module.METADATA_KEYS}
        for index in range(len(buggy_dataset))
    ]
    calibration_episodes = {
        row["episode_id"] for row in eval_rows if row["evaluation_role"] == "calibration_normal"
    }
    fingerprints = {
        NORMAL_DATASET_NAME: lance_module.FingerprintBuilder.inventory_sha256(normal_lance),
        BUGGY_DATASET_NAME: lance_module.FingerprintBuilder.inventory_sha256(buggy_lance),
    }
    manifest_rows = [
        *lewm_eval_module.canonical_rows_from_samples(
            dataset_name=NORMAL_DATASET_NAME,
            dataset_fingerprint=fingerprints[NORMAL_DATASET_NAME],
            samples=normal_samples,
            calibration_episodes=calibration_episodes,
        ),
        *lewm_eval_module.canonical_rows_from_samples(
            dataset_name=BUGGY_DATASET_NAME,
            dataset_fingerprint=fingerprints[BUGGY_DATASET_NAME],
            samples=buggy_samples,
            calibration_episodes=calibration_episodes,
        ),
    ]
    lewm_eval_module.validate_manifest_rows(
        manifest_rows,
        expected_calibration_episode_count=len(calibration_episodes),
    )
    write_csv_rows(output_path, manifest_rows, MANIFEST_FIELDS)
    return manifest_rows, fingerprints


def _release_cuda_memory() -> None:
    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _smoke_eval_rows(eval_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    calibration = [row for row in eval_rows if row["evaluation_role"] == "calibration_normal"][:2]
    buggy = [row for row in eval_rows if row["evaluation_role"] == "evaluation_buggy"][:3]
    if len(calibration) < 2 or len(buggy) < 2:
        raise ValueError("Smoke mode needs at least 2 calibration-normal and 2 buggy rows.")
    return [*calibration, *buggy]


def _write_stage_marker(
    output_dir: Path,
    *,
    stage: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "stage": stage,
        "schema_version": 1,
        **payload,
    }
    _write_json(_stage_marker_path(output_dir, stage), payload)
    return payload


def _load_stage_marker(output_dir: Path, stage: str) -> dict[str, Any]:
    path = _stage_marker_path(output_dir, stage)
    if not path.is_file():
        raise FileNotFoundError(f"Missing stage marker: {path}")
    return _read_json(path)


def _validate_stage_marker(
    output_dir: Path,
    stage: str,
    *,
    expected_smoke: bool,
) -> dict[str, Any]:
    payload = _load_stage_marker(output_dir, stage)
    if bool(payload.get("smoke", False)) != expected_smoke:
        raise ValueError(
            f"Stage {stage} smoke mismatch: expected smoke={expected_smoke}, found {payload.get('smoke')}"
        )
    for item in payload.get("files", {}).values():
        path = Path(item["path"])
        if not path.is_file():
            raise FileNotFoundError(f"Stage {stage} missing output file: {path}")
        if item.get("sha256") and sha256_file(path) != item["sha256"]:
            raise ValueError(f"Stage {stage} hash mismatch for {path}")
    return payload


def validate_stage_outputs(output_dir: Path, *, smoke: bool) -> dict[str, Any]:
    stages: dict[str, Any] = {}
    for stage in STAGE_ORDER:
        marker_path = _stage_marker_path(output_dir, stage)
        if not marker_path.is_file():
            stages[stage] = {"status": "missing"}
            continue
        try:
            payload = _validate_stage_marker(output_dir, stage, expected_smoke=smoke)
        except Exception as exc:  # pragma: no cover - exercised through CLI/tests
            stages[stage] = {"status": "invalid", "error": str(exc)}
            continue
        stages[stage] = {
            "status": "complete",
            "marker": str(marker_path),
            "summary_status": payload.get("status", "complete"),
        }
    return {
        "status": "stage_outputs_validated",
        "output_dir": str(output_dir),
        "smoke": smoke,
        "stages": stages,
    }


def _maybe_skip(output_dir: Path, stage: str, *, smoke: bool, force: bool) -> dict[str, Any] | None:
    if force:
        return None
    try:
        return _validate_stage_marker(output_dir, stage, expected_smoke=smoke)
    except Exception:
        return None


def run_preflight(
    *,
    input_root: Path,
    readiness_json: Path,
    eval_manifest: Path,
    split_csv: Path,
    output_dir: Path,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    cached = _maybe_skip(output_dir, "preflight", smoke=smoke, force=force)
    if cached is not None:
        return cached
    output_dir.mkdir(parents=True, exist_ok=True)
    readiness, eval_rows = _validate_readiness_and_manifest(readiness_json, eval_manifest)
    train_rows = _load_train_rows(split_csv)
    resolved_eval_rows = _smoke_eval_rows(eval_rows) if smoke else eval_rows
    normal_root, test_root = detect_kaggle_roots(input_root)
    runtime_imports = _check_runtime_imports()
    repack_root = output_dir / REPACK_ROOT_NAME
    seed_inputs = {
        seed: _resolve_seed_inputs(input_root, seed=seed, repack_root=repack_root)
        for seed in SUPPORTED_SEEDS
    }
    artifact_infos = _resolve_seed_artifacts(
        seed_tarballs={seed: Path(info["tarball"]) for seed, info in seed_inputs.items()},
        seed_sidecars={seed: Path(info["sidecar"]) for seed, info in seed_inputs.items()},
        extract_root=output_dir / EXTRACT_ROOT_NAME,
    )
    train_coverage = summarize_source_coverage(
        train_rows,
        normal_root=normal_root,
        test_root=test_root,
    )
    eval_coverage = summarize_source_coverage(
        resolved_eval_rows,
        normal_root=normal_root,
        test_root=test_root,
    )
    files: dict[str, dict[str, str]] = {
        "readiness_json": _file_record(readiness_json),
        "eval_manifest": _file_record(eval_manifest),
        "split_csv": _file_record(split_csv),
    }
    for artifact in artifact_infos:
        seed = int(artifact["seed"])
        files[f"seed{seed}_tarball"] = _file_record(Path(artifact["tarball"]))
        files[f"seed{seed}_sidecar"] = _file_record(Path(artifact["sidecar"]))
        files[f"seed{seed}_weights"] = _file_record(Path(artifact["weights_path"]))
        files[f"seed{seed}_config"] = _file_record(Path(artifact["config_path"]))
        files[f"seed{seed}_metadata"] = _file_record(
            Path(artifact["artifact_root"]) / "training_metadata.json"
        )
    payload = {
        "status": "preflight_complete",
        "smoke": smoke,
        "input_root": str(input_root),
        "normal_root": str(normal_root),
        "test_root": str(test_root),
        "readiness_json": str(readiness_json),
        "split_csv": str(split_csv),
        "runtime_imports": runtime_imports,
        "train_coverage": train_coverage,
        "eval_coverage": eval_coverage,
        "eval_row_count": len(resolved_eval_rows),
        "frozen_eval_row_count": len(eval_rows),
        "seed_inputs": seed_inputs,
        "seed_artifacts": artifact_infos,
        "files": files,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, stage="preflight", payload=payload)


def run_materialize_lance(
    *,
    readiness_json: Path,
    eval_manifest: Path,
    split_csv: Path,
    output_dir: Path,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    cached = _maybe_skip(output_dir, "materialize_lance", smoke=smoke, force=force)
    if cached is not None:
        return cached
    preflight = _validate_stage_marker(output_dir, "preflight", expected_smoke=smoke)
    readiness, eval_rows = _validate_readiness_and_manifest(readiness_json, eval_manifest)
    train_rows = _load_train_rows(split_csv)
    selected_eval_rows = _smoke_eval_rows(eval_rows) if smoke else eval_rows
    normal_root = Path(preflight["normal_root"])
    test_root = Path(preflight["test_root"])
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_manifest_path = output_dir / "r5_wob_manifest.csv"
    frozen_manifest_path.write_text(_render_eval_manifest(selected_eval_rows), encoding="utf-8")
    train_lance = _build_lance_from_rows(
        train_rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / TRAIN_LANCE_NAME,
    )
    normal_rows = [
        row for row in selected_eval_rows if row["evaluation_role"] == "calibration_normal"
    ]
    buggy_rows = [row for row in selected_eval_rows if row["evaluation_role"] == "evaluation_buggy"]
    normal_lance = _build_lance_from_rows(
        normal_rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / NORMAL_LANCE_NAME,
    )
    buggy_lance = _build_lance_from_rows(
        buggy_rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / BUGGY_LANCE_NAME,
    )
    manifest_rows, dataset_fingerprints = _build_window_manifest(
        normal_lance=normal_lance,
        buggy_lance=buggy_lance,
        eval_rows=selected_eval_rows,
        output_path=output_dir / WINDOW_MANIFEST_NAME,
    )
    payload = {
        "status": "materialize_complete",
        "smoke": smoke,
        "readiness_sha256": readiness["eval_manifest_sha256"],
        "eval_row_count": len(selected_eval_rows),
        "window_row_count": len(manifest_rows),
        "dataset_fingerprints": dataset_fingerprints,
        "files": {
            "r5_wob_manifest.csv": _file_record(frozen_manifest_path),
            TRAIN_LANCE_NAME: _file_record(train_lance),
            NORMAL_LANCE_NAME: _file_record(normal_lance),
            BUGGY_LANCE_NAME: _file_record(buggy_lance),
            WINDOW_MANIFEST_NAME: _file_record(output_dir / WINDOW_MANIFEST_NAME),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, stage="materialize_lance", payload=payload)


def run_baseline_scores(
    *,
    output_dir: Path,
    baseline_batch_size: int,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    cached = _maybe_skip(output_dir, "baseline_scores", smoke=smoke, force=force)
    if cached is not None:
        return cached
    materialize = _validate_stage_marker(output_dir, "materialize_lance", expected_smoke=smoke)
    gate8_module = _load_script_module("run_gate8_baselines_from_lance")
    baseline_metadata = gate8_module.run_gate8_baselines(
        manifest_path=Path(materialize["files"][WINDOW_MANIFEST_NAME]["path"]),
        train_lance=Path(materialize["files"][TRAIN_LANCE_NAME]["path"]),
        normal_lance=Path(materialize["files"][NORMAL_LANCE_NAME]["path"]),
        buggy_lance=Path(materialize["files"][BUGGY_LANCE_NAME]["path"]),
        output_dir=output_dir,
        batch_size=baseline_batch_size,
    )
    manifest_rows = read_csv_rows(Path(materialize["files"][WINDOW_MANIFEST_NAME]["path"]))
    baseline_path = output_dir / "baseline_scores.csv"
    baseline_rows = read_csv_rows(baseline_path)
    gate8_module.validate_baseline_alignment(manifest_rows, baseline_rows)
    payload = {
        "status": "baseline_complete",
        "smoke": smoke,
        "batch_size": baseline_batch_size,
        "baseline_metadata": baseline_metadata,
        "files": {
            "baseline_scores.csv": _file_record(baseline_path),
            "gate8_metadata.json": _file_record(output_dir / "gate8_metadata.json"),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, stage="baseline_scores", payload=payload)


def run_lewm_seed_stage(
    *,
    output_dir: Path,
    seed: int,
    device: str,
    lewm_batch_size: int,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    stage_name = f"lewm_seed{seed}"
    cached = _maybe_skip(output_dir, stage_name, smoke=smoke, force=force)
    if cached is not None:
        return cached
    materialize = _validate_stage_marker(output_dir, "materialize_lance", expected_smoke=smoke)
    preflight = _validate_stage_marker(output_dir, "preflight", expected_smoke=smoke)
    manifest_rows = read_csv_rows(Path(materialize["files"][WINDOW_MANIFEST_NAME]["path"]))
    artifact = next(item for item in preflight["seed_artifacts"] if int(item["seed"]) == int(seed))
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
    lewm_eval_module = _load_script_module("run_gate7_lance_scoring")
    try:
        raw_score_rows = [
            *lewm_eval_module._score_dataset(
                Path(materialize["files"][NORMAL_LANCE_NAME]["path"]),
                normal_ids,
                adapter,
                batch_size=lewm_batch_size,
                device=device,
            ),
            *lewm_eval_module._score_dataset(
                Path(materialize["files"][BUGGY_LANCE_NAME]["path"]),
                buggy_ids,
                adapter,
                batch_size=lewm_batch_size,
                device=device,
            ),
        ]
    finally:
        del adapter
        _release_cuda_memory()
    validate_score_alignment(manifest_rows, raw_score_rows)
    score_path = write_csv_rows(
        output_dir / f"lewm_scores_seed{seed}.csv",
        raw_score_rows,
        ("window_id", "mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3"),
    )
    payload = {
        "status": "lewm_seed_complete",
        "smoke": smoke,
        "seed": seed,
        "device": device,
        "batch_size": lewm_batch_size,
        "checkpoint_sha256": artifact["checkpoint_sha256"],
        "files": {
            f"lewm_scores_seed{seed}.csv": _file_record(score_path),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, stage=stage_name, payload=payload)


def assemble_r5_wob_from_stages(
    *,
    output_dir: Path,
    readiness_json: Path,
    bootstrap_seed: int,
    n_bootstrap: int,
    smoke: bool,
) -> dict[str, Any]:
    preflight = _validate_stage_marker(output_dir, "preflight", expected_smoke=smoke)
    materialize = _validate_stage_marker(output_dir, "materialize_lance", expected_smoke=smoke)
    baseline_stage = _validate_stage_marker(output_dir, "baseline_scores", expected_smoke=smoke)
    manifest_rows = read_csv_rows(Path(materialize["files"][WINDOW_MANIFEST_NAME]["path"]))
    baseline_rows = read_csv_rows(Path(baseline_stage["files"]["baseline_scores.csv"]["path"]))
    gate8_module = _load_script_module("run_gate8_baselines_from_lance")
    gate8_module.validate_baseline_alignment(manifest_rows, baseline_rows)
    per_method_rows: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    lewm_outputs: list[dict[str, Any]] = []

    for seed in SUPPORTED_SEEDS:
        stage = _validate_stage_marker(output_dir, f"lewm_seed{seed}", expected_smoke=smoke)
        raw_score_path = Path(stage["files"][f"lewm_scores_seed{seed}.csv"]["path"])
        raw_score_rows = read_csv_rows(raw_score_path)
        validate_score_alignment(manifest_rows, raw_score_rows)
        artifact = next(
            item for item in preflight["seed_artifacts"] if int(item["seed"]) == int(seed)
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
                    "raw_score_path": str(output_dir / "baseline_scores.csv"),
                    "raw_score_sha256": sha256_file(output_dir / "baseline_scores.csv"),
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
    frozen_manifest_path = output_dir / "r5_wob_manifest.csv"
    metrics_payload = {
        "status": "r5_wob_smoke_complete" if smoke else "r5_wob_complete",
        "protocol": "wob_identical_episode_nonlocked",
        "smoke": smoke,
        "paper_valid": not smoke,
        "readiness_json": str(readiness_json),
        "readiness_sha256": sha256_file(readiness_json),
        "frozen_eval_manifest_path": str(frozen_manifest_path),
        "frozen_eval_manifest_sha256": sha256_file(frozen_manifest_path),
        "window_manifest_path": str(output_dir / WINDOW_MANIFEST_NAME),
        "window_manifest_sha256": sha256_file(output_dir / WINDOW_MANIFEST_NAME),
        "episode_score_path": str(episode_scores_path),
        "episode_score_sha256": sha256_file(episode_scores_path),
        "baseline_score_path": str(output_dir / "baseline_scores.csv"),
        "baseline_score_sha256": sha256_file(output_dir / "baseline_scores.csv"),
        "comparison_path": str(comparison_path),
        "comparison_sha256": sha256_file(comparison_path),
        "results": comparison_rows,
        "seed_outputs": lewm_outputs,
        "bootstrap": {
            "seed": bootstrap_seed,
            "n_bootstrap": n_bootstrap,
            "group_key": "source_episode_id",
        },
        "dataset_fingerprints": materialize["dataset_fingerprints"],
        "baseline_metadata": baseline_stage["baseline_metadata"],
        "train_coverage": preflight["train_coverage"],
        "eval_coverage": preflight["eval_coverage"],
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": not smoke,
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
        "status": "r5_wob_smoke_complete" if smoke else "r5_wob_complete",
        "smoke": smoke,
        "paper_valid": not smoke,
        "environment": runtime_provenance(include_lewm=True),
        "outputs": {
            "r5_wob_manifest.csv": sha256_file(frozen_manifest_path),
            "episode_scores.csv": sha256_file(episode_scores_path),
            "baseline_scores.csv": sha256_file(output_dir / "baseline_scores.csv"),
            "r5_wob_metrics.json": sha256_file(metrics_path),
            "r5_wob_comparison.csv": sha256_file(comparison_path),
            "r5_wob_provenance.json": "",
            "R5_WOB_REPORT.md": sha256_file(report_path),
        },
        "readiness_json_sha256": sha256_file(readiness_json),
        "eval_manifest_sha256": sha256_file(frozen_manifest_path),
        "window_manifest_sha256": sha256_file(output_dir / WINDOW_MANIFEST_NAME),
        "seed_artifacts": preflight["seed_artifacts"],
        "baseline_metadata": baseline_stage["baseline_metadata"],
        "dataset_fingerprints": materialize["dataset_fingerprints"],
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    provenance_path = _write_json(output_dir / "r5_wob_provenance.json", provenance_payload)
    provenance_payload["outputs"]["r5_wob_provenance.json"] = sha256_file(provenance_path)
    _write_json(provenance_path, provenance_payload)
    return {
        "comparison_rows": comparison_rows,
        "episode_scores_path": episode_scores_path,
        "comparison_path": comparison_path,
        "metrics_path": metrics_path,
        "report_path": report_path,
        "provenance_path": provenance_path,
        "seed_outputs": lewm_outputs,
    }


def run_aggregate_metrics(
    *,
    output_dir: Path,
    readiness_json: Path,
    bootstrap_seed: int,
    n_bootstrap: int,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    cached = _maybe_skip(output_dir, "aggregate_metrics", smoke=smoke, force=force)
    if cached is not None:
        return cached
    assembled = assemble_r5_wob_from_stages(
        output_dir=output_dir,
        readiness_json=readiness_json,
        bootstrap_seed=bootstrap_seed,
        n_bootstrap=n_bootstrap,
        smoke=smoke,
    )
    payload = {
        "status": "aggregate_complete",
        "smoke": smoke,
        "bootstrap_seed": bootstrap_seed,
        "n_bootstrap": n_bootstrap,
        "files": {
            "episode_scores.csv": _file_record(assembled["episode_scores_path"]),
            "r5_wob_comparison.csv": _file_record(assembled["comparison_path"]),
            "r5_wob_metrics.json": _file_record(assembled["metrics_path"]),
            "R5_WOB_REPORT.md": _file_record(assembled["report_path"]),
            "r5_wob_provenance.json": _file_record(assembled["provenance_path"]),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, stage="aggregate_metrics", payload=payload)


def run_validate_package(
    *,
    output_dir: Path,
    readiness_json: Path,
    success_tarball: Path,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    cached = _maybe_skip(output_dir, "validate_package", smoke=smoke, force=force)
    if cached is not None:
        return cached
    if smoke:
        raise ValueError(
            "Smoke outputs are intentionally not package-valid for paper or Kaggle intake."
        )
    _validate_stage_marker(output_dir, "aggregate_metrics", expected_smoke=False)
    stage_validation = validate_stage_outputs(output_dir, smoke=False)
    invalid = [
        name
        for name, state in stage_validation["stages"].items()
        if name != "validate_package" and state["status"] != "complete"
    ]
    if invalid:
        raise ValueError(f"Cannot package staged R5-WOB outputs; incomplete stages: {invalid}")
    validate_module = _load_script_module("validate_r5_wob_evaluation")
    validator_result = validate_module.validate_r5_wob(output_dir, readiness_json)
    success_tarball.parent.mkdir(parents=True, exist_ok=True)
    success_sha = Path(str(success_tarball) + ".sha256")
    if success_tarball.exists():
        success_tarball.unlink()
    if success_sha.exists():
        success_sha.unlink()
    with tarfile.open(success_tarball, "w:gz") as archive:
        for name in (
            "r5_wob_manifest.csv",
            "episode_scores.csv",
            "baseline_scores.csv",
            "r5_wob_metrics.json",
            "r5_wob_comparison.csv",
            "r5_wob_provenance.json",
            "R5_WOB_REPORT.md",
        ):
            archive.add(output_dir / name, arcname=name)
    success_sha.write_text(
        f"{sha256_file(success_tarball)}  {success_tarball.name}\n",
        encoding="utf-8",
    )
    payload = {
        "status": "validate_package_complete",
        "smoke": False,
        "validator_result": validator_result,
        "files": {
            "success_tarball": _file_record(success_tarball),
            "success_tarball_sha256": _file_record(success_sha),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, stage="validate_package", payload=payload)


def run_stage(
    *,
    stage: str,
    input_root: Path,
    readiness_json: Path,
    eval_manifest: Path,
    split_csv: Path,
    output_dir: Path,
    baseline_batch_size: int,
    lewm_batch_size: int,
    device: str,
    bootstrap_seed: int,
    n_bootstrap: int,
    success_tarball: Path,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    if stage == "preflight":
        return run_preflight(
            input_root=input_root,
            readiness_json=readiness_json,
            eval_manifest=eval_manifest,
            split_csv=split_csv,
            output_dir=output_dir,
            smoke=smoke,
            force=force,
        )
    if stage == "materialize_lance":
        return run_materialize_lance(
            readiness_json=readiness_json,
            eval_manifest=eval_manifest,
            split_csv=split_csv,
            output_dir=output_dir,
            smoke=smoke,
            force=force,
        )
    if stage == "baseline_scores":
        return run_baseline_scores(
            output_dir=output_dir,
            baseline_batch_size=baseline_batch_size,
            smoke=smoke,
            force=force,
        )
    if stage.startswith("lewm_seed"):
        seed = int(stage.removeprefix("lewm_seed"))
        return run_lewm_seed_stage(
            output_dir=output_dir,
            seed=seed,
            device=device,
            lewm_batch_size=lewm_batch_size,
            smoke=smoke,
            force=force,
        )
    if stage == "aggregate_metrics":
        return run_aggregate_metrics(
            output_dir=output_dir,
            readiness_json=readiness_json,
            bootstrap_seed=bootstrap_seed,
            n_bootstrap=n_bootstrap,
            smoke=smoke,
            force=force,
        )
    if stage == "validate_package":
        return run_validate_package(
            output_dir=output_dir,
            readiness_json=readiness_json,
            success_tarball=success_tarball,
            smoke=smoke,
            force=force,
        )
    raise ValueError(f"Unsupported R5-WOB stage: {stage}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the staged non-locked R5-WOB evaluation.")
    parser.add_argument("--stage", choices=STAGE_ORDER, required=True)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS_JSON)
    parser.add_argument("--eval-manifest", type=Path, default=DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--split-csv", type=Path, default=DEFAULT_SPLIT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--success-tarball", type=Path, default=DEFAULT_SUCCESS_TAR)
    parser.add_argument("--baseline-batch-size", type=int, default=4)
    parser.add_argument("--lewm-batch-size", type=int, default=2)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_stage(
        stage=args.stage,
        input_root=args.input_root,
        readiness_json=args.readiness_json,
        eval_manifest=args.eval_manifest,
        split_csv=args.split_csv,
        output_dir=args.output_dir,
        baseline_batch_size=args.baseline_batch_size,
        lewm_batch_size=args.lewm_batch_size,
        device=args.device,
        bootstrap_seed=args.bootstrap_seed,
        n_bootstrap=args.n_bootstrap,
        success_tarball=args.success_tarball,
        smoke=args.smoke,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
