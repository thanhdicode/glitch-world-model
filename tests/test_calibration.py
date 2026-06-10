import json
from pathlib import Path

import pytest

from glitch_detection.calibration import calibrate_threshold, evaluate_with_fixed_threshold
from glitch_detection.evaluate import evaluate_scores


def _write_scores(path: Path, rows: list[tuple[str, float]]) -> None:
    path.write_text(
        "clip_id,source,clip_dir,start_frame,end_frame,score\n"
        + "".join(f"{source}_0,{source},{source}/0,0,3,{score}\n" for source, score in rows),
        encoding="utf-8",
    )


def test_calibrate_threshold_writes_validation_metadata(tmp_path: Path):
    scores_path = tmp_path / "validation_scores.csv"
    _write_scores(scores_path, [("normal", 0.1), ("buggy", 0.8)])
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\nbuggy,0,3,1\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "calibration.json"
    calibration = calibrate_threshold(scores_path, labels_path, output_path)

    assert calibration["threshold"] == 0.8
    assert calibration["calibration_split"] == "validation"
    assert calibration["clip_count"] == 2
    assert json.loads(output_path.read_text(encoding="utf-8")) == calibration


def test_evaluate_with_fixed_threshold_uses_calibrated_value(tmp_path: Path):
    scores_path = tmp_path / "test_scores.csv"
    _write_scores(scores_path, [("normal", 0.2), ("buggy", 0.7)])
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\nbuggy,0,3,1\n",
        encoding="utf-8",
    )
    calibration_path = tmp_path / "calibration.json"
    calibration_path.write_text(
        json.dumps({"threshold": 0.6, "calibration_split": "validation"}),
        encoding="utf-8",
    )

    metrics = evaluate_with_fixed_threshold(
        scores_path,
        labels_path,
        calibration_path,
        tmp_path / "metrics.json",
    )

    assert metrics["threshold"] == 0.6
    assert metrics["threshold_source"] == "validation"
    assert metrics["f1"] == 1.0


def test_evaluate_scores_rejects_implicit_threshold_fitting(tmp_path: Path):
    scores_path = tmp_path / "scores.csv"
    _write_scores(scores_path, [("normal", 0.1), ("buggy", 0.8)])
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\nbuggy,0,3,1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="allow_fit_threshold"):
        evaluate_scores(scores_path, labels_path, tmp_path / "metrics.json")

    assert not (tmp_path / "metrics.json").exists()


def test_evaluate_scores_allows_explicit_validation_threshold_fitting(tmp_path: Path):
    scores_path = tmp_path / "scores.csv"
    _write_scores(scores_path, [("normal", 0.1), ("buggy", 0.8)])
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\nbuggy,0,3,1\n",
        encoding="utf-8",
    )

    metrics = evaluate_scores(
        scores_path,
        labels_path,
        tmp_path / "metrics.json",
        allow_fit_threshold=True,
    )

    assert metrics["threshold"] == 0.8
    assert metrics["threshold_source"] == "fitted_on_evaluation_rows"
