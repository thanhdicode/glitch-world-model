import json
from pathlib import Path

import pytest

from glitch_detection.manifest import ClipRecord, write_manifest
from glitch_detection.splits import GroupedSplitRecord, write_grouped_split_csv
from scripts.run_kaggle_video_autoencoder import run_kaggle_video_autoencoder


def _record(tmp_path: Path, source: str) -> ClipRecord:
    clip_id = f"{source}_000000"
    clip_dir = tmp_path / source / "clips" / clip_id
    clip_dir.mkdir(parents=True)
    return ClipRecord(clip_id, source, str(clip_dir), 0, 15, 16, 30.0)


def _split(source: str, label: str, split: str, pair_id: str) -> GroupedSplitRecord:
    return GroupedSplitRecord(source, "Blinking", label, split, pair_id)


def test_dry_run_writes_protocol_audit_without_checkpoint(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    split_path = tmp_path / "split.csv"
    output_root = tmp_path / "outputs"
    records = [
        _record(tmp_path, "train_normal"),
        _record(tmp_path, "train_buggy"),
        _record(tmp_path, "validation_buggy"),
        _record(tmp_path, "test_normal"),
    ]
    write_manifest(manifest_path, records)
    write_grouped_split_csv(
        split_path,
        [
            _split("train_normal", "Normal", "train", "Blinking/1"),
            _split("train_buggy", "Buggy", "train", "Blinking/2"),
            _split("validation_buggy", "Buggy", "validation", "Blinking/3"),
            _split("test_normal", "Normal", "test", "Blinking/4"),
        ],
        seed=42,
    )

    summary = run_kaggle_video_autoencoder(
        manifest_path=manifest_path,
        split_path=split_path,
        output_root=output_root,
        dry_run=True,
    )

    assert summary["status"] == "dry-run only"
    assert summary["train_normal_clip_count"] == 1
    assert summary["validation_clip_count"] == 1
    assert summary["test_clip_count"] == 1
    assert summary["test_materialized"] is False
    assert not (output_root / "video_autoencoder.pt").exists()
    assert not (output_root / "test_manifest.csv").exists()
    assert json.loads((output_root / "protocol_audit.json").read_text(encoding="utf-8")) == summary


def test_dry_run_rejects_cross_split_pair_groups(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    split_path = tmp_path / "split.csv"
    records = [_record(tmp_path, "train_normal"), _record(tmp_path, "test_buggy")]
    write_manifest(manifest_path, records)
    write_grouped_split_csv(
        split_path,
        [
            _split("train_normal", "Normal", "train", "Blinking/1"),
            _split("test_buggy", "Buggy", "test", "Blinking/1"),
        ],
        seed=42,
    )

    with pytest.raises(ValueError, match="cross split"):
        run_kaggle_video_autoencoder(
            manifest_path=manifest_path,
            split_path=split_path,
            output_root=tmp_path / "outputs",
            dry_run=True,
        )
