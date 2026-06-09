from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

from .evaluate import auroc, binary_metrics, choose_best_f1_threshold, read_scores
from .manifest import LabelInterval, read_labels
from .splits import SplitRecord, read_split_csv

AGGREGATIONS = ("mean", "max", "median", "p90", "p95", "topk_mean")
VIDEO_SCORE_FIELDS = [
    "source",
    "category",
    "split",
    "source_label",
    "score",
    "label",
    "clip_count",
    "aggregation",
]


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _aggregate(values: list[float], aggregation: str, top_k: int) -> float:
    if aggregation == "mean":
        return mean(values)
    if aggregation == "max":
        return max(values)
    if aggregation == "median":
        return median(values)
    if aggregation == "p90":
        return _percentile(values, 0.90)
    if aggregation == "p95":
        return _percentile(values, 0.95)
    if aggregation == "topk_mean":
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        return mean(sorted(values, reverse=True)[:top_k])
    raise ValueError(f"Unsupported aggregation: {aggregation}. Expected one of {AGGREGATIONS}.")


def aggregate_scores_by_source(
    score_rows: Path | Iterable[dict[str, Any]],
    aggregation: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    rows = read_scores(score_rows) if isinstance(score_rows, Path) else list(score_rows)
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source"])].append(float(row["score"]))
    return [
        {
            "source": source,
            "score": _aggregate(values, aggregation, top_k),
            "clip_count": len(values),
            "aggregation": aggregation,
        }
        for source, values in sorted(grouped.items())
    ]


def source_labels_from_intervals(
    intervals: Path | Iterable[LabelInterval],
    sources: Iterable[str] | None = None,
) -> dict[str, int]:
    label_intervals = read_labels(intervals) if isinstance(intervals, Path) else list(intervals)
    labels = {source: 0 for source in sources or []}
    for interval in label_intervals:
        if interval.label == 1:
            labels[interval.source] = 1
    return dict(sorted(labels.items()))


def _split_metadata(
    split_rows: Path | Iterable[SplitRecord | dict[str, Any]] | None,
) -> dict[str, dict[str, str]]:
    if split_rows is None:
        return {}
    rows: Iterable[SplitRecord | dict[str, Any]]
    rows = read_split_csv(split_rows) if isinstance(split_rows, Path) else split_rows
    metadata: dict[str, dict[str, str]] = {}
    for row in rows:
        if isinstance(row, SplitRecord):
            metadata[row.source] = {
                "category": row.category,
                "source_label": row.label,
                "split": row.split,
            }
        else:
            metadata[str(row["source"])] = {
                "category": str(row.get("category", "")),
                "source_label": str(row.get("source_label", row.get("label", ""))),
                "split": str(row.get("split", "")),
            }
    return metadata


def build_video_level_rows(
    aggregated_rows: Iterable[dict[str, Any]],
    source_labels: dict[str, int],
    split_rows: Path | Iterable[SplitRecord | dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    metadata = _split_metadata(split_rows)
    result: list[dict[str, Any]] = []
    for row in aggregated_rows:
        source = str(row["source"])
        result.append(
            {
                "source": source,
                **metadata.get(source, {}),
                "score": float(row["score"]),
                "label": int(source_labels.get(source, 0)),
                "clip_count": int(row["clip_count"]),
                "aggregation": str(row["aggregation"]),
            }
        )
    return result


def compute_video_level_metrics(
    rows: Iterable[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    video_rows = list(rows)
    labels = [int(row["label"]) for row in video_rows]
    scores = [float(row["score"]) for row in video_rows]
    predictions = [int(score >= threshold) for score in scores]
    return {
        **binary_metrics(labels, predictions),
        "auroc": auroc(labels, scores),
        "source_count": len(video_rows),
        "positive_source_count": sum(labels),
        "negative_source_count": len(labels) - sum(labels),
    }


def calibrate_video_threshold(
    validation_rows: Iterable[dict[str, Any]],
    aggregation: str,
    scorer: str,
) -> dict[str, Any]:
    rows = list(validation_rows)
    labels = [int(row["label"]) for row in rows]
    scores = [float(row["score"]) for row in rows]
    threshold, _ = choose_best_f1_threshold(labels, scores)
    return {
        "threshold": threshold,
        "calibration_split": "validation",
        "aggregation": aggregation,
        "scorer": scorer,
        "validation_metrics": compute_video_level_metrics(rows, threshold),
    }


def evaluate_video_with_fixed_threshold(
    test_rows: Iterable[dict[str, Any]],
    calibration: dict[str, Any],
) -> dict[str, Any]:
    threshold = float(calibration["threshold"])
    return {
        "threshold": threshold,
        "threshold_source": calibration.get("calibration_split", "validation"),
        "aggregation": calibration["aggregation"],
        "scorer": calibration["scorer"],
        "test_metrics": compute_video_level_metrics(test_rows, threshold),
    }


def write_video_rows_csv(rows: Iterable[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=VIDEO_SCORE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def write_json(payload: Any, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def write_video_comparison(rows: list[dict[str, Any]], output_path: Path) -> Path:
    lines = [
        "# TempGlitch Video-Level Comparison",
        "",
        "| Scorer | Aggregation | Threshold | Precision | Recall | F1 | AUROC | TP | FP | FN | TN | Sources | Note |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        metrics = row["test_metrics"]
        auroc_value = metrics["auroc"]
        auroc_text = "n/a" if auroc_value is None else f"{auroc_value:.6g}"
        lines.append(
            f"| {row['scorer']} | {row['aggregation']} | {row['threshold']:.6g} | "
            f"{metrics['precision']:.6g} | {metrics['recall']:.6g} | {metrics['f1']:.6g} | "
            f"{auroc_text} | {metrics['true_positive']:.0f} | {metrics['false_positive']:.0f} | "
            f"{metrics['false_negative']:.0f} | {metrics['true_negative']:.0f} | "
            f"{metrics['source_count']} | fixed validation threshold |"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
