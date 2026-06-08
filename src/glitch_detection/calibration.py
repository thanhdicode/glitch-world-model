from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluate import evaluate_scores


def calibrate_threshold(
    validation_scores_path: Path,
    labels_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    calibration = evaluate_scores(validation_scores_path, labels_path, output_path)
    calibration["calibration_split"] = "validation"
    output_path.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    return calibration


def evaluate_with_fixed_threshold(
    test_scores_path: Path,
    labels_path: Path,
    calibration_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    metrics = evaluate_scores(
        test_scores_path,
        labels_path,
        output_path,
        threshold=float(calibration["threshold"]),
    )
    metrics["threshold_source"] = calibration.get("calibration_split", "validation")
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
