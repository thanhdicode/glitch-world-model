from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import feature_distance, frame_diff, mini_latent
from .manifest import ClipRecord
from .pairs import infer_tempglitch_pair_id
from .splits import GroupedSplitRecord, SplitRecord
from .video_eval import aggregate_scores_by_source, build_video_level_rows


@dataclass(frozen=True)
class FittedScorer:
    scorer: str
    model: Any
    fit_metadata: dict[str, Any]


def train_normal_records(
    manifest_records: Iterable[ClipRecord],
    split_records: Iterable[SplitRecord | GroupedSplitRecord],
) -> list[ClipRecord]:
    normal_sources = {
        row.source for row in split_records if row.split == "train" and row.label == "Normal"
    }
    return [record for record in manifest_records if record.source in normal_sources]


def fit_scorer_for_split(
    scorer: str,
    manifest_records: list[ClipRecord],
    split_records: list[SplitRecord | GroupedSplitRecord],
) -> FittedScorer:
    validation_sources = sorted({row.source for row in split_records if row.split == "validation"})
    test_sources = sorted({row.source for row in split_records if row.split == "test"})
    train_records = train_normal_records(manifest_records, split_records)
    train_sources = sorted({record.source for record in train_records})

    if scorer == "frame_diff":
        model = None
        train_sources = []
        train_clip_count = 0
        fit_split = "none"
        labels_used = False
    elif scorer == "feature_distance":
        model = feature_distance.fit_centroid(train_records)
        train_clip_count = len(train_records)
        fit_split = "train"
        labels_used = True
    elif scorer == "mini_latent":
        model = mini_latent.fit_model(train_records)
        train_clip_count = len(train_records)
        fit_split = "train"
        labels_used = True
    else:
        raise ValueError(f"Unsupported repeated-evaluation scorer: {scorer}")

    return FittedScorer(
        scorer=scorer,
        model=model,
        fit_metadata={
            "scorer": scorer,
            "fit_split": fit_split,
            "train_sources_used": train_sources,
            "train_normal_clip_count": train_clip_count,
            "validation_sources_count": len(validation_sources),
            "test_sources_count": len(test_sources),
            "labels_used_for_fitting": labels_used,
        },
    )


def score_fitted_scorer(fitted: FittedScorer, records: list[ClipRecord]) -> dict[str, float]:
    if fitted.scorer == "frame_diff":
        return {record.clip_id: frame_diff.score_clip(Path(record.clip_dir)) for record in records}
    if fitted.scorer == "feature_distance":
        return feature_distance.score_records_with_centroid(records, fitted.model)
    if fitted.scorer == "mini_latent":
        return mini_latent.score_records_with_model(records, fitted.model)
    raise ValueError(f"Unsupported repeated-evaluation scorer: {fitted.scorer}")


def clip_score_rows(
    records: list[ClipRecord],
    scores: dict[str, float],
) -> list[dict[str, Any]]:
    return [
        {
            "clip_id": record.clip_id,
            "source": record.source,
            "clip_dir": record.clip_dir,
            "start_frame": record.start_frame,
            "end_frame": record.end_frame,
            "score": float(scores[record.clip_id]),
        }
        for record in records
    ]


def write_clip_scores_csv(rows: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def split_rows_as_dicts(
    split_records: Iterable[SplitRecord | GroupedSplitRecord],
) -> list[dict[str, str]]:
    return [
        {
            "source": row.source,
            "category": row.category,
            "label": row.label,
            "split": row.split,
            "pair_id_heuristic": str(getattr(row, "pair_id_heuristic", "")),
        }
        for row in split_records
    ]


def source_labels_for_split(
    split_records: Iterable[SplitRecord | GroupedSplitRecord],
    split: str,
) -> dict[str, int]:
    return {row.source: int(row.label == "Buggy") for row in split_records if row.split == split}


def build_video_rows(
    clip_rows: list[dict[str, Any]],
    split_records: list[SplitRecord | GroupedSplitRecord],
    split: str,
    aggregation: str,
    top_k: int,
) -> list[dict[str, Any]]:
    video_rows = build_video_level_rows(
        aggregate_scores_by_source(clip_rows, aggregation, top_k),
        source_labels_for_split(split_records, split),
        split_rows_as_dicts(split_records),
    )
    for row in video_rows:
        row["pair_id_heuristic"] = (
            f"{row.get('category', 'unknown')}/{infer_tempglitch_pair_id(str(row['source']))}"
        )
    return video_rows
