from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .manifest import read_labels, read_manifest, write_manifest

SPLIT_FIELDS = ["source", "category", "label", "split"]


@dataclass(frozen=True)
class SplitRecord:
    source: str
    category: str
    label: str
    split: str


def assign_video_splits(metadata_rows: list[dict[str, str]], seed: int = 42) -> list[SplitRecord]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in metadata_rows:
        groups[(row["category"], row["public_label"])].append(row["source"])

    rng = random.Random(seed)
    records: list[SplitRecord] = []
    for (category, label), sources in sorted(groups.items()):
        shuffled = sorted(set(sources))
        rng.shuffle(shuffled)
        split_order = ["train", "test"] if len(shuffled) == 2 else ["train", "validation", "test"]
        for index, source in enumerate(shuffled):
            records.append(
                SplitRecord(
                    source=source,
                    category=category,
                    label=label,
                    split=split_order[index % len(split_order)],
                )
            )
    return sorted(records, key=lambda record: record.source)


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


def sources_for_split(records: list[SplitRecord], split: str) -> set[str]:
    return {record.source for record in records if record.split == split}


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
