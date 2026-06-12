from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REQUIRED_TEMPGLITCH_CATEGORIES = frozenset(
    {
        "Blinking",
        "Frozen Animation",
        "Shooting Error",
        "Stuck in Place",
        "Velocity Bug",
    }
)


@dataclass(frozen=True)
class LeWMResearchProtocol:
    seed: int = 42
    minimum_train_normal_episodes: int = 30
    minimum_validation_normal_episodes: int = 10
    minimum_validation_buggy_episodes: int = 15
    required_categories: frozenset[str] = REQUIRED_TEMPGLITCH_CATEGORIES


def _read_csv_by_source(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {row["source"]: row for row in csv.DictReader(handle)}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_local_research_source(
    metadata_path: Path,
    split_path: Path,
    video_root: Path,
    protocol: LeWMResearchProtocol = LeWMResearchProtocol(),
) -> dict[str, Any]:
    metadata = _read_csv_by_source(metadata_path)
    split = _read_csv_by_source(split_path)
    missing_split = sorted(set(metadata) - set(split))
    if missing_split:
        raise ValueError(f"Missing frozen split rows for local sources: {missing_split}")

    selected: dict[str, list[dict[str, str]]] = {
        "train_normal": [],
        "validation_normal": [],
        "validation_buggy": [],
    }
    missing_videos: list[str] = []
    for source, metadata_row in metadata.items():
        row = split[source]
        video_path = video_root / metadata_row["local_video_path"]
        if not video_path.is_file():
            missing_videos.append(str(video_path))
            continue
        if row["materialize"].lower() != "true":
            continue
        key = (row["split"], row["label"])
        if key == ("train", "Normal"):
            selected["train_normal"].append(row)
        elif key == ("validation", "Normal"):
            selected["validation_normal"].append(row)
        elif key == ("validation", "Buggy"):
            selected["validation_buggy"].append(row)
        elif row["split"] == "test":
            raise ValueError(f"Locked-test source was locally materialized: {source}")

    if missing_videos:
        raise FileNotFoundError(f"Missing locally declared TempGlitch videos: {missing_videos}")

    for rows in selected.values():
        rows.sort(
            key=lambda row: hashlib.sha256(f"{protocol.seed}:{row['source']}".encode()).hexdigest()
        )

    minimums = {
        "train_normal": protocol.minimum_train_normal_episodes,
        "validation_normal": protocol.minimum_validation_normal_episodes,
        "validation_buggy": protocol.minimum_validation_buggy_episodes,
    }
    insufficient = {
        key: {"required": minimums[key], "found": len(rows)}
        for key, rows in selected.items()
        if len(rows) < minimums[key]
    }
    if insufficient:
        raise ValueError(f"Insufficient local research episodes: {insufficient}")

    train_sources = {row["source"] for row in selected["train_normal"]}
    validation_sources = {
        row["source"] for key in ("validation_normal", "validation_buggy") for row in selected[key]
    }
    train_pairs = {row["pair_id"] for row in selected["train_normal"]}
    validation_pairs = {
        row["pair_id"] for key in ("validation_normal", "validation_buggy") for row in selected[key]
    }
    source_overlap = sorted(train_sources & validation_sources)
    pair_overlap = sorted(train_pairs & validation_pairs)
    if source_overlap or pair_overlap:
        raise ValueError(
            f"Research train/validation leakage: sources={source_overlap}, pairs={pair_overlap}"
        )

    validation_categories = {
        row["category"]
        for key in ("validation_normal", "validation_buggy")
        for row in selected[key]
    }
    missing_categories = sorted(protocol.required_categories - validation_categories)
    if missing_categories:
        raise ValueError(f"Validation is missing required categories: {missing_categories}")

    return {
        "status": "research_mvp_source_ready",
        "protocol": {
            **asdict(protocol),
            "required_categories": sorted(protocol.required_categories),
        },
        "metadata_path": str(metadata_path),
        "metadata_sha256": _sha256_file(metadata_path),
        "split_path": str(split_path),
        "split_sha256": _sha256_file(split_path),
        "video_root": str(video_root),
        "counts": {key: len(rows) for key, rows in selected.items()},
        "category_counts": {
            key: dict(sorted(Counter(row["category"] for row in rows).items()))
            for key, rows in selected.items()
        },
        "selected_sources": {
            key: [row["source"] for row in rows] for key, rows in selected.items()
        },
        "source_overlap": source_overlap,
        "pair_overlap": pair_overlap,
        "action_mode": "zero_action",
        "normal_only_training": True,
        "checkpoint_selection_split": "validation_normal",
        "performance_evaluation_split": "validation_normal_plus_buggy",
        "primary_evaluation_unit": "episode",
        "window_metrics_diagnostic_only": True,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def write_research_audit(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path
