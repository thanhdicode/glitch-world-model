from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .manifest import ClipRecord
from .splits import GroupedSplitRecord, validate_no_group_leakage


@dataclass(frozen=True)
class NeuralPartitions:
    train_normal: list[ClipRecord]
    validation: list[ClipRecord]
    test: list[ClipRecord]
    audit: dict[str, object]


def rebase_clip_records(records: list[ClipRecord], clips_root: Path) -> list[ClipRecord]:
    return [
        ClipRecord(
            clip_id=record.clip_id,
            source=record.source,
            clip_dir=str(clips_root / record.source / "clips" / record.clip_id),
            start_frame=record.start_frame,
            end_frame=record.end_frame,
            frame_count=record.frame_count,
            fps=record.fps,
        )
        for record in records
    ]


def prepare_neural_partitions(
    records: list[ClipRecord],
    split_records: list[GroupedSplitRecord],
) -> NeuralPartitions:
    audit = validate_no_group_leakage(split_records)
    if audit["cross_split_group_count"]:
        raise ValueError("Neural protocol rejects cross split pair groups.")

    train_normal_sources = {
        row.source for row in split_records if row.split == "train" and row.label == "Normal"
    }
    validation_sources = {row.source for row in split_records if row.split == "validation"}
    test_sources = {row.source for row in split_records if row.split == "test"}
    train_normal = [record for record in records if record.source in train_normal_sources]
    if not train_normal:
        raise ValueError("Neural protocol requires at least one train-normal clip.")

    return NeuralPartitions(
        train_normal=train_normal,
        validation=[record for record in records if record.source in validation_sources],
        test=[record for record in records if record.source in test_sources],
        audit=audit,
    )
