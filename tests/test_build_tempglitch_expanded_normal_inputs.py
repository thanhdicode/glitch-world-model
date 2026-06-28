from __future__ import annotations

import csv
from pathlib import Path

import scripts.build_tempglitch_expanded_normal_inputs as mod


def _write_metadata(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "category", "public_label"])
        writer.writeheader()
        writer.writerows(rows)


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


def test_build_parser_defaults():
    parser = mod.build_parser()
    args = parser.parse_args(["--output-dir", "/tmp/x"])
    assert args.limit_per_group == 8
    assert args.image_size == 112
    assert args.frame_stride == 1


def test_limit_per_group_validation(tmp_path: Path):
    try:
        mod.build_expanded_inputs(output_dir=tmp_path, limit_per_group=0)
    except ValueError as exc:
        assert "limit_per_group" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for limit_per_group < 1.")
