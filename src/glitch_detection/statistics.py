from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean
from typing import Any, Iterable

import numpy as np

from .evaluate import auroc, average_precision, binary_metrics


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _metric(rows: list[dict[str, Any]], metric_name: str, threshold: float | None) -> float | None:
    labels = [int(row["label"]) for row in rows]
    scores = [float(row["score"]) for row in rows]
    if metric_name == "auroc":
        return auroc(labels, scores)
    if metric_name == "auprc":
        return average_precision(labels, scores)
    if metric_name == "f1":
        if threshold is None:
            raise ValueError("F1 bootstrap requires a fixed threshold.")
        predictions = [int(score >= threshold) for score in scores]
        return binary_metrics(labels, predictions)["f1"]
    if metric_name in {"balanced_accuracy", "mcc"}:
        if threshold is None:
            raise ValueError(f"{metric_name} bootstrap requires a fixed threshold.")
        predictions = [int(score >= threshold) for score in scores]
        metrics = binary_metrics(labels, predictions)
        if metric_name == "balanced_accuracy":
            negatives = metrics["true_negative"] + metrics["false_positive"]
            positives = metrics["true_positive"] + metrics["false_negative"]
            if negatives == 0 or positives == 0:
                return None
            specificity = metrics["true_negative"] / negatives
            return (metrics["recall"] + specificity) / 2.0
        tp = metrics["true_positive"]
        fp = metrics["false_positive"]
        fn = metrics["false_negative"]
        tn = metrics["true_negative"]
        denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        if denominator == 0:
            return None
        return ((tp * tn) - (fp * fn)) / denominator
    raise ValueError(
        "metric_name must be one of 'auroc', 'auprc', 'f1', 'balanced_accuracy', or 'mcc'."
    )


def _compute_midrank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values)
    sorted_values = values[order]
    midranks = np.zeros(len(values), dtype=float)
    start = 0
    while start < len(sorted_values):
        end = start
        while end < len(sorted_values) and sorted_values[end] == sorted_values[start]:
            end += 1
        midranks[start:end] = 0.5 * (start + end - 1) + 1.0
        start = end
    result = np.empty(len(values), dtype=float)
    result[order] = midranks
    return result


def _fast_delong(
    predictions_sorted_transposed: np.ndarray, label_1_count: int
) -> tuple[np.ndarray, np.ndarray]:
    classifier_count = predictions_sorted_transposed.shape[0]
    positive_count = label_1_count
    negative_count = predictions_sorted_transposed.shape[1] - positive_count
    positive_examples = predictions_sorted_transposed[:, :positive_count]
    negative_examples = predictions_sorted_transposed[:, positive_count:]
    tx = np.empty((classifier_count, positive_count), dtype=float)
    ty = np.empty((classifier_count, negative_count), dtype=float)
    tz = np.empty((classifier_count, positive_count + negative_count), dtype=float)
    for index in range(classifier_count):
        tx[index] = _compute_midrank(positive_examples[index])
        ty[index] = _compute_midrank(negative_examples[index])
        tz[index] = _compute_midrank(predictions_sorted_transposed[index])

    aucs = tz[:, :positive_count].sum(axis=1) / (positive_count * negative_count) - (
        positive_count + 1.0
    ) / (2.0 * negative_count)
    v01 = (tz[:, :positive_count] - tx) / negative_count
    v10 = 1.0 - (tz[:, positive_count:] - ty) / positive_count
    sx = np.atleast_2d(np.cov(v01, bias=True))
    sy = np.atleast_2d(np.cov(v10, bias=True))
    delong_covariance = sx / positive_count + sy / negative_count
    return aucs, delong_covariance


def delong_auroc_test(
    labels: Iterable[int],
    scores_a: Iterable[float],
    scores_b: Iterable[float],
) -> dict[str, float | None]:
    label_list = [int(value) for value in labels]
    score_list_a = [float(value) for value in scores_a]
    score_list_b = [float(value) for value in scores_b]
    if not (len(label_list) == len(score_list_a) == len(score_list_b)):
        raise ValueError("labels and score lists must have identical lengths.")
    if not label_list:
        raise ValueError("DeLong AUROC test requires at least one row.")
    positives = sum(label_list)
    negatives = len(label_list) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("DeLong AUROC test requires both positive and negative labels.")
    if any(label not in {0, 1} for label in label_list):
        raise ValueError("DeLong AUROC test requires binary labels encoded as 0/1.")

    labels_array = np.asarray(label_list, dtype=int)
    order = np.argsort(-labels_array, kind="mergesort")
    sorted_predictions = np.vstack(
        [
            np.asarray(score_list_a, dtype=float)[order],
            np.asarray(score_list_b, dtype=float)[order],
        ]
    )
    aucs, covariance = _fast_delong(sorted_predictions, positives)
    difference = float(aucs[0] - aucs[1])
    variance = float(np.array([1.0, -1.0]) @ covariance @ np.array([1.0, -1.0]))
    if variance <= 0:
        z_score = (
            0.0
            if math.isclose(difference, 0.0, abs_tol=1e-12)
            else math.copysign(math.inf, difference)
        )
        p_value = 1.0 if z_score == 0.0 else 0.0
    else:
        z_score = difference / math.sqrt(variance)
        p_value = math.erfc(abs(z_score) / math.sqrt(2.0))
    return {
        "auroc_a": float(aucs[0]),
        "auroc_b": float(aucs[1]),
        "z": float(z_score),
        "p_value": float(p_value),
    }


def _group_rows(rows: list[dict[str, Any]], group_key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if group_key not in row:
            raise KeyError(f"Missing bootstrap group key {group_key!r}.")
        groups[str(row[group_key])].append(row)
    return groups


def _row_signature(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in row.items() if key != "score"))


def paired_bootstrap_delta(
    rows_a: Iterable[dict[str, Any]],
    rows_b: Iterable[dict[str, Any]],
    metric_name: str,
    group_key: str = "source",
    n_bootstrap: int = 1000,
    seed: int = 42,
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    source_rows_a = list(rows_a)
    source_rows_b = list(rows_b)
    if not source_rows_a or not source_rows_b:
        raise ValueError("Paired bootstrap delta requires at least one row per method.")
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be at least 1.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")

    groups_a = _group_rows(source_rows_a, group_key)
    groups_b = _group_rows(source_rows_b, group_key)
    if sorted(groups_a) != sorted(groups_b):
        raise ValueError(
            "Paired bootstrap delta requires identical group keys across both methods."
        )
    for group_id in sorted(groups_a):
        signatures_a = sorted(_row_signature(row) for row in groups_a[group_id])
        signatures_b = sorted(_row_signature(row) for row in groups_b[group_id])
        if signatures_a != signatures_b:
            raise ValueError(
                f"Paired bootstrap delta requires aligned rows within group {group_id!r}."
            )

    rng = random.Random(seed)
    group_ids = sorted(groups_a)
    values: list[float] = []
    for _ in range(n_bootstrap):
        sampled_group_ids = rng.choices(group_ids, k=len(group_ids))
        sampled_a = [row for group_id in sampled_group_ids for row in groups_a[group_id]]
        sampled_b = [row for group_id in sampled_group_ids for row in groups_b[group_id]]
        value_a = _metric(sampled_a, metric_name, threshold=None)
        value_b = _metric(sampled_b, metric_name, threshold=None)
        if value_a is not None and value_b is not None:
            values.append(float(value_a - value_b))

    point_a = _metric(source_rows_a, metric_name, threshold=None)
    point_b = _metric(source_rows_b, metric_name, threshold=None)
    point_delta = None
    if point_a is not None and point_b is not None:
        point_delta = float(point_a - point_b)
    alpha = (1.0 - confidence_level) / 2.0
    return {
        "metric_name": metric_name,
        "point_a": point_a,
        "point_b": point_b,
        "point_delta": point_delta,
        "lower": _percentile(values, alpha) if values else None,
        "mean": mean(values) if values else None,
        "upper": _percentile(values, 1.0 - alpha) if values else None,
        "n_bootstrap": n_bootstrap,
        "valid_bootstrap_count": len(values),
        "seed": seed,
        "group_key": group_key,
        "confidence_level": confidence_level,
    }


def bootstrap_metric_ci(
    rows: Iterable[dict[str, Any]],
    metric_name: str,
    n_bootstrap: int = 1000,
    seed: int = 42,
    group_key: str = "source",
    confidence_level: float = 0.95,
    threshold: float | None = None,
) -> dict[str, Any]:
    source_rows = list(rows)
    if not source_rows:
        raise ValueError("Bootstrap requires at least one row.")
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be at least 1.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")

    groups = _group_rows(source_rows, group_key)
    group_ids = sorted(groups)
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(n_bootstrap):
        sampled_rows = [
            row for group_id in rng.choices(group_ids, k=len(group_ids)) for row in groups[group_id]
        ]
        value = _metric(sampled_rows, metric_name, threshold)
        if value is not None:
            values.append(float(value))

    alpha = (1.0 - confidence_level) / 2.0
    point = _metric(source_rows, metric_name, threshold)
    return {
        "metric_name": metric_name,
        "point": point,
        "lower": _percentile(values, alpha) if values else None,
        "mean": mean(values) if values else None,
        "upper": _percentile(values, 1.0 - alpha) if values else None,
        "n_bootstrap": n_bootstrap,
        "valid_bootstrap_count": len(values),
        "seed": seed,
        "group_key": group_key,
        "confidence_level": confidence_level,
    }
