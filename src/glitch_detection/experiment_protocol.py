from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .calibration import calibrate_threshold, evaluate_with_fixed_threshold
from .manifest import ClipRecord, read_manifest
from .repeated_eval import (
    FittedScorer,
    clip_score_rows,
    fit_scorer_for_split,
    score_fitted_scorer,
    train_normal_records,
    write_clip_scores_csv,
)
from .splits import GroupedSplitRecord, read_grouped_split_csv, validate_no_group_leakage


@dataclass(frozen=True)
class ProtocolPartitions:
    manifest_records: list[ClipRecord]
    split_records: list[GroupedSplitRecord]
    train_normal: list[ClipRecord]
    validation: list[ClipRecord]
    test: list[ClipRecord]
    audit: dict[str, Any]
    test_materialized: bool


@dataclass(frozen=True)
class ValidationProtocolResult:
    partitions: ProtocolPartitions
    fitted_scorer: FittedScorer
    calibration_path: Path
    metadata_path: Path


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _config_hash(scorer: str, scorer_config: dict[str, Any]) -> str:
    payload = json.dumps(
        {"scorer": scorer, "config": scorer_config},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def prepare_protocol_partitions(
    manifest_path: Path,
    split_path: Path,
    *,
    allow_test_materialization: bool = False,
) -> ProtocolPartitions:
    manifest_records = read_manifest(manifest_path)
    split_records = read_grouped_split_csv(split_path)
    audit = validate_no_group_leakage(split_records)
    if audit["cross_split_group_count"]:
        raise ValueError("Experiment protocol rejects cross-split groups.")

    source_sets = {
        split: {row.source for row in split_records if row.split == split}
        for split in ["validation", "test"]
    }
    train_normal = train_normal_records(manifest_records, split_records)
    if not train_normal:
        raise ValueError("Experiment protocol requires at least one train-normal clip.")

    return ProtocolPartitions(
        manifest_records=manifest_records,
        split_records=split_records,
        train_normal=train_normal,
        validation=[
            record for record in manifest_records if record.source in source_sets["validation"]
        ],
        test=(
            [record for record in manifest_records if record.source in source_sets["test"]]
            if allow_test_materialization
            else []
        ),
        audit=audit,
        test_materialized=allow_test_materialization,
    )


def run_validation_protocol(
    partitions: ProtocolPartitions,
    labels_path: Path,
    output_root: Path,
    scorer: str,
    *,
    dataset_id: str,
    dataset_revision: str,
    sample_mode: str,
    seed: int,
    command: str,
    scorer_config: dict[str, Any] | None = None,
) -> ValidationProtocolResult:
    scorer_config = scorer_config or {}
    fitted = fit_scorer_for_split(
        scorer,
        partitions.manifest_records,
        partitions.split_records,
    )
    validation_scores_path = write_clip_scores_csv(
        clip_score_rows(
            partitions.validation,
            score_fitted_scorer(fitted, partitions.validation),
        ),
        output_root / "validation_scores.csv",
    )
    calibration_path = output_root / "validation_calibration.json"
    calibrate_threshold(validation_scores_path, labels_path, calibration_path)

    split_counts = {
        split: sum(row.split == split for row in partitions.split_records)
        for split in ["train", "validation", "test"]
    }
    metadata = {
        "dataset_id": dataset_id,
        "dataset_revision": dataset_revision,
        "sample_mode": sample_mode,
        "seed": seed,
        "split_counts": split_counts,
        "group_leakage_count": partitions.audit["cross_split_group_count"],
        "train_normal_clip_count": len(partitions.train_normal),
        "train_normal_source_count": len({row.source for row in partitions.train_normal}),
        "validation_clip_count": len(partitions.validation),
        "validation_source_count": len({row.source for row in partitions.validation}),
        "test_materialized": partitions.test_materialized,
        "test_scored": False,
        "scorer": scorer,
        "scorer_config": scorer_config,
        "scorer_config_hash": _config_hash(scorer, scorer_config),
        "fit_metadata": fitted.fit_metadata,
        "command": command,
        "git_commit": _git_commit(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = _write_json(metadata, output_root / "protocol_metadata.json")
    return ValidationProtocolResult(partitions, fitted, calibration_path, metadata_path)


def score_test_with_release_gate(
    validation_result: ValidationProtocolResult,
    labels_path: Path,
    output_root: Path,
    *,
    release_approved: bool = False,
) -> dict[str, Any]:
    if not release_approved:
        raise PermissionError("Locked-test scoring requires explicit release approval.")
    if not validation_result.partitions.test_materialized:
        raise PermissionError("Locked-test records were not explicitly materialized.")

    test_scores_path = write_clip_scores_csv(
        clip_score_rows(
            validation_result.partitions.test,
            score_fitted_scorer(
                validation_result.fitted_scorer,
                validation_result.partitions.test,
            ),
        ),
        output_root / "test_scores.csv",
    )
    metrics = evaluate_with_fixed_threshold(
        test_scores_path,
        labels_path,
        validation_result.calibration_path,
        output_root / "test_metrics.json",
    )
    metadata = json.loads(validation_result.metadata_path.read_text(encoding="utf-8"))
    metadata["test_scored"] = True
    _write_json(metadata, validation_result.metadata_path)
    return metrics
