from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

from glitch_detection.gate6_data import sha256_file
from glitch_detection.manifest import ClipRecord, read_manifest
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.splits import read_grouped_split_csv

BASELINE_NAMES = ("video_autoencoder", "cnn_lstm", "video_transformer")
ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_sha256_sidecar(path: Path) -> dict[str, str]:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.is_file():
        raise FileNotFoundError(f"Missing SHA256 sidecar: {sidecar}")
    text = sidecar.read_text(encoding="utf-8-sig").strip()
    digest, _, filename = text.partition("  ")
    if len(digest) != 64 or filename != path.name:
        raise ValueError(f"Invalid SHA256 sidecar format: {sidecar}")
    if digest != sha256_file(path):
        raise ValueError(f"SHA256 mismatch for {path}")
    return {"sha256": digest, "sha256_path": str(sidecar)}


def _clip_dir_signature(path_text: str, output_root: Path) -> tuple[str, ...]:
    resolved = _resolve_downloaded_kaggle_path(path_text, output_root)
    return PurePosixPath(str(resolved).replace("\\", "/")).parts[-3:]


def _resolve_downloaded_kaggle_path(path_text: str, output_root: Path) -> Path:
    candidate = Path(path_text)
    if candidate.exists():
        return candidate

    normalized = PurePosixPath(path_text.replace("\\", "/"))
    parts = [part for part in normalized.parts if part not in {"/", "\\"}]
    if "kaggle" not in parts or "input" not in parts or len(parts) < 2:
        return candidate

    dataset_name = parts[-2]
    dataset_indexes = [index for index, part in enumerate(parts[:-1]) if part == dataset_name]
    if not dataset_indexes:
        return candidate
    relative_tail = parts[dataset_indexes[-1] + 1 :]
    if not relative_tail:
        return candidate

    search_roots: list[Path] = []
    for parent in output_root.resolve().parents:
        search_roots.append(parent / "k1_tempglitch_kaggle_dataset" / dataset_name)
        search_roots.append(parent / dataset_name)
    search_roots.append(ROOT / "outputs" / "k1_tempglitch_kaggle_dataset" / dataset_name)

    seen: set[Path] = set()
    for root in search_roots:
        resolved_root = root.resolve()
        if resolved_root in seen:
            continue
        seen.add(resolved_root)
        local_candidate = resolved_root.joinpath(*relative_tail)
        if local_candidate.exists():
            return local_candidate
    return candidate


def _record_signature(record: ClipRecord) -> tuple[str, str, str, int, int, int, float]:
    return (
        record.clip_id,
        record.source,
        record.clip_dir,
        record.start_frame,
        record.end_frame,
        record.frame_count,
        record.fps,
    )


def _normalized_record_signature(
    record: ClipRecord, *, output_root: Path
) -> tuple[str, str, tuple[str, ...], int, int, int, float]:
    return (
        record.clip_id,
        record.source,
        _clip_dir_signature(record.clip_dir, output_root),
        record.start_frame,
        record.end_frame,
        record.frame_count,
        record.fps,
    )


def _validate_scores_alignment(
    manifest_records: list[ClipRecord], scores_path: Path, *, output_root: Path
) -> dict[str, Any]:
    with scores_path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(manifest_records):
        raise ValueError(f"Score row count mismatch for {scores_path}")
    expected_clip_ids = [record.clip_id for record in manifest_records]
    actual_clip_ids = [row["clip_id"] for row in rows]
    if actual_clip_ids != expected_clip_ids:
        raise ValueError(f"Score rows are not aligned with validation manifest for {scores_path}")
    for record, row in zip(manifest_records, rows):
        resolved_clip_dir = str(_resolve_downloaded_kaggle_path(row["clip_dir"], output_root))
        row_signature = _clip_dir_signature(row["clip_dir"], output_root)
        record_signature = _clip_dir_signature(record.clip_dir, output_root)
        if row["source"] != record.source or (
            resolved_clip_dir != record.clip_dir and row_signature != record_signature
        ):
            raise ValueError(f"Score row provenance mismatch for clip {record.clip_id}")
        if (
            int(row["start_frame"]) != record.start_frame
            or int(row["end_frame"]) != record.end_frame
        ):
            raise ValueError(f"Score row frame bounds mismatch for clip {record.clip_id}")
        if not math.isfinite(float(row["score"])):
            raise ValueError(f"Non-finite score for clip {record.clip_id}")
    return {"score_row_count": len(rows)}


def validate_learned_baselines(output_root: Path) -> dict[str, Any]:
    protocol_path = output_root / "protocol_audit.json"
    summary_path = output_root / "learned_baselines_summary.json"
    protocol = _read_json(protocol_path)
    summary = _read_json(summary_path)
    if protocol != summary:
        raise ValueError(
            "protocol_audit.json and learned_baselines_summary.json must match exactly."
        )
    for field in (
        "test_materialized",
        "test_scored",
        "locked_test_materialized",
        "locked_test_scored",
    ):
        if protocol.get(field) is not False:
            raise ValueError(f"{field} must be false.")
    if protocol["leakage_audit"]["cross_split_group_count"] != 0:
        raise ValueError("Learned baselines protocol must report zero cross-split leakage.")

    manifest_path = _resolve_downloaded_kaggle_path(protocol["manifest_path"], output_root)
    split_path = _resolve_downloaded_kaggle_path(protocol["split_path"], output_root)
    clips_root = (
        _resolve_downloaded_kaggle_path(protocol["clips_root"], output_root)
        if protocol.get("clips_root")
        else None
    )
    records = read_manifest(manifest_path)
    if clips_root is not None:
        records = rebase_clip_records(records, clips_root)
    partitions = prepare_neural_partitions(records, read_grouped_split_csv(split_path))
    train_manifest_records = read_manifest(output_root / "train_normal_manifest.csv")
    validation_manifest_records = read_manifest(output_root / "validation_manifest.csv")
    if [
        _normalized_record_signature(record, output_root=output_root)
        for record in train_manifest_records
    ] != [
        _normalized_record_signature(record, output_root=output_root)
        for record in partitions.train_normal
    ]:
        raise ValueError(
            "Persisted train_normal_manifest.csv does not match the grouped train-normal partition."
        )
    if [
        _normalized_record_signature(record, output_root=output_root)
        for record in validation_manifest_records
    ] != [
        _normalized_record_signature(record, output_root=output_root)
        for record in partitions.validation
    ]:
        raise ValueError(
            "Persisted validation_manifest.csv does not match the grouped validation partition."
        )

    baseline_validations: dict[str, Any] = {}
    for name in BASELINE_NAMES:
        checkpoint_path = output_root / f"{name}.pt"
        metadata_path = output_root / f"{name}_training_metadata.json"
        scores_path = output_root / f"{name}_validation_scores.csv"
        metadata = _read_json(metadata_path)
        if metadata.get("fit_split") != "train-normal":
            raise ValueError(f"{name} metadata must record fit_split=train-normal.")
        baseline_validations[name] = {
            "checkpoint": {"path": str(checkpoint_path), **_read_sha256_sidecar(checkpoint_path)},
            "training_metadata": {
                "path": str(metadata_path),
                **_read_sha256_sidecar(metadata_path),
            },
            "validation_scores": {
                "path": str(scores_path),
                **_read_sha256_sidecar(scores_path),
                **_validate_scores_alignment(
                    validation_manifest_records, scores_path, output_root=output_root
                ),
            },
        }

    receipt = {
        "status": "validated",
        "output_root": str(output_root),
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "train_normal_clip_count": len(train_manifest_records),
        "validation_clip_count": len(validation_manifest_records),
        "baseline_validations": baseline_validations,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    receipt_path = output_root / "learned_baselines_validation.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the learned baseline Kaggle artifact layout and protocol boundaries."
    )
    parser.add_argument("--output-root", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    receipt = validate_learned_baselines(args.output_root)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
