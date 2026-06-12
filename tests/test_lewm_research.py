import csv
from pathlib import Path

import pytest

from glitch_detection.lewm_research import (
    LeWMResearchProtocol,
    audit_local_research_source,
)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    video_root = tmp_path / "videos"
    video_root.mkdir()
    metadata_rows = []
    split_rows = []
    categories = [
        "Blinking",
        "Frozen Animation",
        "Shooting Error",
        "Stuck in Place",
        "Velocity Bug",
    ]
    specifications = [
        ("train", "Normal", 5),
        ("validation", "Normal", 5),
        ("validation", "Buggy", 5),
    ]
    index = 0
    for partition, label, count in specifications:
        for offset in range(count):
            source = f"{partition}-{label}-{offset}"
            path = video_root / f"{source}.mp4"
            path.write_bytes(b"video")
            metadata_rows.append({"source": source, "local_video_path": path.name})
            split_rows.append(
                {
                    "source": source,
                    "episode_id": source,
                    "pair_id": f"pair-{index}",
                    "category": categories[offset % len(categories)],
                    "label": label,
                    "split": partition,
                    "materialize": "True",
                }
            )
            index += 1
    metadata_path = tmp_path / "metadata.csv"
    split_path = tmp_path / "split.csv"
    _write_csv(metadata_path, metadata_rows)
    _write_csv(split_path, split_rows)
    return metadata_path, split_path, video_root


def test_research_audit_uses_all_local_nonlocked_rows(tmp_path: Path):
    metadata, split, video_root = _fixture(tmp_path)
    protocol = LeWMResearchProtocol(
        minimum_train_normal_episodes=5,
        minimum_validation_normal_episodes=5,
        minimum_validation_buggy_episodes=5,
    )

    result = audit_local_research_source(metadata, split, video_root, protocol)

    assert result["counts"] == {
        "train_normal": 5,
        "validation_normal": 5,
        "validation_buggy": 5,
    }
    assert result["primary_evaluation_unit"] == "episode"
    assert result["normal_only_training"] is True
    assert result["locked_test_scored"] is False


def test_research_audit_rejects_small_buggy_sample(tmp_path: Path):
    metadata, split, video_root = _fixture(tmp_path)
    protocol = LeWMResearchProtocol(
        minimum_train_normal_episodes=5,
        minimum_validation_normal_episodes=5,
        minimum_validation_buggy_episodes=6,
    )

    with pytest.raises(ValueError, match="Insufficient local research episodes"):
        audit_local_research_source(metadata, split, video_root, protocol)


def test_research_audit_rejects_pair_leakage(tmp_path: Path):
    metadata, split, video_root = _fixture(tmp_path)
    rows = list(csv.DictReader(split.open(encoding="utf-8")))
    rows[5]["pair_id"] = rows[0]["pair_id"]
    _write_csv(split, rows)
    protocol = LeWMResearchProtocol(
        minimum_train_normal_episodes=5,
        minimum_validation_normal_episodes=5,
        minimum_validation_buggy_episodes=5,
    )

    with pytest.raises(ValueError, match="leakage"):
        audit_local_research_source(metadata, split, video_root, protocol)
