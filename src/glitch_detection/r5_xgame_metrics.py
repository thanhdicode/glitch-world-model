"""Binary episode-level metrics guarded against one-class evaluation."""

from __future__ import annotations

from typing import Sequence

from .evaluate import auroc, average_precision, binary_metrics


def _fpr_at_95_tpr(labels: Sequence[int], scores: Sequence[float]) -> float:
    positives = sum(labels)
    negatives = len(labels) - positives
    for threshold in sorted(set(scores), reverse=True):
        predictions = [int(score >= threshold) for score in scores]
        true_positives = sum(
            label == 1 and prediction == 1 for label, prediction in zip(labels, predictions)
        )
        false_positives = sum(
            label == 0 and prediction == 1 for label, prediction in zip(labels, predictions)
        )
        if true_positives / positives >= 0.95:
            return false_positives / negatives
    return 1.0


def evaluate_r5_xgame_binary_scores(
    labels: Sequence[int], scores: Sequence[float], *, threshold: float
) -> dict[str, float]:
    """Return valid binary metrics only when both classes are present."""
    if len(labels) != len(scores) or not labels:
        raise ValueError("R5-XGame labels and scores must be non-empty and aligned.")
    if set(labels) != {0, 1}:
        raise ValueError(
            "R5-XGame binary metrics require both normal and buggy evaluation episodes."
        )
    predictions = [int(score >= threshold) for score in scores]
    classification = binary_metrics(list(labels), predictions)
    return {
        "auroc": float(auroc(list(labels), list(scores))),
        "auprc": float(average_precision(list(labels), list(scores))),
        "f1": float(classification["f1"]),
        "precision": float(classification["precision"]),
        "recall": float(classification["recall"]),
        "fpr_at_95_tpr": _fpr_at_95_tpr(labels, scores),
    }
