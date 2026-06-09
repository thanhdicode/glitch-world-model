from pathlib import Path

import pytest

from glitch_detection.manifest import ClipRecord
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.splits import GroupedSplitRecord


def _record(source: str, clip_id: str) -> ClipRecord:
    return ClipRecord(
        clip_id=clip_id,
        source=source,
        clip_dir=f"C:/local/{source}/clips/{clip_id}",
        start_frame=0,
        end_frame=15,
        frame_count=16,
        fps=30.0,
    )


def _split(
    source: str,
    label: str,
    split: str,
    pair_id: str,
) -> GroupedSplitRecord:
    return GroupedSplitRecord(
        source=source,
        category="Blinking",
        label=label,
        split=split,
        pair_id_heuristic=pair_id,
    )


def test_rebase_clip_records_replaces_machine_specific_clip_dirs(tmp_path: Path):
    records = [_record("normal_1", "normal_1_000000")]

    rebased = rebase_clip_records(records, tmp_path / "clips")

    assert rebased[0].clip_dir == str(tmp_path / "clips" / "normal_1" / "clips" / "normal_1_000000")
    assert rebased[0].clip_id == records[0].clip_id


def test_prepare_neural_partitions_fits_only_train_normal_sources():
    records = [
        _record("train_normal", "train_normal_000000"),
        _record("train_buggy", "train_buggy_000000"),
        _record("validation_normal", "validation_normal_000000"),
        _record("test_normal", "test_normal_000000"),
    ]
    splits = [
        _split("train_normal", "Normal", "train", "Blinking/1"),
        _split("train_buggy", "Buggy", "train", "Blinking/2"),
        _split("validation_normal", "Normal", "validation", "Blinking/3"),
        _split("test_normal", "Normal", "test", "Blinking/4"),
    ]

    partitions = prepare_neural_partitions(records, splits)

    assert [row.source for row in partitions.train_normal] == ["train_normal"]
    assert [row.source for row in partitions.validation] == ["validation_normal"]
    assert [row.source for row in partitions.test] == ["test_normal"]
    assert partitions.audit["cross_split_group_count"] == 0


def test_prepare_neural_partitions_rejects_cross_split_pair_groups():
    records = [
        _record("train_normal", "train_normal_000000"),
        _record("test_buggy", "test_buggy_000000"),
    ]
    splits = [
        _split("train_normal", "Normal", "train", "Blinking/1"),
        _split("test_buggy", "Buggy", "test", "Blinking/1"),
    ]

    with pytest.raises(ValueError, match="cross split"):
        prepare_neural_partitions(records, splits)
