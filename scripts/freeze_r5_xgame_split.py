"""Freeze a deterministic, non-locked R5-XGame manifest from the WOB source split."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from glitch_detection.r5_xgame_protocol import validate_r5_xgame_manifest


def build_r5_xgame_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Reserve held-out normal episodes and all existing non-locked buggy probes."""
    normal_train = sorted(
        (row for row in source_rows if row["label"] == "Normal" and row["split"] == "train"),
        key=lambda row: row["episode_id"],
    )
    normal_calibration = sorted(
        (row for row in source_rows if row["label"] == "Normal" and row["split"] == "validation"),
        key=lambda row: row["episode_id"],
    )
    buggy_evaluation = sorted(
        (row for row in source_rows if row["label"] == "Buggy" and row["split"] == "validation"),
        key=lambda row: (row["category"], row["episode_id"]),
    )
    if len(normal_train) != 48 or len(normal_calibration) != 12 or not buggy_evaluation:
        raise ValueError("Unexpected WOB source split counts; refusing to freeze R5-XGame.")

    selected: list[tuple[dict[str, str], str, str]] = []
    selected.extend((row, "train", "train_normal") for row in normal_train[:36])
    selected.extend((row, "validation", "evaluation_normal_negative") for row in normal_train[36:])
    selected.extend((row, "validation", "calibration_normal") for row in normal_calibration)
    selected.extend((row, "validation", "evaluation_buggy_positive") for row in buggy_evaluation)
    rows = [
        {
            "dataset_id": row["dataset_id"],
            "source": row["source"],
            "episode_id": row["episode_id"],
            "pair_id": row["pair_id"],
            "label": row["label"],
            "split": split,
            "evaluation_role": role,
        }
        for row, split, role in selected
    ]
    validate_r5_xgame_manifest(rows)
    return rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze the non-locked R5-XGame WOB manifest.")
    parser.add_argument("--source-split", type=Path, default=Path("configs/wob_protocol/split.csv"))
    parser.add_argument(
        "--output", type=Path, default=Path("configs/wob_protocol/r5_xgame_split.csv")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with args.source_split.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = build_r5_xgame_rows(list(csv.DictReader(handle)))
    write_rows(args.output, rows)
    print(f"Frozen {len(rows)} R5-XGame rows at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
