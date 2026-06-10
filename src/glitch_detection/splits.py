from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import read_labels, read_manifest, write_manifest
from .pairs import infer_tempglitch_pair_id, pair_leakage_report

SPLIT_FIELDS = ["source", "category", "label", "split"]
GROUPED_SPLIT_FIELDS = [*SPLIT_FIELDS, "pair_id_heuristic"]


@dataclass(frozen=True)
class SplitRecord:
    source: str
    category: str
    label: str
    split: str


@dataclass(frozen=True)
class GroupedSplitRecord:
    source: str
    category: str
    label: str
    split: str
    pair_id_heuristic: str


def _split_counts_for_group(
    group_size: int,
    train_count: int | None,
    validation_count: int | None,
    test_count: int | None,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> dict[str, int]:
    if group_size < 2:
        raise ValueError("Need at least 2 videos per category/label group to split.")

    if train_count is not None or validation_count is not None or test_count is not None:
        if train_count is None or validation_count is None or test_count is None:
            raise ValueError(
                "Explicit split counts require train_count, validation_count, and test_count."
            )
        requested = train_count + validation_count + test_count
        if requested > group_size:
            raise ValueError(
                f"Requested split requires {requested} videos but group has {group_size}."
            )
        return {
            "train": train_count + (group_size - requested),
            "validation": validation_count,
            "test": test_count,
        }

    if group_size == 2:
        return {"train": 1, "validation": 0, "test": 1}
    if group_size < 3:
        raise ValueError("Validation/test split requires 3 videos per category/label group.")

    _ = train_ratio
    validation = max(1, int(group_size * validation_ratio))
    test = max(1, int(group_size * test_ratio))
    train = group_size - validation - test
    if train < 1:
        raise ValueError(
            f"Ratio split requires 3 videos per category/label group, got {group_size}."
        )
    return {"train": train, "validation": validation, "test": test}


def assign_video_splits(
    metadata_rows: list[dict[str, str]],
    seed: int = 42,
    train_count: int | None = None,
    validation_count: int | None = None,
    test_count: int | None = None,
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> list[SplitRecord]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in metadata_rows:
        groups[(row["category"], row["public_label"])].append(row["source"])

    rng = random.Random(seed)
    records: list[SplitRecord] = []
    for (category, label), sources in sorted(groups.items()):
        shuffled = sorted(set(sources))
        rng.shuffle(shuffled)
        counts = _split_counts_for_group(
            group_size=len(shuffled),
            train_count=train_count,
            validation_count=validation_count,
            test_count=test_count,
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            test_ratio=test_ratio,
        )
        split_order = (
            ["train"] * counts["train"]
            + ["validation"] * counts["validation"]
            + ["test"] * counts["test"]
        )
        for index, source in enumerate(shuffled):
            records.append(
                SplitRecord(
                    source=source,
                    category=category,
                    label=label,
                    split=split_order[index],
                )
            )
    return sorted(records, key=lambda record: record.source)


def assign_grouped_video_splits(
    metadata_rows: list[dict[str, str]],
    seed: int = 42,
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> list[GroupedSplitRecord]:
    groups_by_category: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in metadata_rows:
        category = row["category"]
        pair_id = f"{category}/{infer_tempglitch_pair_id(row['source'])}"
        groups_by_category[category][pair_id].append(row)

    rng = random.Random(seed)
    records: list[GroupedSplitRecord] = []
    for category, pair_groups in sorted(groups_by_category.items()):
        group_ids = sorted(pair_groups)
        rng.shuffle(group_ids)
        counts = _split_counts_for_group(
            group_size=len(group_ids),
            train_count=None,
            validation_count=None,
            test_count=None,
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            test_ratio=test_ratio,
        )
        split_order = (
            ["train"] * counts["train"]
            + ["validation"] * counts["validation"]
            + ["test"] * counts["test"]
        )
        for pair_id, split in zip(group_ids, split_order):
            for row in pair_groups[pair_id]:
                records.append(
                    GroupedSplitRecord(
                        source=row["source"],
                        category=category,
                        label=row["public_label"],
                        split=split,
                        pair_id_heuristic=pair_id,
                    )
                )
    return sorted(records, key=lambda record: record.source)


def validate_no_group_leakage(records: list[GroupedSplitRecord | dict[str, Any]]) -> dict[str, Any]:
    report = pair_leakage_report(records)
    return {
        "grouping_mode": report["grouping_mode"],
        "group_count": report["group_count"],
        "suspected_pair_count": report["suspected_pair_count"],
        "cross_split_group_count": report["cross_split_pair_count"],
        "cross_split_groups": report["cross_split_pairs"],
    }


def write_grouped_split_csv(
    path: Path,
    records: list[GroupedSplitRecord],
    seed: int,
    grouping_mode: str = "pair_id_heuristic",
) -> tuple[Path, Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=GROUPED_SPLIT_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "source": record.source,
                    "category": record.category,
                    "label": record.label,
                    "split": record.split,
                    "pair_id_heuristic": record.pair_id_heuristic,
                }
            )
    validation = validate_no_group_leakage(records)
    metadata_path = path.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(
            {
                "seed": seed,
                "grouping_mode": grouping_mode,
                **validation,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path, metadata_path


def write_split_csv(path: Path, records: list[SplitRecord]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SPLIT_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "source": record.source,
                    "category": record.category,
                    "label": record.label,
                    "split": record.split,
                }
            )
    return path


def read_split_csv(path: Path) -> list[SplitRecord]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [
            SplitRecord(
                source=row["source"],
                category=row["category"],
                label=row["label"],
                split=row["split"],
            )
            for row in csv.DictReader(handle)
        ]


def read_grouped_split_csv(path: Path) -> list[GroupedSplitRecord]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [
            GroupedSplitRecord(
                source=row["source"],
                category=row["category"],
                label=row["label"],
                split=row["split"],
                pair_id_heuristic=row["pair_id_heuristic"],
            )
            for row in csv.DictReader(handle)
        ]


def sources_for_split(records: list[SplitRecord], split: str) -> set[str]:
    return {record.source for record in records if record.split == split}


def split_counts_by_group(records: list[SplitRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = f"{record.category}/{record.label}/{record.split}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def filter_manifest_by_sources(input_path: Path, sources: set[str], output_path: Path) -> Path:
    records = [record for record in read_manifest(input_path) if record.source in sources]
    write_manifest(output_path, records)
    return output_path


def filter_labels_by_sources(input_path: Path, sources: set[str], output_path: Path) -> Path:
    labels = [label for label in read_labels(input_path) if label.source in sources]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "start_frame", "end_frame", "label"])
        writer.writeheader()
        for label in labels:
            writer.writerow(
                {
                    "source": label.source,
                    "start_frame": label.start_frame,
                    "end_frame": label.end_frame,
                    "label": label.label,
                }
            )
    return output_path


def filter_scores_by_sources(input_path: Path, sources: set[str], output_path: Path) -> Path:
    with input_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = [row for row in reader if row["source"] in sources]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path
