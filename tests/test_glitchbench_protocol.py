from __future__ import annotations

import csv
from pathlib import Path

import pytest
from PIL import Image

from glitch_detection.glitchbench_protocol import (
    GlitchBenchProtocolError,
    validate_glitchbench_manifest,
    validate_glitchbench_split,
)
from glitch_detection.splits import GroupedSplitRecord, write_grouped_split_csv


def _png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 4), (255, 0, 0)).save(path)
    return path


def _write_protocol_manifest(path: Path, rows: list[dict[str, str]]) -> Path:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _rows(tmp_path: Path) -> list[dict[str, str]]:
    clip_root = tmp_path / "clips_root"
    normal_clip = clip_root / "normal_source" / "clips" / "normal_clip"
    buggy_clip = clip_root / "buggy_source" / "clips" / "buggy_clip"
    _png(normal_clip / "frame_000000.png")
    _png(buggy_clip / "frame_000000.png")
    normal_image = _png(tmp_path / "normal.png")
    buggy_image = _png(tmp_path / "buggy.png")
    return [
        {
            "source": "normal_source",
            "clip_id": "normal_clip",
            "clip_dir": str(normal_clip),
            "image_path": str(normal_image),
            "record_id": "record-1",
            "reddit_id": "reddit-1",
            "game": "Game A",
            "glitch_type": "Physics",
            "source_domain": "Social Media",
            "raw_label": "synthetic_normal",
            "mapped_label": "Normal",
            "group_key": "reddit-1",
            "synthetic_normal": "true",
            "temporal_label_available": "false",
        },
        {
            "source": "buggy_source",
            "clip_id": "buggy_clip",
            "clip_dir": str(buggy_clip),
            "image_path": str(buggy_image),
            "record_id": "record-1",
            "reddit_id": "reddit-1",
            "game": "Game A",
            "glitch_type": "Physics",
            "source_domain": "Social Media",
            "raw_label": "glitch",
            "mapped_label": "Buggy",
            "group_key": "reddit-1",
            "synthetic_normal": "false",
            "temporal_label_available": "false",
        },
    ]


def test_glitchbench_protocol_accepts_valid_manifest_and_split(tmp_path: Path):
    manifest_path = _write_protocol_manifest(tmp_path / "glitchbench_records.csv", _rows(tmp_path))
    split_path = tmp_path / "grouped_split.csv"
    write_grouped_split_csv(
        split_path,
        [
            GroupedSplitRecord("normal_source", "Physics", "Normal", "train", "reddit-1"),
            GroupedSplitRecord("buggy_source", "Physics", "Buggy", "validation", "reddit-1"),
            GroupedSplitRecord("normal_source", "Physics", "Normal", "validation", "reddit-1"),
        ],
        seed=42,
    )
    # overwrite with leakage-free split
    write_grouped_split_csv(
        split_path,
        [
            GroupedSplitRecord("normal_source", "Physics", "Normal", "validation", "reddit-1"),
            GroupedSplitRecord("buggy_source", "Physics", "Buggy", "validation", "reddit-1"),
        ],
        seed=42,
    )

    assert validate_glitchbench_manifest(manifest_path)["record_count"] == 2
    assert validate_glitchbench_split(manifest_path, split_path)["validation_source_count"] == 2


def test_glitchbench_protocol_rejects_missing_required_field(tmp_path: Path):
    rows = _rows(tmp_path)
    del rows[0]["group_key"]
    manifest_path = _write_protocol_manifest(tmp_path / "missing.csv", rows)

    with pytest.raises(GlitchBenchProtocolError, match="non-empty group_key"):
        validate_glitchbench_manifest(manifest_path)


def test_glitchbench_protocol_rejects_ambiguous_label_mapping(tmp_path: Path):
    rows = _rows(tmp_path)
    rows[1]["raw_label"] = "mystery"
    manifest_path = _write_protocol_manifest(tmp_path / "ambiguous.csv", rows)

    with pytest.raises(GlitchBenchProtocolError, match="ambiguous"):
        validate_glitchbench_manifest(manifest_path)


def test_glitchbench_protocol_rejects_split_leakage(tmp_path: Path):
    manifest_path = _write_protocol_manifest(tmp_path / "glitchbench_records.csv", _rows(tmp_path))
    split_path = tmp_path / "grouped_split.csv"
    write_grouped_split_csv(
        split_path,
        [
            GroupedSplitRecord("normal_source", "Physics", "Normal", "train", "reddit-1"),
            GroupedSplitRecord("buggy_source", "Physics", "Buggy", "validation", "reddit-1"),
        ],
        seed=42,
    )

    with pytest.raises(GlitchBenchProtocolError, match="cross-split leakage"):
        validate_glitchbench_split(manifest_path, split_path)
