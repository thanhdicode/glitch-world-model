"""Tests for R5 identical-episode evaluation orchestration.

These tests cover:
- Episode manifest building from window manifest rows.
- Episode manifest validation (locked-test guard, empty/no-eval/homogeneity).
- Window-to-episode score aggregation (max/mean).
- LeWM window-score extraction (all four transition aggregations).
- Baseline window-score extraction.
- FPR@95TPR computation.
- Full R5 scorer evaluation (metrics + bootstrap CI).
- CLI smoke test (--help).
- Locked-test path rejection at all entry points.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from glitch_detection.lewm_r5_eval import (
    EpisodeRecord,
    aggregate_window_to_episode,
    build_episode_manifest,
    evaluate_r5_scorer,
    extract_baseline_window_scores,
    extract_lewm_window_scores,
    fpr_at_tpr,
    run_r5_episode_eval,
    validate_episode_manifest,
)


def _mrow(
    window_id: str,
    episode: str,
    label: str,
    role: str,
    dataset_name: str = "normal_validation",
    category: str = "Blinking",
) -> dict[str, str]:
    return {
        "window_id": window_id,
        "source_episode_id": episode,
        "label": label,
        "evaluation_role": role,
        "dataset_name": dataset_name,
        "category": category,
        "source": "test_source",
        "pair_id": "p1",
        "split": "validation",
        "action_mode": "zero_action",
        "dataset_fingerprint": "abc123",
        "dataset_window_index": "0",
    }


def _lewm_row(window_id: str, values: list[float]) -> dict[str, str]:
    fields = ["mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3"]
    return {"window_id": window_id, **{f: str(v) for f, v in zip(fields, values)}}


def _baseline_row(window_id: str, fd: float, feat: float) -> dict[str, str]:
    return {
        "window_id": window_id,
        "frame_diff": str(fd),
        "feature_distance": str(feat),
    }


def _minimal_manifest() -> list[dict[str, str]]:
    """Two calibration-normal windows + two evaluation windows (one normal, one buggy)."""
    return [
        _mrow("cal1", "ep_cal1", "Normal", "calibration_normal"),
        _mrow("cal2", "ep_cal2", "Normal", "calibration_normal"),
        _mrow("n1", "ep_normal_eval", "Normal", "evaluation"),
        _mrow("b1", "ep_buggy_eval", "Buggy", "evaluation", dataset_name="buggy_probe"),
    ]


class TestBuildEpisodeManifest:
    def test_groups_windows_by_episode(self):
        rows = [
            _mrow("w1", "ep_a", "Normal", "calibration_normal"),
            _mrow("w2", "ep_a", "Normal", "calibration_normal"),
            _mrow("w3", "ep_b", "Buggy", "evaluation", dataset_name="buggy_probe"),
        ]
        records = build_episode_manifest(rows)
        assert len(records) == 2
        assert records[0].episode_id == "ep_a"
        assert records[0].window_count == 2
        assert records[0].label == "normal"
        assert records[0].evaluation_role == "calibration_normal"
        assert records[1].episode_id == "ep_b"
        assert records[1].label == "buggy"
        assert records[1].evaluation_role == "evaluation"

    def test_episode_role_is_calibration_normal_if_any_window_is(self):
        rows = [
            _mrow("w1", "ep_x", "Normal", "calibration_normal"),
            _mrow("w2", "ep_x", "Normal", "evaluation"),
        ]
        records = build_episode_manifest(rows)
        assert records[0].evaluation_role == "calibration_normal"

    def test_rejects_mixed_labels_within_episode(self):
        rows = [
            _mrow("w1", "ep_mixed", "Normal", "evaluation"),
            _mrow("w2", "ep_mixed", "Buggy", "evaluation", dataset_name="buggy_probe"),
        ]
        with pytest.raises(ValueError, match="mixed labels"):
            build_episode_manifest(rows)

    def test_rejects_buggy_episode_as_calibration_normal(self):
        rows = [
            _mrow("w1", "ep_bad", "Buggy", "calibration_normal", dataset_name="buggy_probe"),
        ]
        with pytest.raises(ValueError, match="calibration_normal"):
            build_episode_manifest(rows)

    def test_sorted_by_episode_id(self):
        rows = [
            _mrow("w1", "zzz", "Normal", "evaluation"),
            _mrow("w2", "aaa", "Normal", "evaluation"),
        ]
        records = build_episode_manifest(rows)
        assert [r.episode_id for r in records] == ["aaa", "zzz"]


class TestValidateEpisodeManifest:
    def test_accepts_valid_manifest(self):
        rows = _minimal_manifest()
        records = build_episode_manifest(rows)
        validate_episode_manifest(records)

    def test_rejects_empty_manifest(self):
        with pytest.raises(ValueError, match="empty"):
            validate_episode_manifest([])

    def test_rejects_no_calibration_episodes(self):
        records = [
            EpisodeRecord("ep_n", "ds", "normal", "evaluation", 1, "Blinking"),
            EpisodeRecord("ep_b", "ds", "buggy", "evaluation", 1, "Blinking"),
        ]
        with pytest.raises(ValueError, match="calibration_normal"):
            validate_episode_manifest(records)

    def test_rejects_no_evaluation_episodes(self):
        records = [
            EpisodeRecord("ep_cal", "ds", "normal", "calibration_normal", 2, "Blinking"),
        ]
        with pytest.raises(ValueError, match="evaluation episodes"):
            validate_episode_manifest(records)

    def test_rejects_evaluation_without_buggy(self):
        records = [
            EpisodeRecord("cal", "ds", "normal", "calibration_normal", 1, "c"),
            EpisodeRecord("eval_n", "ds", "normal", "evaluation", 1, "c"),
        ]
        with pytest.raises(ValueError, match="buggy"):
            validate_episode_manifest(records)

    def test_rejects_locked_episode_id(self):
        records = [
            EpisodeRecord("locked_ep", "ds", "normal", "calibration_normal", 1, "c"),
            EpisodeRecord("ep_n", "ds", "normal", "evaluation", 1, "c"),
            EpisodeRecord("ep_b", "ds", "buggy", "evaluation", 1, "c"),
        ]
        with pytest.raises(ValueError, match="locked"):
            validate_episode_manifest(records)


class TestAggregateWindowToEpisode:
    def test_max_aggregation_picks_episode_maximum(self):
        rows = _minimal_manifest() + [
            _mrow("b2", "ep_buggy_eval", "Buggy", "evaluation", dataset_name="buggy_probe")
        ]
        records = build_episode_manifest(rows)
        window_scores = {"cal1": 0.1, "cal2": 0.3, "n1": 0.5, "b1": 0.7, "b2": 0.9}
        episode_scores = aggregate_window_to_episode(records, rows, window_scores, "max")
        assert episode_scores["ep_buggy_eval"] == pytest.approx(0.9)
        assert episode_scores["ep_cal1"] == pytest.approx(0.1)

    def test_mean_aggregation_averages_episode_windows(self):
        rows = [
            _mrow("w1", "ep_a", "Normal", "evaluation"),
            _mrow("w2", "ep_a", "Normal", "evaluation"),
            _mrow("w3", "ep_b", "Buggy", "evaluation", dataset_name="buggy_probe"),
        ]
        records = build_episode_manifest(rows)
        window_scores = {"w1": 0.2, "w2": 0.4, "w3": 0.9}
        episode_scores = aggregate_window_to_episode(records, rows, window_scores, "mean")
        assert episode_scores["ep_a"] == pytest.approx(0.3)

    def test_rejects_unsupported_aggregation(self):
        rows = _minimal_manifest()
        records = build_episode_manifest(rows)
        with pytest.raises(ValueError, match="Unsupported episode aggregation"):
            aggregate_window_to_episode(records, rows, {}, "p95")

    def test_rejects_missing_window_score(self):
        rows = _minimal_manifest()
        records = build_episode_manifest(rows)
        partial_scores = {"cal1": 0.1}
        with pytest.raises(ValueError, match="Missing score"):
            aggregate_window_to_episode(records, rows, partial_scores, "max")


class TestExtractWindowScores:
    def test_lewm_mse_max_picks_maximum_mse_transition(self):
        row = _lewm_row("w1", [1.0, 5.0, 2.0, 3.0, 4.0, 6.0])
        result = extract_lewm_window_scores([row], "mse_max")
        assert result["w1"] == pytest.approx(5.0)

    def test_lewm_mse_mean_averages_mse_transitions(self):
        row = _lewm_row("w1", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        result = extract_lewm_window_scores([row], "mse_mean")
        assert result["w1"] == pytest.approx(2.0)

    def test_lewm_l2_max_picks_maximum_l2_transition(self):
        row = _lewm_row("w1", [1.0, 2.0, 3.0, 3.0, 7.0, 4.0])
        result = extract_lewm_window_scores([row], "l2_max")
        assert result["w1"] == pytest.approx(7.0)

    def test_lewm_l2_mean_averages_l2_transitions(self):
        row = _lewm_row("w1", [0.0, 0.0, 0.0, 2.0, 4.0, 6.0])
        result = extract_lewm_window_scores([row], "l2_mean")
        assert result["w1"] == pytest.approx(4.0)

    def test_baseline_frame_diff_extraction(self):
        rows = [_baseline_row("w1", 0.3, 1.2), _baseline_row("w2", 0.7, 0.5)]
        result = extract_baseline_window_scores(rows, "frame_diff")
        assert result == {"w1": pytest.approx(0.3), "w2": pytest.approx(0.7)}

    def test_baseline_feature_distance_extraction(self):
        rows = [_baseline_row("w1", 0.3, 1.2)]
        result = extract_baseline_window_scores(rows, "feature_distance")
        assert result["w1"] == pytest.approx(1.2)

    def test_rejects_unsupported_lewm_aggregation(self):
        row = _lewm_row("w1", [1.0] * 6)
        with pytest.raises(ValueError, match="Unsupported LeWM window aggregation"):
            extract_lewm_window_scores([row], "bad_agg")


class TestFprAtTpr:
    def test_perfect_separation_fpr_is_zero(self):
        labels = [0, 0, 1, 1]
        scores = [0.1, 0.2, 0.8, 0.9]
        assert fpr_at_tpr(labels, scores, target_tpr=0.95) == pytest.approx(0.0)

    def test_no_positives_returns_none(self):
        labels = [0, 0]
        scores = [0.1, 0.2]
        assert fpr_at_tpr(labels, scores) is None

    def test_no_negatives_returns_none(self):
        labels = [1, 1]
        scores = [0.1, 0.2]
        assert fpr_at_tpr(labels, scores) is None

    def test_target_tpr_achievable_at_fpr_greater_than_zero(self):
        labels = [0, 0, 1, 1]
        scores = [0.5, 0.6, 0.4, 0.7]
        fpr = fpr_at_tpr(labels, scores, target_tpr=1.0)
        assert fpr is not None
        assert 0.0 <= fpr <= 1.0


class TestEvaluateR5Scorer:
    def _make_episode_manifest_and_scores(self) -> tuple[list[EpisodeRecord], dict[str, float]]:
        records = [
            EpisodeRecord("cal1", "ds", "normal", "calibration_normal", 3, "Blinking"),
            EpisodeRecord("cal2", "ds", "normal", "calibration_normal", 2, "Blinking"),
            EpisodeRecord("eval_n1", "ds", "normal", "evaluation", 2, "Blinking"),
            EpisodeRecord("eval_n2", "ds", "normal", "evaluation", 2, "Blinking"),
            EpisodeRecord("eval_b1", "ds", "buggy", "evaluation", 3, "Blinking"),
            EpisodeRecord("eval_b2", "ds", "buggy", "evaluation", 3, "Blinking"),
        ]
        scores = {
            "cal1": 0.1,
            "cal2": 0.2,
            "eval_n1": 0.15,
            "eval_n2": 0.18,
            "eval_b1": 0.8,
            "eval_b2": 0.9,
        }
        return records, scores

    def test_primary_metrics_are_auroc_and_auprc(self):
        records, scores = self._make_episode_manifest_and_scores()
        result = evaluate_r5_scorer(
            "test_scorer",
            window_aggregation="mse_max",
            episode_aggregation="max",
            episode_records=records,
            episode_scores=scores,
            n_bootstrap=20,
            bootstrap_seed=42,
        )
        assert result["auroc"] == pytest.approx(1.0)
        assert result["auprc"] == pytest.approx(1.0)
        assert result["scorer"] == "test_scorer"
        assert result["threshold_source"] == "calibration_normal_p95"

    def test_f1_and_fpr_are_secondary_metrics(self):
        records, scores = self._make_episode_manifest_and_scores()
        result = evaluate_r5_scorer(
            "test_scorer",
            window_aggregation="mse_max",
            episode_aggregation="max",
            episode_records=records,
            episode_scores=scores,
            n_bootstrap=20,
            bootstrap_seed=42,
        )
        assert "f1" in result
        assert "fpr_at_95tpr" in result

    def test_bootstrap_ci_bounds_are_present(self):
        records, scores = self._make_episode_manifest_and_scores()
        result = evaluate_r5_scorer(
            "test_scorer",
            window_aggregation="mse_max",
            episode_aggregation="max",
            episode_records=records,
            episode_scores=scores,
            n_bootstrap=50,
            bootstrap_seed=42,
        )
        assert result["auroc_ci_lower"] is not None
        assert result["auroc_ci_upper"] is not None
        assert result["auroc_ci_lower"] <= result["auroc"]
        assert result["auroc_ci_upper"] >= result["auroc"]

    def test_episode_counts_are_evaluation_only(self):
        records, scores = self._make_episode_manifest_and_scores()
        result = evaluate_r5_scorer(
            "test_scorer",
            window_aggregation="mse_max",
            episode_aggregation="max",
            episode_records=records,
            episode_scores=scores,
            n_bootstrap=10,
            bootstrap_seed=0,
        )
        assert result["episode_count"] == 4
        assert result["positive_episode_count"] == 2
        assert result["negative_episode_count"] == 2

    def test_rejects_evaluation_without_both_classes(self):
        records = [
            EpisodeRecord("cal1", "ds", "normal", "calibration_normal", 1, "c"),
            EpisodeRecord("n1", "ds", "normal", "evaluation", 1, "c"),
        ]
        scores = {"cal1": 0.1, "n1": 0.2}
        with pytest.raises(ValueError, match="both normal and buggy"):
            evaluate_r5_scorer(
                "bad",
                window_aggregation="mse_max",
                episode_aggregation="max",
                episode_records=records,
                episode_scores=scores,
                n_bootstrap=5,
                bootstrap_seed=0,
            )

    def test_calibration_threshold_uses_p95_of_calibration_episodes(self):
        records = [
            EpisodeRecord("cal1", "ds", "normal", "calibration_normal", 1, "c"),
            EpisodeRecord("cal2", "ds", "normal", "calibration_normal", 1, "c"),
            EpisodeRecord("eval_n", "ds", "normal", "evaluation", 1, "c"),
            EpisodeRecord("eval_b", "ds", "buggy", "evaluation", 1, "c"),
        ]
        scores = {"cal1": 0.1, "cal2": 0.3, "eval_n": 0.2, "eval_b": 0.9}
        result = evaluate_r5_scorer(
            "t",
            window_aggregation="mse_max",
            episode_aggregation="max",
            episode_records=records,
            episode_scores=scores,
            n_bootstrap=10,
            bootstrap_seed=0,
        )
        assert result["threshold"] == pytest.approx(0.29)


class TestRunR5EpisodeEval:
    def _write_manifest_csv(self, tmp_path: Path, rows: list[dict[str, str]]) -> Path:
        import csv

        path = tmp_path / "window_manifest.csv"
        fieldnames = list(rows[0].keys()) if rows else []
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _write_lewm_scores_csv(self, tmp_path: Path, rows: list[dict[str, str]], name: str) -> Path:
        import csv

        path = tmp_path / f"lewm_scores_{name}.csv"
        fieldnames = list(rows[0].keys()) if rows else []
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _write_baseline_csv(self, tmp_path: Path, rows: list[dict[str, str]]) -> Path:
        import csv

        path = tmp_path / "baseline_scores.csv"
        fieldnames = list(rows[0].keys()) if rows else []
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_full_run_produces_expected_output_files(self, tmp_path: Path):
        manifest_rows = _minimal_manifest()
        lewm_rows = [
            _lewm_row(r["window_id"], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]) for r in manifest_rows
        ]
        baseline_rows = [_baseline_row(r["window_id"], 0.1, 0.2) for r in manifest_rows]

        manifest_path = self._write_manifest_csv(tmp_path, manifest_rows)
        lewm_path = self._write_lewm_scores_csv(tmp_path, lewm_rows, "seed42")
        baseline_path = self._write_baseline_csv(tmp_path, baseline_rows)

        result = run_r5_episode_eval(
            manifest_path=manifest_path,
            lewm_scores_by_name={"seed42": lewm_path},
            baseline_scores_path=baseline_path,
            output_dir=tmp_path / "r5_out",
            lewm_window_aggregations=("mse_max",),
            episode_aggregations=("max",),
            n_bootstrap=20,
            bootstrap_seed=0,
        )

        assert result["status"] == "r5_episode_evaluated"
        assert result["locked_test_materialized"] is False
        assert result["locked_test_scored"] is False
        assert (tmp_path / "r5_out" / "r5_episode_eval.json").is_file()
        assert (tmp_path / "r5_out" / "r5_episode_manifest.csv").is_file()
        assert (tmp_path / "r5_out" / "r5_comparison.csv").is_file()
        assert result["episode_counts"]["total"] == 4
        assert result["episode_counts"]["calibration_normal"] == 2
        assert result["episode_counts"]["evaluation_buggy"] == 1

    def test_result_json_is_valid_json(self, tmp_path: Path):
        manifest_rows = _minimal_manifest()
        lewm_rows = [_lewm_row(r["window_id"], [0.5] * 6) for r in manifest_rows]
        baseline_rows = [_baseline_row(r["window_id"], 0.3, 0.4) for r in manifest_rows]

        manifest_path = self._write_manifest_csv(tmp_path, manifest_rows)
        lewm_path = self._write_lewm_scores_csv(tmp_path, lewm_rows, "seed43")
        baseline_path = self._write_baseline_csv(tmp_path, baseline_rows)

        result = run_r5_episode_eval(
            manifest_path=manifest_path,
            lewm_scores_by_name={"seed43": lewm_path},
            baseline_scores_path=baseline_path,
            output_dir=tmp_path / "r5_json_check",
            lewm_window_aggregations=("mse_max",),
            episode_aggregations=("max",),
            n_bootstrap=10,
            bootstrap_seed=0,
        )

        json_path = Path(result["results_path"])
        parsed = json.loads(json_path.read_text(encoding="utf-8"))
        assert parsed["status"] == "r5_episode_evaluated"

    def test_rejects_locked_manifest_path(self, tmp_path: Path):
        locked = tmp_path / "locked_window_manifest.csv"
        locked.write_text("", encoding="utf-8")
        baseline = tmp_path / "baseline_scores.csv"
        baseline.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="locked"):
            run_r5_episode_eval(
                manifest_path=locked,
                lewm_scores_by_name={},
                baseline_scores_path=baseline,
                output_dir=tmp_path / "out",
            )

    def test_rejects_locked_baseline_path(self, tmp_path: Path):
        manifest = tmp_path / "window_manifest.csv"
        manifest.write_text("", encoding="utf-8")
        locked = tmp_path / "locked_baseline_scores.csv"
        locked.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="locked"):
            run_r5_episode_eval(
                manifest_path=manifest,
                lewm_scores_by_name={},
                baseline_scores_path=locked,
                output_dir=tmp_path / "out",
            )

    def test_rejects_locked_lewm_scores_path(self, tmp_path: Path):
        manifest = tmp_path / "window_manifest.csv"
        manifest.write_text("", encoding="utf-8")
        baseline = tmp_path / "baseline_scores.csv"
        baseline.write_text("", encoding="utf-8")
        locked_lewm = tmp_path / "locked_lewm_scores.csv"
        locked_lewm.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="locked"):
            run_r5_episode_eval(
                manifest_path=manifest,
                lewm_scores_by_name={"seed42": locked_lewm},
                baseline_scores_path=baseline,
                output_dir=tmp_path / "out",
            )


class TestCLISmokeTest:
    def test_cli_help_exits_cleanly(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_r5_identical_episode_eval.py", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "episode" in result.stdout.lower()

    def test_cli_named_path_parsing_rejects_missing_colon(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_r5_identical_episode_eval.py",
                "--manifest",
                "some_manifest.csv",
                "--lewm-scores",
                "bad_format_no_colon",
                "--baseline-scores",
                "baseline.csv",
                "--output-dir",
                "out/",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
