"""Fail-closed staged entrypoint for the four-role R5-XGame protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Sequence

from glitch_detection.kaggle_automation import FingerprintBuilder
from glitch_detection.lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec, sha256_file
from glitch_detection.lewm_lance_eval import (
    BUGGY_DATASET_NAME,
    NORMAL_DATASET_NAME,
    _score_dataset,
    read_csv_rows,
    runtime_provenance,
    validate_score_alignment,
    write_csv_rows,
)
from glitch_detection.r5_tempglitch_eval import (
    BASELINE_WINDOW_SCORERS,
    EPISODE_AGGREGATIONS,
    EPISODE_SCORE_FIELDS,
    LEWM_WINDOW_SCORERS,
    _float_text,
    _lewm_window_scores,
    aggregate_episode_scores,
)
from glitch_detection.r5_wob_eval import (
    _build_lance_from_rows,
    _build_window_manifest,
    _load_script_module,
    _write_json,
)
from glitch_detection.r5_xgame_live import train_fresh_seed
from glitch_detection.r5_xgame_metrics import evaluate_r5_xgame_binary_scores
from glitch_detection.r5_xgame_protocol import (
    BUGGY_EVAL_ROLE,
    CALIBRATION_ROLE,
    NORMAL_EVAL_ROLE,
    TRAIN_ROLE,
    validate_r5_xgame_manifest,
)
from glitch_detection.statistics import bootstrap_metric_ci
from glitch_detection.wob_kaggle_common import detect_kaggle_roots, iter_kaggle_dataset_roots

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROLE_COUNTS = {
    TRAIN_ROLE: 36,
    CALIBRATION_ROLE: 12,
    NORMAL_EVAL_ROLE: 12,
    BUGGY_EVAL_ROLE: 60,
}
SUPPORTED_SEEDS = (42, 43, 44)
STAGES = (
    "preflight",
    "materialize",
    "baseline_score",
    "train_lewm",
    "lewm_score",
    "aggregate_episode",
    "calibrate_thresholds",
    "evaluate_binary",
    "bootstrap_ci",
    "package",
    "validate_package",
)
TRAIN_LANCE_NAME = "_r5_xgame_train_normal.lance"
NORMAL_LANCE_NAME = "_r5_xgame_calibration_eval_normal.lance"
BUGGY_LANCE_NAME = "_r5_xgame_eval_buggy.lance"
WINDOW_MANIFEST_NAME = "r5_xgame_window_manifest.csv"
BASELINE_SCORE_NAME = "r5_xgame_baseline_scores.csv"
EPISODE_SCORE_NAME = "r5_xgame_episode_scores.csv"
COMPARISON_NAME = "r5_xgame_comparison.csv"
METRICS_NAME = "r5_xgame_metrics.json"
PROVENANCE_NAME = "r5_xgame_provenance.json"
REPORT_NAME = "R5_XGAME_REPORT.md"
TARBALL_NAME = "r5_xgame_outputs.tar.gz"
LEWM_SCORE_FIELDS = ("window_id", "mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3")
PLANNED_OUTPUTS = (
    "r5_xgame_manifest.csv",
    WINDOW_MANIFEST_NAME,
    BASELINE_SCORE_NAME,
    "r5_xgame_lewm_scores_seed42.csv",
    "r5_xgame_lewm_scores_seed43.csv",
    "r5_xgame_lewm_scores_seed44.csv",
    EPISODE_SCORE_NAME,
    COMPARISON_NAME,
    METRICS_NAME,
    REPORT_NAME,
    PROVENANCE_NAME,
    TARBALL_NAME,
    f"{TARBALL_NAME}.sha256",
)
PACKAGE_OUTPUT_NAMES = tuple(
    name
    for name in PLANNED_OUTPUTS
    if not name.endswith(".tar.gz") and not name.endswith(".sha256")
)
PACKAGE_STAGE_MARKER_NAMES = tuple(
    f"stage_{stage}.json" for stage in STAGES if stage != "validate_package"
)
PRE_PACKAGE_STAGE_MARKER_NAMES = tuple(
    name for name in PACKAGE_STAGE_MARKER_NAMES if name != "stage_package.json"
)
PACKAGE_MEMBER_NAMES = PACKAGE_OUTPUT_NAMES + PACKAGE_STAGE_MARKER_NAMES
XGAME_COMPARISON_FIELDS = (
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
    "fpr_at_95_tpr",
    "balanced_accuracy",
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
    "calibration_episode_ids",
    "auroc_ci_lower",
    "auroc_ci_upper",
    "f1_ci_lower",
    "f1_ci_upper",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _validate_seed_selection(seeds: Sequence[int], *, allow_subset: bool) -> tuple[int, ...]:
    ordered = tuple(dict.fromkeys(int(seed) for seed in seeds))
    invalid = [seed for seed in ordered if seed not in SUPPORTED_SEEDS]
    if invalid:
        raise ValueError(f"Unsupported R5-XGame seeds: {invalid}")
    if not allow_subset and ordered != SUPPORTED_SEEDS:
        raise ValueError("R5-XGame requires fresh seeds 42, 43, and 44.")
    if not ordered:
        raise ValueError("R5-XGame requires at least one seed.")
    return ordered


def _role_hash(rows: Sequence[dict[str, str]], roles: set[str]) -> str:
    values = [
        f"{row['evaluation_role']},{row['label']},{row['source']},{row['episode_id']}"
        for row in rows
        if row["evaluation_role"] in roles
    ]
    return hashlib.sha256("\n".join(sorted(values)).encode()).hexdigest()


def _validate_counts(rows: Sequence[dict[str, str]]) -> dict[str, int]:
    counts = validate_r5_xgame_manifest(rows)
    if counts != EXPECTED_ROLE_COUNTS:
        raise ValueError(
            f"R5-XGame role counts changed: expected {EXPECTED_ROLE_COUNTS}, found {counts}."
        )
    return counts


def _normalize_rows(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        label = row["label"].strip()
        normalized.append(
            {
                **row,
                "category": row.get("category") or "world_of_bugs",
                "action_mode": row.get("action_mode") or "real",
                "label": label,
            }
        )
    return normalized


def _resolve_source_path(row: dict[str, str], *, normal_root: Path, test_root: Path) -> Path:
    root = normal_root if row["label"] == "Normal" else test_root
    return root / Path(row["source"])


def _coverage(
    rows: Sequence[dict[str, str]], *, normal_root: Path, test_root: Path
) -> dict[str, Any]:
    missing = [
        str(_resolve_source_path(row, normal_root=normal_root, test_root=test_root))
        for row in rows
        if not _resolve_source_path(row, normal_root=normal_root, test_root=test_root).is_file()
    ]
    return {
        "required_count": len(rows),
        "resolved_count": len(rows) - len(missing),
        "missing_count": len(missing),
        "missing_examples": missing[:10],
    }


def _reject_old_r5_wob_inputs(input_root: Path, output_dir: Path) -> None:
    lowered_output = output_dir.as_posix().lower()
    if "r5_wob" in lowered_output or "wob_seed" in lowered_output:
        raise ValueError("R5-XGame refuses to write into an old R5-WOB artifact path.")
    suspicious = []
    for root in iter_kaggle_dataset_roots(input_root):
        lowered = root.as_posix().lower()
        if "r5_wob" in lowered or "wob_seed" in lowered or "checkpoint" in lowered:
            suspicious.append(str(root))
    if suspicious:
        raise ValueError(f"R5-XGame refuses old R5-WOB/checkpoint inputs: {suspicious[:5]}")


def _stage_marker_path(output_dir: Path, stage: str) -> Path:
    return output_dir / f"stage_{stage}.json"


def _file_record(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Cannot record missing path: {path}")
    digest = FingerprintBuilder.inventory_sha256(path) if path.is_dir() else sha256_file(path)
    return {
        "path": str(path),
        "path_type": "directory" if path.is_dir() else "file",
        "sha256": digest,
    }


def _write_stage_marker(output_dir: Path, stage: str, payload: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    marker = {"schema_version": 1, "stage": stage, **payload}
    _write_json(_stage_marker_path(output_dir, stage), marker)
    return marker


def _load_stage_marker(output_dir: Path, stage: str) -> dict[str, Any]:
    path = _stage_marker_path(output_dir, stage)
    if not path.is_file():
        raise FileNotFoundError(f"Missing R5-XGame stage marker: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _require_safe_flags(payload: dict[str, Any], *, context: str) -> None:
    for field in (
        "validation_buggy_used_for_fit_select",
        "locked_test_materialized",
        "locked_test_scored",
    ):
        if payload.get(field) is not False:
            raise ValueError(f"Unsafe {context} flag: {field}")


def _package_stage_payload(*, provenance_path: Path) -> dict[str, Any]:
    return {
        "status": "package_complete",
        "package_members": list(PACKAGE_MEMBER_NAMES),
        "package_member_count": len(PACKAGE_MEMBER_NAMES),
        "tarball_name": TARBALL_NAME,
        "sha256_sidecar_name": f"{TARBALL_NAME}.sha256",
        "files": {
            PROVENANCE_NAME: _file_record(provenance_path),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def _write_package_stage_snapshot(snapshot_path: Path, *, provenance_path: Path) -> dict[str, Any]:
    marker = {
        "schema_version": 1,
        "stage": "package",
        **_package_stage_payload(provenance_path=provenance_path),
    }
    _write_json(snapshot_path, marker)
    return marker


def _package_contract_paths(output_dir: Path) -> list[Path]:
    missing = [
        name
        for name in (*PACKAGE_OUTPUT_NAMES, *PRE_PACKAGE_STAGE_MARKER_NAMES)
        if not (output_dir / name).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            f"R5-XGame package contract is incomplete before tarball creation: {sorted(missing)}"
        )
    return [output_dir / name for name in (*PACKAGE_OUTPUT_NAMES, *PRE_PACKAGE_STAGE_MARKER_NAMES)]


def _assert_score_rows_complete(
    manifest_rows: Sequence[dict[str, str]],
    raw_rows: Sequence[dict[str, str]],
    *,
    context: str,
) -> None:
    expected_rows = len(manifest_rows)
    actual_rows = len(raw_rows)
    if actual_rows != expected_rows:
        raise ValueError(
            f"{context} row count mismatch: expected {expected_rows}, found {actual_rows}."
        )
    validate_score_alignment(manifest_rows, raw_rows)


def _seed_score_path(output_dir: Path, seed: int) -> Path:
    return output_dir / f"r5_xgame_lewm_scores_seed{seed}.csv"


def _write_csv_rows_atomic(
    path: Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        tmp_path = Path(handle.name)
    try:
        write_csv_rows(tmp_path, rows, tuple(fieldnames))
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return path


def validate_existing_lewm_score_file(
    output_dir: Path,
    manifest_rows: Sequence[dict[str, str]],
    *,
    seed: int,
) -> dict[str, Any]:
    score_path = _seed_score_path(output_dir, seed)
    if not score_path.is_file():
        raise FileNotFoundError(f"Missing R5-XGame score CSV for seed{seed}: {score_path}")
    raw_rows = read_csv_rows(score_path)
    _assert_score_rows_complete(
        manifest_rows, raw_rows, context=f"r5_xgame_lewm_scores_seed{seed}.csv"
    )
    return {
        "path": str(score_path),
        "sha256": sha256_file(score_path),
        "row_count": len(raw_rows),
    }


def preflight(
    manifest: Path, input_root: Path, output_dir: Path, seeds: list[int]
) -> dict[str, object]:
    rows = _normalize_rows(_read_manifest(manifest))
    counts = _validate_counts(rows)
    _reject_old_r5_wob_inputs(input_root, output_dir)
    try:
        normal_root, test_root = detect_kaggle_roots(input_root)
    except FileNotFoundError:
        normal_root = input_root
        test_root = input_root
    coverage_by_role = {
        role: _coverage(
            [row for row in rows if row["evaluation_role"] == role],
            normal_root=normal_root,
            test_root=test_root,
        )
        for role in EXPECTED_ROLE_COUNTS
    }
    missing_by_role = {
        role: [
            str(_resolve_source_path(row, normal_root=normal_root, test_root=test_root))
            for row in rows
            if row["evaluation_role"] == role
            and not _resolve_source_path(
                row, normal_root=normal_root, test_root=test_root
            ).is_file()
        ]
        for role in EXPECTED_ROLE_COUNTS
    }
    payload = {
        "status": "preflight_complete"
        if not any(missing_by_role.values())
        else "preflight_missing_inputs",
        "manifest": str(manifest),
        "manifest_sha256": _sha256(manifest),
        "role_counts": counts,
        "role_hashes": {
            "train": _role_hash(rows, {TRAIN_ROLE}),
            "calibration": _role_hash(rows, {CALIBRATION_ROLE}),
            "evaluation": _role_hash(rows, {NORMAL_EVAL_ROLE, BUGGY_EVAL_ROLE}),
        },
        "seeds": seeds,
        "input_root": str(input_root),
        "normal_root": str(normal_root),
        "test_root": str(test_root),
        "coverage_by_role": coverage_by_role,
        "missing_by_role": missing_by_role,
        "old_r5_wob_checkpoint_reused": False,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    _write_stage_marker(output_dir, "preflight", payload)
    return payload


def run_materialize(*, manifest: Path, output_dir: Path) -> dict[str, Any]:
    preflight_marker = _load_stage_marker(output_dir, "preflight")
    if preflight_marker["status"] != "preflight_complete":
        raise ValueError("R5-XGame materialization requires a complete preflight.")
    rows = _normalize_rows(_read_manifest(manifest))
    _validate_counts(rows)
    role_rows = {
        role: [row for row in rows if row["evaluation_role"] == role]
        for role in EXPECTED_ROLE_COUNTS
    }
    for stale in (TRAIN_LANCE_NAME, NORMAL_LANCE_NAME, BUGGY_LANCE_NAME):
        path = output_dir / stale
        if path.exists():
            shutil.rmtree(path)
    frozen_manifest = output_dir / "r5_xgame_manifest.csv"
    shutil.copyfile(manifest, frozen_manifest)
    normal_root = Path(str(preflight_marker["normal_root"]))
    test_root = Path(str(preflight_marker["test_root"]))
    train_lance = _build_lance_from_rows(
        role_rows[TRAIN_ROLE],
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / TRAIN_LANCE_NAME,
        progress=lambda message: print(f"[r5_xgame] {message}", flush=True),
        progress_label="materialize/train_normal",
    )
    normal_lance = _build_lance_from_rows(
        [*role_rows[CALIBRATION_ROLE], *role_rows[NORMAL_EVAL_ROLE]],
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / NORMAL_LANCE_NAME,
        progress=lambda message: print(f"[r5_xgame] {message}", flush=True),
        progress_label="materialize/normal_eval",
    )
    buggy_lance = _build_lance_from_rows(
        role_rows[BUGGY_EVAL_ROLE],
        normal_root=normal_root,
        test_root=test_root,
        output_path=output_dir / BUGGY_LANCE_NAME,
        progress=lambda message: print(f"[r5_xgame] {message}", flush=True),
        progress_label="materialize/buggy_eval",
    )
    window_rows, dataset_fingerprints = _build_window_manifest(
        normal_lance=normal_lance,
        buggy_lance=buggy_lance,
        eval_rows=[
            *role_rows[CALIBRATION_ROLE],
            *role_rows[NORMAL_EVAL_ROLE],
            *role_rows[BUGGY_EVAL_ROLE],
        ],
        output_path=output_dir / WINDOW_MANIFEST_NAME,
    )
    payload = {
        "status": "materialize_complete",
        "window_row_count": len(window_rows),
        "dataset_fingerprints": dataset_fingerprints,
        "files": {
            "r5_xgame_manifest.csv": _file_record(frozen_manifest),
            WINDOW_MANIFEST_NAME: _file_record(output_dir / WINDOW_MANIFEST_NAME),
            TRAIN_LANCE_NAME: _file_record(train_lance),
            NORMAL_LANCE_NAME: _file_record(normal_lance),
            BUGGY_LANCE_NAME: _file_record(buggy_lance),
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, "materialize", payload)


def run_baseline_score(*, output_dir: Path, batch_size: int) -> dict[str, Any]:
    materialize = _load_stage_marker(output_dir, "materialize")
    gate8 = _load_script_module("run_gate8_baselines_from_lance")
    metadata = gate8.run_gate8_baselines(
        manifest_path=Path(materialize["files"][WINDOW_MANIFEST_NAME]["path"]),
        train_lance=Path(materialize["files"][TRAIN_LANCE_NAME]["path"]),
        normal_lance=Path(materialize["files"][NORMAL_LANCE_NAME]["path"]),
        buggy_lance=Path(materialize["files"][BUGGY_LANCE_NAME]["path"]),
        output_dir=output_dir,
        batch_size=batch_size,
    )
    raw_path = output_dir / "baseline_scores.csv"
    score_path = output_dir / BASELINE_SCORE_NAME
    shutil.copyfile(raw_path, score_path)
    payload = {
        "status": "baseline_score_complete",
        "batch_size": batch_size,
        "baseline_metadata": metadata,
        "files": {BASELINE_SCORE_NAME: _file_record(score_path)},
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, "baseline_score", payload)


def run_train_lewm(
    *, output_dir: Path, seeds: Sequence[int], device: str, resume: bool
) -> dict[str, Any]:
    selected_seeds = _validate_seed_selection(seeds, allow_subset=False)
    materialize = _load_stage_marker(output_dir, "materialize")
    seed_outputs = []
    for seed in selected_seeds:
        seed_dir = output_dir / f"_lewm_seed{seed}"
        metadata = train_fresh_seed(
            Path(materialize["files"][TRAIN_LANCE_NAME]["path"]),
            Path(materialize["files"][NORMAL_LANCE_NAME]["path"]),
            seed_dir,
            seed=int(seed),
            device=device,
            resume=resume,
        )
        seed_outputs.append(
            {
                "seed": int(seed),
                "artifact_root": str(seed_dir),
                "training_metadata": metadata,
                "weights_path": str(seed_dir / "best_weights.pt"),
                "config_path": str(seed_dir / "config.json"),
                "checkpoint_sha256": sha256_file(seed_dir / "best_weights.pt"),
            }
        )
    payload = {
        "status": "train_lewm_complete",
        "device": device,
        "resume": resume,
        "seed_outputs": seed_outputs,
        "files": {
            f"seed{item['seed']}_artifact_root": _file_record(Path(item["artifact_root"]))
            for item in seed_outputs
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, "train_lewm", payload)


def run_lewm_score(
    *, output_dir: Path, seeds: Sequence[int], device: str, batch_size: int
) -> dict[str, Any]:
    selected_seeds = _validate_seed_selection(seeds, allow_subset=True)
    materialize = _load_stage_marker(output_dir, "materialize")
    _require_safe_flags(materialize, context="materialize")
    train_stage = _load_stage_marker(output_dir, "train_lewm")
    if train_stage.get("status") != "train_lewm_complete":
        raise ValueError("R5-XGame lewm_score requires stage_train_lewm.json with completion.")
    _require_safe_flags(train_stage, context="train_lewm")
    manifest_rows = read_csv_rows(Path(materialize["files"][WINDOW_MANIFEST_NAME]["path"]))
    normal_ids = [
        row["window_id"] for row in manifest_rows if row["dataset_name"] == NORMAL_DATASET_NAME
    ]
    buggy_ids = [
        row["window_id"] for row in manifest_rows if row["dataset_name"] == BUGGY_DATASET_NAME
    ]
    files: dict[str, dict[str, str]] = {}
    seed_infos = []
    for seed in SUPPORTED_SEEDS:
        seed_info = next(
            item for item in train_stage["seed_outputs"] if int(item["seed"]) == int(seed)
        )
        score_path = _seed_score_path(output_dir, seed)
        if seed not in selected_seeds:
            existing = validate_existing_lewm_score_file(output_dir, manifest_rows, seed=seed)
            print(
                f"[r5_xgame] reuse existing score seed={seed} rows={existing['row_count']} "
                f"path={existing['path']}",
                flush=True,
            )
            files[score_path.name] = _file_record(score_path)
            seed_infos.append(
                {
                    **seed_info,
                    "raw_score_path": str(score_path),
                    "raw_score_sha256": existing["sha256"],
                }
            )
            continue
        print(f"[r5_xgame] lewm_score seed={seed} load checkpoint", flush=True)
        adapter = LeWMAdapter(
            LeWMCheckpointSpec(
                weights_path=Path(seed_info["weights_path"]),
                config_path=Path(seed_info["config_path"]),
                action_mode=ActionMode.REAL,
                expected_sha256=str(seed_info["checkpoint_sha256"]),
                device=device,
            )
        ).load()
        print(
            f"[r5_xgame] lewm_score seed={seed} score dataset={NORMAL_DATASET_NAME} "
            f"windows={len(normal_ids)}",
            flush=True,
        )
        normal_rows = _score_dataset(
            Path(materialize["files"][NORMAL_LANCE_NAME]["path"]),
            normal_ids,
            adapter,
            batch_size=batch_size,
            device=device,
        )
        print(
            f"[r5_xgame] lewm_score seed={seed} score dataset={BUGGY_DATASET_NAME} "
            f"windows={len(buggy_ids)}",
            flush=True,
        )
        buggy_rows = _score_dataset(
            Path(materialize["files"][BUGGY_LANCE_NAME]["path"]),
            buggy_ids,
            adapter,
            batch_size=batch_size,
            device=device,
        )
        raw_rows = [*normal_rows, *buggy_rows]
        _assert_score_rows_complete(
            manifest_rows,
            raw_rows,
            context=f"lewm_score seed{seed}",
        )
        print(
            f"[r5_xgame] lewm_score seed={seed} validated rows={len(raw_rows)}",
            flush=True,
        )
        score_path = _write_csv_rows_atomic(score_path, raw_rows, LEWM_SCORE_FIELDS)
        files[score_path.name] = _file_record(score_path)
        seed_infos.append(
            {
                **seed_info,
                "raw_score_path": str(score_path),
                "raw_score_sha256": sha256_file(score_path),
            }
        )
        print(
            f"[r5_xgame] lewm_score seed={seed} wrote {score_path.name}",
            flush=True,
        )
    payload = {
        "status": "lewm_score_complete",
        "device": device,
        "batch_size": batch_size,
        "seed_outputs": seed_infos,
        "files": files,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return _write_stage_marker(output_dir, "lewm_score", payload)


def _score_rows_for_lewm(raw_rows: Sequence[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {name: [] for name in LEWM_WINDOW_SCORERS}
    for row in raw_rows:
        for scorer, value in _lewm_window_scores(row).items():
            result[scorer].append({"window_id": row["window_id"], "score": f"{value:.12g}"})
    return result


def run_aggregate_episode(*, output_dir: Path, seeds: Sequence[int]) -> dict[str, Any]:
    selected_seeds = _validate_seed_selection(seeds, allow_subset=False)
    manifest_rows = read_csv_rows(output_dir / WINDOW_MANIFEST_NAME)
    baseline_rows = read_csv_rows(output_dir / BASELINE_SCORE_NAME)
    per_method_rows: list[dict[str, str]] = []
    for seed in selected_seeds:
        score_info = validate_existing_lewm_score_file(output_dir, manifest_rows, seed=seed)
        raw_rows = read_csv_rows(Path(score_info["path"]))
        for window_scorer, aligned_rows in _score_rows_for_lewm(raw_rows).items():
            for aggregation in EPISODE_AGGREGATIONS:
                per_method_rows.extend(
                    aggregate_episode_scores(
                        manifest_rows,
                        aligned_rows,
                        window_scorer=window_scorer,
                        episode_aggregation=aggregation,
                        method_family="lewm",
                        method="lewm",
                        seed=int(seed),
                    )
                )
    for baseline_name in BASELINE_WINDOW_SCORERS:
        aligned_rows = [
            {"window_id": row["window_id"], "score": row[baseline_name]} for row in baseline_rows
        ]
        for aggregation in EPISODE_AGGREGATIONS:
            per_method_rows.extend(
                aggregate_episode_scores(
                    manifest_rows,
                    aligned_rows,
                    window_scorer=baseline_name,
                    episode_aggregation=aggregation,
                    method_family="baseline",
                    method=baseline_name,
                    seed=None,
                )
            )
    path = write_csv_rows(output_dir / EPISODE_SCORE_NAME, per_method_rows, EPISODE_SCORE_FIELDS)
    return _write_stage_marker(
        output_dir,
        "aggregate_episode",
        {
            "status": "aggregate_episode_complete",
            "episode_score_rows": len(per_method_rows),
            "files": {EPISODE_SCORE_NAME: _file_record(path)},
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )


def _group_episode_rows(
    rows: Sequence[dict[str, str]],
) -> dict[tuple[str, str, str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row["method_family"],
            row["method"],
            row["window_scorer"],
            row["seed"],
            row["episode_aggregation"],
        )
        grouped.setdefault(key, []).append(row)
    return grouped


def _percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def run_calibrate_thresholds(*, output_dir: Path) -> dict[str, Any]:
    rows = read_csv_rows(output_dir / EPISODE_SCORE_NAME)
    thresholds = []
    for key, group in _group_episode_rows(rows).items():
        calibration_rows = [row for row in group if row["evaluation_role"] == "calibration_normal"]
        if not calibration_rows:
            raise ValueError(f"Missing calibration rows for R5-XGame configuration: {key}")
        threshold = _percentile([float(row["score"]) for row in calibration_rows], 0.95)
        thresholds.append(
            {
                "method_family": key[0],
                "method": key[1],
                "window_scorer": key[2],
                "seed": key[3],
                "episode_aggregation": key[4],
                "threshold": threshold,
                "threshold_source": "calibration_normal_p95",
                "calibration_episode_ids": sorted(
                    row["source_episode_id"] for row in calibration_rows
                ),
            }
        )
    path = _write_json(output_dir / "r5_xgame_thresholds.json", {"thresholds": thresholds})
    return _write_stage_marker(
        output_dir,
        "calibrate_thresholds",
        {
            "status": "calibrate_thresholds_complete",
            "threshold_count": len(thresholds),
            "files": {"r5_xgame_thresholds.json": _file_record(path)},
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )


def _threshold_lookup(output_dir: Path) -> dict[tuple[str, str, str, str, str], dict[str, Any]]:
    payload = json.loads((output_dir / "r5_xgame_thresholds.json").read_text(encoding="utf-8"))
    return {
        (
            row["method_family"],
            row["method"],
            row["window_scorer"],
            row["seed"],
            row["episode_aggregation"],
        ): row
        for row in payload["thresholds"]
    }


def run_evaluate_binary(*, output_dir: Path) -> dict[str, Any]:
    episode_rows = read_csv_rows(output_dir / EPISODE_SCORE_NAME)
    thresholds = _threshold_lookup(output_dir)
    comparison_rows: list[dict[str, str]] = []
    for key, group in _group_episode_rows(episode_rows).items():
        threshold = float(thresholds[key]["threshold"])
        evaluation_rows = [row for row in group if row["evaluation_role"] == "evaluation"]
        labels = [1 if row["label"].lower() == "buggy" else 0 for row in evaluation_rows]
        scores = [float(row["score"]) for row in evaluation_rows]
        metrics = evaluate_r5_xgame_binary_scores(labels, scores, threshold=threshold)
        raw_score_path = (
            output_dir / BASELINE_SCORE_NAME
            if key[0] == "baseline"
            else output_dir / f"r5_xgame_lewm_scores_seed{key[3]}.csv"
        )
        comparison_rows.append(
            {
                "method_family": key[0],
                "method": key[1],
                "window_scorer": key[2],
                "seed": key[3],
                "episode_aggregation": key[4],
                "raw_score_path": str(raw_score_path),
                "raw_score_sha256": sha256_file(raw_score_path),
                "checkpoint_sha256": ""
                if key[0] == "baseline"
                else sha256_file(output_dir / f"_lewm_seed{key[3]}" / "best_weights.pt"),
                "threshold": _float_text(threshold),
                "threshold_source": thresholds[key]["threshold_source"],
                "auroc": _float_text(metrics["auroc"]),
                "auprc": _float_text(metrics["auprc"]),
                "f1": _float_text(metrics["f1"]),
                "precision": _float_text(metrics["precision"]),
                "recall": _float_text(metrics["recall"]),
                "fpr_at_95_tpr": _float_text(metrics["fpr_at_95_tpr"]),
                "balanced_accuracy": _float_text(metrics["balanced_accuracy"]),
                "evaluation_episode_count": str(len(evaluation_rows)),
                "positive_episode_count": str(sum(labels)),
                "negative_episode_count": str(len(labels) - sum(labels)),
                "calibration_episode_ids": ",".join(thresholds[key]["calibration_episode_ids"]),
                "auroc_ci_lower": "",
                "auroc_ci_upper": "",
                "f1_ci_lower": "",
                "f1_ci_upper": "",
            }
        )
    path = write_csv_rows(output_dir / COMPARISON_NAME, comparison_rows, XGAME_COMPARISON_FIELDS)
    summary = max(comparison_rows, key=lambda row: float(row["auroc"]))
    metrics_path = _write_json(
        output_dir / METRICS_NAME,
        {
            "status": "r5_xgame_binary_evaluated_unvalidated_ci",
            "summary_row": summary,
            "results": comparison_rows,
            **{
                field: float(summary[field])
                for field in (
                    "auroc",
                    "auprc",
                    "f1",
                    "precision",
                    "recall",
                    "fpr_at_95_tpr",
                    "balanced_accuracy",
                )
            },
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )
    return _write_stage_marker(
        output_dir,
        "evaluate_binary",
        {
            "status": "evaluate_binary_complete",
            "comparison_rows": len(comparison_rows),
            "files": {
                COMPARISON_NAME: _file_record(path),
                METRICS_NAME: _file_record(metrics_path),
            },
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )


def run_bootstrap_ci(*, output_dir: Path, bootstrap_seed: int, n_bootstrap: int) -> dict[str, Any]:
    episode_rows = read_csv_rows(output_dir / EPISODE_SCORE_NAME)
    thresholds = _threshold_lookup(output_dir)
    updated_rows: list[dict[str, str]] = []
    for row in read_csv_rows(output_dir / COMPARISON_NAME):
        key = (
            row["method_family"],
            row["method"],
            row["window_scorer"],
            row["seed"],
            row["episode_aggregation"],
        )
        group = _group_episode_rows(episode_rows)[key]
        eval_rows = [
            {
                "source_episode_id": item["source_episode_id"],
                "label": 1 if item["label"].lower() == "buggy" else 0,
                "score": float(item["score"]),
            }
            for item in group
            if item["evaluation_role"] == "evaluation"
        ]
        threshold = float(thresholds[key]["threshold"])
        auroc_ci = bootstrap_metric_ci(
            eval_rows,
            "auroc",
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
            group_key="source_episode_id",
        )
        f1_ci = bootstrap_metric_ci(
            eval_rows,
            "f1",
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
            group_key="source_episode_id",
            threshold=threshold,
        )
        row["auroc_ci_lower"] = _float_text(auroc_ci["lower"])
        row["auroc_ci_upper"] = _float_text(auroc_ci["upper"])
        row["f1_ci_lower"] = _float_text(f1_ci["lower"])
        row["f1_ci_upper"] = _float_text(f1_ci["upper"])
        updated_rows.append(row)
    comparison_path = write_csv_rows(
        output_dir / COMPARISON_NAME, updated_rows, XGAME_COMPARISON_FIELDS
    )
    summary = max(updated_rows, key=lambda item: float(item["auroc"]))
    metrics_path = _write_json(
        output_dir / METRICS_NAME,
        {
            "status": "r5_xgame_complete",
            "summary_row": summary,
            "results": updated_rows,
            "bootstrap": {
                "seed": bootstrap_seed,
                "n_bootstrap": n_bootstrap,
                "group_key": "source_episode_id",
            },
            **{
                field: float(summary[field])
                for field in (
                    "auroc",
                    "auprc",
                    "f1",
                    "precision",
                    "recall",
                    "fpr_at_95_tpr",
                    "balanced_accuracy",
                )
            },
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )
    return _write_stage_marker(
        output_dir,
        "bootstrap_ci",
        {
            "status": "bootstrap_ci_complete",
            "bootstrap_seed": bootstrap_seed,
            "n_bootstrap": n_bootstrap,
            "files": {
                COMPARISON_NAME: _file_record(comparison_path),
                METRICS_NAME: _file_record(metrics_path),
            },
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )


def _report_text(output_dir: Path) -> str:
    metrics = json.loads((output_dir / METRICS_NAME).read_text(encoding="utf-8"))
    summary = metrics["summary_row"]
    return (
        "# R5-XGame Non-Locked Four-Role Evaluation\n\n"
        f"- Manifest SHA256: `{sha256_file(output_dir / 'r5_xgame_manifest.csv')}`\n"
        f"- Window manifest SHA256: `{sha256_file(output_dir / WINDOW_MANIFEST_NAME)}`\n"
        "- Train rows: 36 normal episodes only.\n"
        "- Threshold rows: 12 calibration-normal episodes only.\n"
        "- Evaluation rows: 12 held-out normal-negative and 60 buggy-positive episodes.\n"
        "- Locked/test rows: unmaterialized and unscored.\n\n"
        f"Highest observed AUROC row in this non-locked validation run: `{summary['method']}` "
        f"seed `{summary['seed'] or 'n/a'}` / `{summary['window_scorer']}` / "
        f"`{summary['episode_aggregation']}`.\n\n"
        "Claim boundary: this is a validation-only R5-XGame run. Do not claim superiority, "
        "state of the art, cross-game generalization, action-conditioning benefit, or locked-test performance.\n"
    )


def run_package(*, manifest: Path, output_dir: Path) -> dict[str, Any]:
    if not (output_dir / REPORT_NAME).is_file():
        (output_dir / REPORT_NAME).write_text(_report_text(output_dir), encoding="utf-8")
    provenance = {
        "status": "r5_xgame_complete",
        "git_commit": runtime_provenance(include_lewm=False)["git_sha"],
        "environment": runtime_provenance(include_lewm=False),
        "manifest_sha256": sha256_file(manifest),
        "role_counts": EXPECTED_ROLE_COUNTS,
        "seeds": list(SUPPORTED_SEEDS),
        "train_role_sha256": _role_hash(_normalize_rows(_read_manifest(manifest)), {TRAIN_ROLE}),
        "calibration_role_sha256": _role_hash(
            _normalize_rows(_read_manifest(manifest)), {CALIBRATION_ROLE}
        ),
        "evaluation_role_sha256": _role_hash(
            _normalize_rows(_read_manifest(manifest)), {NORMAL_EVAL_ROLE, BUGGY_EVAL_ROLE}
        ),
        "outputs": {
            name: sha256_file(output_dir / name)
            for name in PACKAGE_OUTPUT_NAMES
            if (output_dir / name).is_file()
        },
        "old_r5_wob_checkpoint_reused": False,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    provenance_path = _write_json(output_dir / PROVENANCE_NAME, provenance)
    tarball = output_dir / TARBALL_NAME
    sha_path = output_dir / f"{TARBALL_NAME}.sha256"
    if tarball.exists():
        tarball.unlink()
    if sha_path.exists():
        sha_path.unlink()
    package_inputs = _package_contract_paths(output_dir)
    with tempfile.TemporaryDirectory(prefix="r5_xgame_package_") as tmp:
        snapshot_path = Path(tmp) / "stage_package.json"
        _write_package_stage_snapshot(snapshot_path, provenance_path=provenance_path)
        with tarfile.open(tarball, "w:gz") as archive:
            for path in package_inputs:
                archive.add(path, arcname=path.name)
            archive.add(snapshot_path, arcname=snapshot_path.name)
    sha_path.write_text(f"{sha256_file(tarball)}  {tarball.name}\n", encoding="utf-8")
    return _write_stage_marker(
        output_dir, "package", _package_stage_payload(provenance_path=provenance_path)
    )


def run_validate_package(*, output_dir: Path, frozen_manifest: Path) -> dict[str, Any]:
    validator = _load_script_module("validate_r5_xgame_output_bundle")
    result = validator.validate_output_dir(output_dir, frozen_manifest)
    tarball_result = validator.validate_tarball(
        output_dir / TARBALL_NAME,
        output_dir / f"{TARBALL_NAME}.sha256",
        frozen_manifest,
    )
    return _write_stage_marker(
        output_dir,
        "validate_package",
        {
            "status": "validate_package_complete",
            "validator_result": result,
            "tarball_validator_result": tarball_result,
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )


def run_stage(args: argparse.Namespace, stage: str) -> dict[str, Any]:
    if stage == "preflight":
        return preflight(args.manifest, args.input_root, args.output_dir, args.seeds)
    if stage == "materialize":
        return run_materialize(manifest=args.manifest, output_dir=args.output_dir)
    if stage == "baseline_score":
        return run_baseline_score(output_dir=args.output_dir, batch_size=args.baseline_batch_size)
    if stage == "train_lewm":
        return run_train_lewm(
            output_dir=args.output_dir, seeds=args.seeds, device=args.device, resume=args.resume
        )
    if stage == "lewm_score":
        return run_lewm_score(
            output_dir=args.output_dir,
            seeds=args.seeds,
            device=args.device,
            batch_size=args.lewm_batch_size,
        )
    if stage == "aggregate_episode":
        return run_aggregate_episode(output_dir=args.output_dir, seeds=args.seeds)
    if stage == "calibrate_thresholds":
        return run_calibrate_thresholds(output_dir=args.output_dir)
    if stage == "evaluate_binary":
        return run_evaluate_binary(output_dir=args.output_dir)
    if stage == "bootstrap_ci":
        return run_bootstrap_ci(
            output_dir=args.output_dir,
            bootstrap_seed=args.bootstrap_seed,
            n_bootstrap=args.n_bootstrap,
        )
    if stage == "package":
        return run_package(manifest=args.manifest, output_dir=args.output_dir)
    if stage == "validate_package":
        return run_validate_package(output_dir=args.output_dir, frozen_manifest=args.manifest)
    raise ValueError(f"Unsupported R5-XGame stage: {stage}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe R5-XGame stage.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/r5_xgame"))
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--stage", choices=(*STAGES, "all"), default="preflight")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--baseline-batch-size", type=int, default=4)
    parser.add_argument("--lewm-batch-size", type=int, default=2)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--package", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke:
        raise ValueError(
            "R5-XGame smoke mode is not supported because one-class shortcuts are unsafe."
        )
    allow_subset = args.stage == "lewm_score"
    _validate_seed_selection(args.seeds, allow_subset=allow_subset)
    if args.dry_run:
        receipt = preflight(args.manifest, args.input_root, args.output_dir, args.seeds)
        ready = receipt["status"] == "preflight_complete"
        print(
            json.dumps(
                {**receipt, "SAFE_TO_RUN_KAGGLE": ready, "planned_outputs": PLANNED_OUTPUTS},
                indent=2,
            )
        )
        return 0
    stages = STAGES if args.stage == "all" else (args.stage,)
    result: dict[str, Any] = {}
    for stage in stages:
        result = run_stage(args, stage)
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
