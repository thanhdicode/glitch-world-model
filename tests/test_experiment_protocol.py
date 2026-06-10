import json
from pathlib import Path

import pytest
from PIL import Image

from glitch_detection.experiment_protocol import (
    prepare_protocol_partitions,
    run_validation_protocol,
    score_test_with_release_gate,
)
from glitch_detection.manifest import ClipRecord, write_manifest
from glitch_detection.splits import GroupedSplitRecord, write_grouped_split_csv


def _fixture(tmp_path: Path, *, leaking: bool = False) -> tuple[Path, Path, Path]:
    records: list[ClipRecord] = []
    split_records: list[GroupedSplitRecord] = []
    labels_path = tmp_path / "labels.csv"
    label_lines = ["source,start_frame,end_frame,label"]
    rows = [
        ("train_normal", "Normal", "train", "pair-1", [10, 11, 12]),
        ("train_buggy", "Buggy", "train", "pair-2", [10, 100, 10]),
        ("validation_normal", "Normal", "validation", "pair-3", [12, 13, 14]),
        ("validation_buggy", "Buggy", "validation", "pair-4", [12, 120, 12]),
        ("test_normal", "Normal", "test", "pair-5", [13, 14, 15]),
        ("test_buggy", "Buggy", "test", "pair-6", [13, 130, 13]),
    ]
    for source, label, split, pair_id, values in rows:
        clip_dir = tmp_path / "clips" / source
        clip_dir.mkdir(parents=True)
        for index, value in enumerate(values):
            Image.new("RGB", (4, 4), color=(value, value, value)).save(
                clip_dir / f"{index:03d}.png"
            )
        records.append(ClipRecord(source, source, str(clip_dir), 0, 2, 3, 30.0))
        split_records.append(
            GroupedSplitRecord(
                source,
                "Blinking",
                label,
                split,
                "pair-1" if leaking and source == "test_buggy" else pair_id,
            )
        )
        if label == "Buggy":
            label_lines.append(f"{source},0,2,1")

    manifest_path = tmp_path / "manifest.csv"
    write_manifest(manifest_path, records)
    split_path, _ = write_grouped_split_csv(tmp_path / "split.csv", split_records, seed=42)
    labels_path.write_text("\n".join(label_lines) + "\n", encoding="utf-8")
    return manifest_path, split_path, labels_path


def test_protocol_defaults_to_validation_only_and_records_provenance(tmp_path: Path):
    manifest_path, split_path, labels_path = _fixture(tmp_path)
    partitions = prepare_protocol_partitions(manifest_path, split_path)

    result = run_validation_protocol(
        partitions,
        labels_path,
        tmp_path / "outputs",
        "frame_diff",
        dataset_id="fixture",
        dataset_revision="revision",
        sample_mode="synthetic",
        seed=42,
        command="pytest",
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert [row.source for row in partitions.train_normal] == ["train_normal"]
    assert {row.source for row in partitions.validation} == {
        "validation_normal",
        "validation_buggy",
    }
    assert partitions.test == []
    assert metadata["group_leakage_count"] == 0
    assert metadata["test_materialized"] is False
    assert metadata["test_scored"] is False
    assert metadata["fit_metadata"]["fit_split"] == "none"
    assert len(metadata["scorer_config_hash"]) == 64


def test_protocol_rejects_test_scoring_without_both_release_gates(tmp_path: Path):
    manifest_path, split_path, labels_path = _fixture(tmp_path)
    partitions = prepare_protocol_partitions(manifest_path, split_path)
    result = run_validation_protocol(
        partitions,
        labels_path,
        tmp_path / "outputs",
        "frame_diff",
        dataset_id="fixture",
        dataset_revision="revision",
        sample_mode="synthetic",
        seed=42,
        command="pytest",
    )

    with pytest.raises(PermissionError, match="explicit release approval"):
        score_test_with_release_gate(result, labels_path, tmp_path / "outputs")
    with pytest.raises(PermissionError, match="not explicitly materialized"):
        score_test_with_release_gate(
            result,
            labels_path,
            tmp_path / "outputs",
            release_approved=True,
        )


def test_protocol_rejects_cross_split_groups(tmp_path: Path):
    manifest_path, split_path, _ = _fixture(tmp_path, leaking=True)

    with pytest.raises(ValueError, match="cross-split"):
        prepare_protocol_partitions(manifest_path, split_path)
