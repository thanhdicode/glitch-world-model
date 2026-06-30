from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.summarize_tempglitch_selection import (
    SelectionSummaryError,
    load_comparison_rows,
    load_safety_metadata,
    render_markdown,
    summarize_selection,
)

HEADER = (
    "method_family,method,window_scorer,seed,episode_aggregation,threshold_source,"
    "auroc,auprc,f1,precision,recall,balanced_accuracy,fpr_at_95_tpr,"
    "evaluation_episode_count,positive_episode_count,negative_episode_count,"
    "auroc_ci_lower,auroc_ci_upper,f1_ci_lower,f1_ci_upper\n"
)


def write_comparison(path: Path, rows: list[str]) -> None:
    path.write_text(HEADER + "".join(rows), encoding="utf-8")


def test_summarize_selection_ranks_by_metrics_and_preserves_axes(
    tmp_path: Path,
) -> None:
    comparison = tmp_path / "comparison.csv"
    write_comparison(
        comparison,
        [
            "lewm,lewm,lewm_l2_max,44,mean,calibration_normal_p95,"
            "0.7159,0.8026,0.7143,0.75,0.6818,0.6326,0.75,"
            "34,22,12,0.5349,0.8770,0.5854,0.8293\n",
            "baseline,feature_distance,feature_distance,,top2_mean,"
            "calibration_normal_p95,"
            "0.6136,0.7310,0.1600,0.6667,0.0909,0.5038,0.8333,"
            "34,22,12,0.4636,0.7545,0,0.3575\n",
            "lewm,lewm,lewm_l2_max,44,max,calibration_normal_p95,"
            "0.6174,0.7299,0.6500,0.65,0.65,0.55,0.9167,"
            "34,22,12,0.4014,0.8179,0.4516,0.8\n",
        ],
    )

    rows = load_comparison_rows(comparison)
    summary = summarize_selection(rows, top_k=2)

    assert summary["row_count"] == 3
    assert summary["best_by_metric"]["auroc"]["window_scorer"] == "lewm_l2_max"
    assert summary["best_by_metric"]["auroc"]["episode_aggregation"] == "mean"
    assert summary["best_by_metric"]["auroc"]["auroc"] == pytest.approx(0.7159)
    assert summary["top_by_metric"]["auroc"][1]["episode_aggregation"] == "max"
    assert summary["axis_guardrail"] == (
        "window_scorer and episode_aggregation are separate axes; "
        "lewm_l2_max is a window scorer, not episode-level max aggregation."
    )


def test_render_markdown_names_window_and_episode_axes(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.csv"
    write_comparison(
        comparison,
        [
            "lewm,lewm,lewm_l2_max,44,mean,calibration_normal_p95,"
            "0.7159,0.8026,0.7143,0.75,0.6818,0.6326,0.75,"
            "34,22,12,0.5349,0.8770,0.5854,0.8293\n",
        ],
    )

    markdown = render_markdown(
        summarize_selection(load_comparison_rows(comparison), top_k=1),
        title="Synthetic TempGlitch Audit",
    )

    assert "# Synthetic TempGlitch Audit" in markdown
    assert "`lewm_l2_max`" in markdown
    assert "episode `mean`" in markdown
    assert "window scorer" in markdown


def test_missing_required_column_fails_closed(tmp_path: Path) -> None:
    comparison = tmp_path / "bad.csv"
    comparison.write_text("method,auroc\nlewm,0.5\n", encoding="utf-8")

    with pytest.raises(SelectionSummaryError, match="missing required column"):
        load_comparison_rows(comparison)


def test_non_finite_metric_fails_closed(tmp_path: Path) -> None:
    comparison = tmp_path / "bad.csv"
    write_comparison(
        comparison,
        [
            "lewm,lewm,lewm_l2_max,44,mean,calibration_normal_p95,"
            "nan,0.8026,0.7143,0.75,0.6818,0.6326,0.75,"
            "34,22,12,0.5349,0.8770,0.5854,0.8293\n",
        ],
    )

    with pytest.raises(SelectionSummaryError, match="non-finite metric"):
        load_comparison_rows(comparison)


def test_empty_csv_fails_closed(tmp_path: Path) -> None:
    comparison = tmp_path / "empty.csv"
    write_comparison(comparison, [])

    with pytest.raises(SelectionSummaryError, match="no rows"):
        load_comparison_rows(comparison)


def test_locked_test_metadata_fails_closed(tmp_path: Path) -> None:
    metadata = tmp_path / "metrics.json"
    metadata.write_text(json.dumps({"locked_test_scored": True}), encoding="utf-8")

    with pytest.raises(SelectionSummaryError, match="locked_test_scored"):
        load_safety_metadata(metadata)
