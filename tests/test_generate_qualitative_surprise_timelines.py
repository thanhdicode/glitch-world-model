from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.generate_qualitative_surprise_timelines import (
    build_episode_timelines,
    generate_qualitative_surprise_timelines,
    lewm_window_score_from_row,
    select_best_comparison_row,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def test_select_best_comparison_row_prefers_highest_auroc_then_auprc():
    rows = [
        {"method_family": "lewm", "auroc": "0.71", "auprc": "0.80", "seed": "43"},
        {"method_family": "lewm", "auroc": "0.71", "auprc": "0.81", "seed": "42"},
        {"method_family": "baseline", "auroc": "0.99", "auprc": "0.99", "seed": ""},
    ]

    selected = select_best_comparison_row(rows)

    assert selected["seed"] == "42"
    assert selected["auprc"] == "0.81"


def test_lewm_window_score_from_row_matches_expected_aggregations():
    row = {
        "mse_t1": "1.0",
        "mse_t2": "4.0",
        "mse_t3": "9.0",
        "l2_t1": "2.0",
        "l2_t2": "8.0",
        "l2_t3": "10.0",
    }

    assert lewm_window_score_from_row(row, "lewm_mse_mean") == 14.0 / 3.0
    assert lewm_window_score_from_row(row, "lewm_mse_max") == 9.0
    assert lewm_window_score_from_row(row, "lewm_mse_top2_mean") == 6.5
    assert lewm_window_score_from_row(row, "lewm_l2_mean") == 20.0 / 3.0
    assert lewm_window_score_from_row(row, "lewm_l2_max") == 10.0
    assert lewm_window_score_from_row(row, "lewm_l2_top2_mean") == 9.0


def test_build_episode_timelines_orders_by_dataset_window_index():
    manifest_rows = [
        {
            "window_id": "b",
            "dataset_window_index": "2",
            "source_episode_id": "episode-1",
            "label": "Buggy",
            "evaluation_role": "evaluation",
            "category": "Blinking",
            "source": "episode-1",
        },
        {
            "window_id": "a",
            "dataset_window_index": "1",
            "source_episode_id": "episode-1",
            "label": "Buggy",
            "evaluation_role": "evaluation",
            "category": "Blinking",
            "source": "episode-1",
        },
    ]
    raw_rows = [
        {
            "window_id": "a",
            "mse_t1": "1",
            "mse_t2": "1",
            "mse_t3": "1",
            "l2_t1": "3",
            "l2_t2": "4",
            "l2_t3": "5",
        },
        {
            "window_id": "b",
            "mse_t1": "2",
            "mse_t2": "2",
            "mse_t3": "2",
            "l2_t1": "6",
            "l2_t2": "7",
            "l2_t3": "8",
        },
    ]

    timelines = build_episode_timelines(manifest_rows, raw_rows, window_scorer="lewm_l2_max")

    assert timelines["episode-1"].window_indices == (1, 2)
    assert timelines["episode-1"].scores == (5.0, 8.0)


def test_generate_qualitative_surprise_timelines_writes_receipt_and_plots(
    tmp_path: Path, monkeypatch
):
    comparison_csv = _write_csv(
        tmp_path / "followup_comparison.csv",
        [
            "method_family",
            "method",
            "window_scorer",
            "seed",
            "episode_aggregation",
            "raw_score_path",
            "threshold",
            "threshold_source",
            "auroc",
            "auprc",
        ],
        [
            {
                "method_family": "lewm",
                "method": "lewm",
                "window_scorer": "lewm_l2_max",
                "seed": "44",
                "episode_aggregation": "mean",
                "raw_score_path": "raw_scores.csv",
                "threshold": "0.5",
                "threshold_source": "calibration_normal_p95",
                "auroc": "0.9",
                "auprc": "0.8",
            }
        ],
    )
    episode_scores_csv = _write_csv(
        tmp_path / "followup_episode_scores.csv",
        [
            "method_family",
            "method",
            "window_scorer",
            "seed",
            "episode_aggregation",
            "source_episode_id",
            "source",
            "pair_id",
            "category",
            "label",
            "dataset_name",
            "evaluation_role",
            "window_count",
            "score",
        ],
        [
            {
                "method_family": "lewm",
                "method": "lewm",
                "window_scorer": "lewm_l2_max",
                "seed": "44",
                "episode_aggregation": "mean",
                "source_episode_id": "buggy-1",
                "source": "buggy-1",
                "pair_id": "pair-b",
                "category": "Blinking",
                "label": "Buggy",
                "dataset_name": "buggy_probe",
                "evaluation_role": "evaluation",
                "window_count": "2",
                "score": "0.9",
            },
            {
                "method_family": "lewm",
                "method": "lewm",
                "window_scorer": "lewm_l2_max",
                "seed": "44",
                "episode_aggregation": "mean",
                "source_episode_id": "normal-1",
                "source": "normal-1",
                "pair_id": "pair-n",
                "category": "Blinking",
                "label": "Normal",
                "dataset_name": "normal_validation",
                "evaluation_role": "evaluation",
                "window_count": "2",
                "score": "0.4",
            },
        ],
    )
    manifest_csv = _write_csv(
        tmp_path / "followup_manifest.csv",
        [
            "window_id",
            "dataset_window_index",
            "source",
            "source_episode_id",
            "pair_id",
            "category",
            "label",
            "dataset_name",
            "evaluation_role",
        ],
        [
            {
                "window_id": "w0",
                "dataset_window_index": "0",
                "source": "buggy-1",
                "source_episode_id": "buggy-1",
                "pair_id": "pair-b",
                "category": "Blinking",
                "label": "Buggy",
                "dataset_name": "buggy_probe",
                "evaluation_role": "evaluation",
            },
            {
                "window_id": "w1",
                "dataset_window_index": "1",
                "source": "buggy-1",
                "source_episode_id": "buggy-1",
                "pair_id": "pair-b",
                "category": "Blinking",
                "label": "Buggy",
                "dataset_name": "buggy_probe",
                "evaluation_role": "evaluation",
            },
            {
                "window_id": "w2",
                "dataset_window_index": "0",
                "source": "normal-1",
                "source_episode_id": "normal-1",
                "pair_id": "pair-n",
                "category": "Blinking",
                "label": "Normal",
                "dataset_name": "normal_validation",
                "evaluation_role": "evaluation",
            },
            {
                "window_id": "w3",
                "dataset_window_index": "1",
                "source": "normal-1",
                "source_episode_id": "normal-1",
                "pair_id": "pair-n",
                "category": "Blinking",
                "label": "Normal",
                "dataset_name": "normal_validation",
                "evaluation_role": "evaluation",
            },
        ],
    )
    raw_scores_csv = _write_csv(
        tmp_path / "raw_scores.csv",
        ["window_id", "mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3"],
        [
            {
                "window_id": "w0",
                "mse_t1": "1",
                "mse_t2": "1",
                "mse_t3": "1",
                "l2_t1": "1",
                "l2_t2": "2",
                "l2_t3": "3",
            },
            {
                "window_id": "w1",
                "mse_t1": "1",
                "mse_t2": "1",
                "mse_t3": "1",
                "l2_t1": "4",
                "l2_t2": "5",
                "l2_t3": "6",
            },
            {
                "window_id": "w2",
                "mse_t1": "1",
                "mse_t2": "1",
                "mse_t3": "1",
                "l2_t1": "2",
                "l2_t2": "2",
                "l2_t3": "2",
            },
            {
                "window_id": "w3",
                "mse_t1": "1",
                "mse_t2": "1",
                "mse_t3": "1",
                "l2_t1": "3",
                "l2_t2": "3",
                "l2_t3": "3",
            },
        ],
    )

    def fake_plot_series(values, output_path, **_kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes((",".join(str(v) for v in values)).encode("utf-8"))
        return output_path

    monkeypatch.setattr(
        "scripts.generate_qualitative_surprise_timelines.plot_series",
        fake_plot_series,
    )

    receipt = generate_qualitative_surprise_timelines(
        comparison_csv=comparison_csv,
        episode_scores_csv=episode_scores_csv,
        manifest_csv=manifest_csv,
        output_dir=tmp_path / "out",
        receipt_path=tmp_path / "out" / "receipt.json",
        max_buggy=1,
        max_normal=1,
    )

    assert receipt["temporal_metrics_claimed"] is False
    assert receipt["ground_truth_spans_available"] is False
    assert receipt["locked_test_used"] is False
    assert receipt["k4_required"] is False
    assert receipt["selected_config"]["raw_score_sha256"]
    assert receipt["plot_count"] == 2
    assert (tmp_path / "out" / "receipt.json").is_file()
    saved = json.loads((tmp_path / "out" / "receipt.json").read_text(encoding="utf-8"))
    assert saved["plot_count"] == 2
    assert raw_scores_csv.is_file()
