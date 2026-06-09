from pathlib import Path

import pytest

from glitch_detection.manifest import LabelInterval
from glitch_detection.video_eval import (
    aggregate_scores_by_source,
    build_video_level_rows,
    calibrate_video_threshold,
    compute_video_level_metrics,
    evaluate_video_with_fixed_threshold,
    source_labels_from_intervals,
)
from scripts.run_tempglitch_video_level_experiments import require_input_file

SCORE_ROWS = [
    {"source": "buggy", "score": "0.1"},
    {"source": "buggy", "score": "0.5"},
    {"source": "buggy", "score": "0.9"},
    {"source": "normal", "score": "0.2"},
    {"source": "normal", "score": "0.4"},
]


def _scores_by_source(rows: list[dict[str, object]]) -> dict[str, float]:
    return {str(row["source"]): float(row["score"]) for row in rows}


def test_aggregate_scores_by_source_mean_max_median():
    assert _scores_by_source(aggregate_scores_by_source(SCORE_ROWS, "mean")) == {
        "buggy": 0.5,
        "normal": pytest.approx(0.3),
    }
    assert _scores_by_source(aggregate_scores_by_source(SCORE_ROWS, "max")) == {
        "buggy": 0.9,
        "normal": 0.4,
    }
    assert _scores_by_source(aggregate_scores_by_source(SCORE_ROWS, "median")) == {
        "buggy": 0.5,
        "normal": pytest.approx(0.3),
    }


def test_aggregate_scores_by_source_percentiles():
    rows = [{"source": "video", "score": str(score)} for score in range(1, 11)]

    assert _scores_by_source(aggregate_scores_by_source(rows, "p90"))["video"] == 9.1
    assert _scores_by_source(aggregate_scores_by_source(rows, "p95"))["video"] == pytest.approx(
        9.55
    )


def test_topk_mean_uses_top_scores_and_handles_short_sources():
    rows = aggregate_scores_by_source(SCORE_ROWS, "topk_mean", top_k=3)

    assert _scores_by_source(rows) == {
        "buggy": 0.5,
        "normal": pytest.approx(0.3),
    }
    assert {str(row["source"]): int(row["clip_count"]) for row in rows} == {
        "buggy": 3,
        "normal": 2,
    }


def test_source_labels_from_intervals_marks_implicit_negatives():
    intervals = [LabelInterval("buggy", 0, 100, 1)]

    labels = source_labels_from_intervals(intervals, sources={"buggy", "normal"})

    assert labels == {"buggy": 1, "normal": 0}


def test_build_video_level_rows_merges_split_metadata():
    aggregated = aggregate_scores_by_source(SCORE_ROWS, "max")
    split_rows = [
        {"source": "buggy", "category": "Blinking", "label": "Buggy", "split": "validation"},
        {"source": "normal", "category": "Blinking", "label": "Normal", "split": "validation"},
    ]

    rows = build_video_level_rows(
        aggregated,
        source_labels={"buggy": 1, "normal": 0},
        split_rows=split_rows,
    )

    assert rows[0]["aggregation"] == "max"
    assert rows[0]["category"] == "Blinking"
    assert rows[0]["split"] == "validation"
    assert rows[0]["source_label"] == "Buggy"
    assert [row["label"] for row in rows] == [1, 0]


def test_video_threshold_calibrated_on_validation_only():
    validation_rows = [
        {"source": "v_normal", "score": 0.2, "label": 0, "aggregation": "max"},
        {"source": "v_buggy", "score": 0.8, "label": 1, "aggregation": "max"},
    ]
    test_rows = [
        {"source": "t_normal", "score": 0.7, "label": 0, "aggregation": "max"},
        {"source": "t_buggy", "score": 0.9, "label": 1, "aggregation": "max"},
    ]

    calibration = calibrate_video_threshold(validation_rows, aggregation="max", scorer="demo")
    result = evaluate_video_with_fixed_threshold(test_rows, calibration)

    assert calibration["threshold"] == 0.8
    assert calibration["calibration_split"] == "validation"
    assert result["threshold"] == 0.8
    assert result["threshold_source"] == "validation"
    assert result["test_metrics"]["true_negative"] == 1.0


def test_video_metrics_include_confusion_counts_and_auroc():
    rows = [
        {"score": 0.1, "label": 0},
        {"score": 0.7, "label": 0},
        {"score": 0.8, "label": 1},
        {"score": 0.9, "label": 1},
    ]

    metrics = compute_video_level_metrics(rows, threshold=0.75)

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["accuracy"] == 1.0
    assert metrics["auroc"] == 1.0
    assert metrics["true_positive"] == 2.0
    assert metrics["false_positive"] == 0.0
    assert metrics["false_negative"] == 0.0
    assert metrics["true_negative"] == 2.0
    assert metrics["source_count"] == 4
    assert metrics["positive_source_count"] == 2
    assert metrics["negative_source_count"] == 2


def test_missing_input_file_error_lists_expected_path(tmp_path: Path):
    missing = tmp_path / "frame_diff_val_scores.csv"

    with pytest.raises(FileNotFoundError, match="frame_diff_val_scores.csv"):
        require_input_file(missing, description="validation scores for frame_diff")
