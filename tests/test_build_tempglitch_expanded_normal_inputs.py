from __future__ import annotations

import csv
from pathlib import Path

import pytest

import scripts.build_tempglitch_expanded_normal_inputs as mod


def _write_metadata(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "category", "public_label"])
        writer.writeheader()
        writer.writerows(rows)


def _paired_rows(categories: list[str], limit_per_group: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for category in categories:
        for index in range(limit_per_group):
            pair_id = f"{category}/pair-{index:03d}"
            rows.append(
                {
                    "source": f"{category}_Normal_{index}",
                    "episode_id": f"{category}_Normal_{index}",
                    "pair_id": pair_id,
                    "category": category,
                    "label": "Normal",
                }
            )
            rows.append(
                {
                    "source": f"{category}_Buggy_{index}",
                    "episode_id": f"{category}_Buggy_{index}",
                    "pair_id": pair_id,
                    "category": category,
                    "label": "Buggy",
                }
            )
    return rows


def test_build_split_rows_parses_metadata(tmp_path: Path):
    meta = tmp_path / "metadata.csv"
    _write_metadata(
        meta,
        [
            {"source": "Blinking_Normal_1", "category": "Blinking", "public_label": "Normal"},
            {"source": "Blinking_Buggy_1", "category": "Blinking", "public_label": "Buggy"},
        ],
    )
    rows = mod._build_split_rows(meta)
    assert len(rows) == 2
    for row in rows:
        assert set(row) == {"source", "episode_id", "pair_id", "category", "label"}
        assert row["pair_id"].startswith(row["category"] + "/")
    labels = {row["label"] for row in rows}
    assert labels == {"Normal", "Buggy"}


def test_build_split_rows_rejects_empty(tmp_path: Path):
    meta = tmp_path / "empty.csv"
    _write_metadata(meta, [])
    try:
        mod._build_split_rows(meta)
    except ValueError as exc:
        assert "No TempGlitch metadata rows" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for empty metadata.")


def test_split_support_counts_show_limit_8_is_not_expanded_enough():
    records = mod.freeze_tempglitch_split(
        _paired_rows(["Blinking", "Frozen", "Shooting", "Teleportation", "Physics"], 8),
        exposed_groups=set(),
        seed=42,
    )
    support = mod._split_support_counts(records)
    assert support["validation_normal_episode_count"] == 10
    assert support["validation_buggy_episode_count"] == 10


def test_split_support_counts_reaches_target_at_limit_30():
    records = mod.freeze_tempglitch_split(
        _paired_rows(["Blinking", "Frozen", "Shooting", "Teleportation", "Physics"], 30),
        exposed_groups=set(),
        seed=42,
    )
    support = mod._split_support_counts(records)
    assert support["validation_normal_episode_count"] == 30
    assert support["validation_buggy_episode_count"] == 30


def test_build_parser_defaults():
    parser = mod.build_parser()
    args = parser.parse_args(["--output-dir", "/tmp/x"])
    assert args.limit_per_group == 35
    assert args.target_validation_normal_count == 34
    assert args.target_validation_buggy_count == 34
    assert args.target_evaluation_normal_count == 30
    assert args.minimum_calibration_normal_count == 1
    assert not args.allow_under_target_support
    assert args.image_size == 112
    assert args.frame_stride == 1


def test_raise_if_under_target_support_blocks_weak_expanded_split():
    support = {
        "validation_normal_episode_count": 10,
        "validation_buggy_episode_count": 10,
    }
    with pytest.raises(ValueError, match="below K-A target support"):
        mod._raise_if_under_target_support(
            support,
            target_validation_normal_count=30,
            target_validation_buggy_count=30,
            target_evaluation_normal_count=30,
            minimum_calibration_normal_count=1,
            allow_under_target_support=False,
        )


def test_support_guard_allows_kaggle_v2_adaptive_calibration_case():
    support = {
        "validation_normal_episode_count": 31,
        "validation_buggy_episode_count": 38,
    }
    mod._raise_if_under_target_support(
        support,
        target_validation_normal_count=34,
        target_validation_buggy_count=34,
        target_evaluation_normal_count=30,
        minimum_calibration_normal_count=1,
        allow_under_target_support=False,
    )
    assert (
        mod._recommended_calibration_normal_count(
            support,
            target_evaluation_normal_count=30,
        )
        == 1
    )


def test_limit_per_group_validation(tmp_path: Path):
    try:
        mod.build_expanded_inputs(output_dir=tmp_path, limit_per_group=0)
    except ValueError as exc:
        assert "limit_per_group" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for limit_per_group < 1.")
