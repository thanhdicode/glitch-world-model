from __future__ import annotations

from math import sqrt
from typing import Any


def _population_std(values: list[float]) -> float:
    if len(values) == 1:
        return 0.0
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return sqrt(variance)


def aggregate_seed_metrics(
    per_seed_metrics: list[dict[str, Any]],
) -> dict[str, dict[str, float | int]]:
    if not per_seed_metrics:
        raise ValueError("aggregate_seed_metrics requires at least one per-seed metrics row.")

    numeric_keys = sorted(
        {
            key
            for row in per_seed_metrics
            for key, value in row.items()
            if key != "seed" and isinstance(value, int | float) and not isinstance(value, bool)
        }
    )
    aggregated: dict[str, dict[str, float | int]] = {}
    for key in numeric_keys:
        values = [float(row[key]) for row in per_seed_metrics if key in row]
        if not values:
            continue
        aggregated[key] = {
            "mean": sum(values) / len(values),
            "std": _population_std(values),
            "min": min(values),
            "max": max(values),
            "n_seeds": len(values),
        }
    return aggregated
