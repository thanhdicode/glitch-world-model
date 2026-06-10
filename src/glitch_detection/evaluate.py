from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .manifest import clip_has_glitch, read_labels


def read_scores(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def binary_metrics(labels: list[int], predictions: list[int]) -> dict[str, float]:
    tp = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 1)
    fp = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 1)
    fn = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 0)
    tn = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 0)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "true_positive": float(tp),
        "false_positive": float(fp),
        "false_negative": float(fn),
        "true_negative": float(tn),
    }


def choose_best_f1_threshold(
    labels: list[int], scores: list[float]
) -> tuple[float, dict[str, float]]:
    if not scores:
        return 0.0, binary_metrics(labels, [])

    best_threshold = min(scores)
    best_metrics = binary_metrics(labels, [1 if score >= best_threshold else 0 for score in scores])
    for threshold in sorted(set(scores)):
        predictions = [1 if score >= threshold else 0 for score in scores]
        metrics = binary_metrics(labels, predictions)
        if metrics["f1"] > best_metrics["f1"]:
            best_threshold = threshold
            best_metrics = metrics
    return best_threshold, best_metrics


def auroc(labels: list[int], scores: list[float]) -> float | None:
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    if not positives or not negatives:
        return None

    wins = 0.0
    total = len(positives) * len(negatives)
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / total


def evaluate_scores(
    scores_path: Path,
    labels_path: Path | None,
    output_path: Path,
    threshold: float | None = None,
    *,
    allow_fit_threshold: bool = False,
) -> dict[str, Any]:
    rows = read_scores(scores_path)
    intervals = read_labels(labels_path)
    labels = [
        int(
            clip_has_glitch(
                source=row["source"],
                start_frame=int(row["start_frame"]),
                end_frame=int(row["end_frame"]),
                labels=intervals,
            )
        )
        for row in rows
    ]
    scores = [float(row["score"]) for row in rows]

    if threshold is None:
        if not allow_fit_threshold:
            raise ValueError(
                "Refusing to fit a threshold on evaluation rows by default. "
                "Pass a frozen threshold or set allow_fit_threshold=True for validation/demo use."
            )
        threshold, metrics = choose_best_f1_threshold(labels, scores)
        threshold_source = "fitted_on_evaluation_rows"
    else:
        predictions = [1 if score >= threshold else 0 for score in scores]
        metrics = binary_metrics(labels, predictions)
        threshold_source = "provided"

    result: dict[str, Any] = {
        "scores_path": str(scores_path),
        "labels_path": str(labels_path) if labels_path else None,
        "threshold": threshold,
        "threshold_source": threshold_source,
        "auroc": auroc(labels, scores),
        "clip_count": len(rows),
        "positive_clip_count": sum(labels),
        **metrics,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate anomaly scores against interval labels.")
    parser.add_argument("--scores", required=True, type=Path, help="Path to scores.csv.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional labels CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output metrics JSON path.")
    parser.add_argument("--threshold", type=float, default=None, help="Optional fixed threshold.")
    parser.add_argument(
        "--fit-threshold",
        action="store_true",
        help="Explicitly fit the threshold on these rows; use only for validation or demos.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = evaluate_scores(
        args.scores,
        args.labels,
        args.output,
        args.threshold,
        allow_fit_threshold=args.fit_threshold,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
