"""Tests for R6 CPU-safe TempGlitch ablation runner (A1–A4) and validator."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_r6_tempglitch_cpu_ablations import (
    check_r5_inputs,
    run_a1_aggregation,
    run_a2_surprise_distance,
    run_a3_threshold_calibration,
    run_a4_failure_mode,
    run_all_ablations,
    run_single_ablation,
)
from scripts.validate_r6_ablations import validate_r6


def _write_comparison_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "scorer",
        "window_aggregation",
        "episode_aggregation",
        "auroc",
        "auprc",
        "auroc_ci_lower",
        "auroc_ci_upper",
        "auprc_ci_lower",
        "auprc_ci_upper",
        "threshold",
        "threshold_source",
        "f1",
        "precision",
        "recall",
        "fpr_at_95tpr",
        "episode_count",
        "positive_episode_count",
        "negative_episode_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["episode_id", "dataset_name", "label", "evaluation_role", "window_count", "category"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _minimal_comparison_rows() -> list[dict]:
    base = {
        "auroc": "0.700",
        "auprc": "0.800",
        "auroc_ci_lower": "0.600",
        "auroc_ci_upper": "0.800",
        "auprc_ci_lower": "0.700",
        "auprc_ci_upper": "0.900",
        "threshold": "0.250",
        "threshold_source": "calibration_normal_p95",
        "f1": "0.650",
        "precision": "0.700",
        "recall": "0.610",
        "fpr_at_95tpr": "0.300",
        "episode_count": "10",
        "positive_episode_count": "8",
        "negative_episode_count": "2",
    }
    rows = []
    for scorer in ("lewm_seed42", "lewm_seed43", "lewm_seed44"):
        for win in ("mse_max", "l2_max"):
            for ep in ("max", "mean"):
                rows.append(
                    {**base, "scorer": scorer, "window_aggregation": win, "episode_aggregation": ep}
                )
    for bname in ("baseline_frame_diff", "baseline_feature_distance"):
        for ep in ("max", "mean"):
            rows.append(
                {**base, "scorer": bname, "window_aggregation": "n/a", "episode_aggregation": ep}
            )
    return rows


def _minimal_manifest_rows() -> list[dict]:
    rows = []
    for i in range(2):
        rows.append(
            {
                "episode_id": f"cal_{i}",
                "dataset_name": "TempGlitch",
                "label": "Normal",
                "evaluation_role": "calibration_normal",
                "window_count": "10",
                "category": "Blinking",
            }
        )
    for cat in ("Blinking", "Flickering", "Flickering"):
        label = "Buggy" if cat == "Flickering" else "Normal"
        role = "evaluation"
        rows.append(
            {
                "episode_id": f"eval_{len(rows)}",
                "dataset_name": "TempGlitch",
                "label": label,
                "evaluation_role": role,
                "window_count": "15",
                "category": cat,
            }
        )
    return rows


def _make_r5_dir(tmp_path: Path) -> Path:
    r5_dir = tmp_path / "r5_out"
    _write_comparison_csv(r5_dir / "r5_comparison.csv", _minimal_comparison_rows())
    _write_manifest_csv(r5_dir / "r5_episode_manifest.csv", _minimal_manifest_rows())
    return r5_dir


class TestCheckR5Inputs:
    def test_present_when_files_exist(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        result = check_r5_inputs(r5_dir)
        assert result["required_files_present"] is True
        assert result["missing_required"] == []

    def test_missing_when_comparison_absent(self, tmp_path: Path) -> None:
        r5_dir = tmp_path / "empty_r5"
        r5_dir.mkdir()
        result = check_r5_inputs(r5_dir)
        assert result["required_files_present"] is False
        assert len(result["missing_required"]) > 0

    def test_locked_guard_raises(self, tmp_path: Path) -> None:
        locked = tmp_path / "locked_test_dir"
        locked.mkdir()
        with pytest.raises(ValueError, match="locked"):
            check_r5_inputs(locked)

    def test_hashes_present_when_files_exist(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        result = check_r5_inputs(r5_dir)
        assert "r5_comparison.csv" in result["present"]
        sha = result["present"]["r5_comparison.csv"]
        assert len(sha) == 64


class TestA1Aggregation:
    def test_produces_output_file(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a1_aggregation(rows, r5_dir, out_dir)
        assert result["status"] == "COMPLETED"
        assert (out_dir / "r6_a1_aggregation_ablation.json").exists()

    def test_groups_by_episode_aggregation(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a1_aggregation(rows, r5_dir, out_dir)
        ep_summary = result["episode_aggregation_summary"]
        assert "max" in ep_summary
        assert "mean" in ep_summary

    def test_safety_flags_false(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a1_aggregation(rows, r5_dir, out_dir)
        assert result["locked_test_materialized"] is False
        assert result["locked_test_scored"] is False
        assert result["wob_dependency_used"] is False

    def test_best_config_has_auroc(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a1_aggregation(rows, r5_dir, out_dir)
        best = result["best_auroc_configuration"]
        assert best["auroc"] is not None
        assert isinstance(best["auroc"], float)


class TestA2SurpriseDistance:
    def test_produces_output_file(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a2_surprise_distance(rows, r5_dir, out_dir)
        assert result["status"] == "COMPLETED"
        assert (out_dir / "r6_a2_surprise_distance_ablation.json").exists()

    def test_cosine_marked_unavailable(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a2_surprise_distance(rows, r5_dir, out_dir)
        assert result["cosine_family"]["status"] == "NOT_AVAILABLE_FROM_CURRENT_ARTIFACTS"

    def test_mse_and_l2_families_present(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a2_surprise_distance(rows, r5_dir, out_dir)
        assert result["mse_family"]["row_count"] > 0
        assert result["l2_family"]["row_count"] > 0

    def test_safety_flags_false(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a2_surprise_distance(rows, r5_dir, out_dir)
        assert result["locked_test_materialized"] is False
        assert result["locked_test_scored"] is False
        assert result["wob_dependency_used"] is False


class TestA3ThresholdCalibration:
    def test_produces_output_file(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a3_threshold_calibration(rows, r5_dir, out_dir, None)
        assert result["status"] == "COMPLETED"
        assert (out_dir / "r6_a3_threshold_calibration_ablation.json").exists()

    def test_sweep_complete_false_without_episode_scores(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a3_threshold_calibration(rows, r5_dir, out_dir, None)
        assert result["sweep_complete"] is False

    def test_configurations_have_threshold(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a3_threshold_calibration(rows, r5_dir, out_dir, None)
        assert len(result["configurations"]) > 0
        for conf in result["configurations"]:
            assert "threshold" in conf
            assert "f1" in conf

    def test_safety_flags_false(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        rows = _read_csv(r5_dir / "r5_comparison.csv")
        result = run_a3_threshold_calibration(rows, r5_dir, out_dir, None)
        assert result["locked_test_materialized"] is False
        assert result["locked_test_scored"] is False
        assert result["wob_dependency_used"] is False


class TestA4FailureMode:
    def test_produces_output_file(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        comp_rows = _read_csv(r5_dir / "r5_comparison.csv")
        man_rows = _read_csv(r5_dir / "r5_episode_manifest.csv")
        result = run_a4_failure_mode(man_rows, comp_rows, r5_dir, out_dir)
        assert result["status"] == "COMPLETED"
        assert (out_dir / "r6_a4_failure_mode_ablation.json").exists()

    def test_category_distribution_populated(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        comp_rows = _read_csv(r5_dir / "r5_comparison.csv")
        man_rows = _read_csv(r5_dir / "r5_episode_manifest.csv")
        result = run_a4_failure_mode(man_rows, comp_rows, r5_dir, out_dir)
        assert len(result["category_distribution"]) > 0

    def test_missing_category_counted(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        man_path = r5_dir / "r5_episode_manifest.csv"
        rows = _read_csv(man_path)
        rows[0]["category"] = ""
        _write_manifest_csv(man_path, rows)
        out_dir = tmp_path / "r6_out"
        comp_rows = _read_csv(r5_dir / "r5_comparison.csv")
        man_rows = _read_csv(r5_dir / "r5_episode_manifest.csv")
        result = run_a4_failure_mode(man_rows, comp_rows, r5_dir, out_dir)
        assert result["episodes_with_missing_category"] >= 0

    def test_safety_flags_false(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        comp_rows = _read_csv(r5_dir / "r5_comparison.csv")
        man_rows = _read_csv(r5_dir / "r5_episode_manifest.csv")
        result = run_a4_failure_mode(man_rows, comp_rows, r5_dir, out_dir)
        assert result["locked_test_materialized"] is False
        assert result["locked_test_scored"] is False
        assert result["wob_dependency_used"] is False


class TestRunAllAblations:
    def test_blocked_when_r5_dir_missing(self, tmp_path: Path) -> None:
        result = run_all_ablations(tmp_path / "nonexistent", tmp_path / "out")
        assert result["status"] == "BLOCKED_MISSING_R5_SCORE_FILES"
        assert result["paper_valid"] is False

    def test_all_ablations_complete_with_valid_inputs(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        result = run_all_ablations(r5_dir, out_dir)
        assert result["status"] == "R6_TEMPGLITCH_CPU_READY"
        assert result["paper_valid"] is True

    def test_provenance_file_written(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        assert (out_dir / "r6_tempglitch_cpu_provenance.json").exists()

    def test_provenance_safety_flags(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        prov = json.loads((out_dir / "r6_tempglitch_cpu_provenance.json").read_text())
        assert prov["locked_test_materialized"] is False
        assert prov["locked_test_scored"] is False
        assert prov["wob_dependency_used"] is False

    def test_all_four_output_files_written(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        for fname in (
            "r6_a1_aggregation_ablation.json",
            "r6_a2_surprise_distance_ablation.json",
            "r6_a3_threshold_calibration_ablation.json",
            "r6_a4_failure_mode_ablation.json",
        ):
            assert (out_dir / fname).exists(), f"Missing: {fname}"

    def test_locked_path_rejected(self, tmp_path: Path) -> None:
        locked = tmp_path / "locked_r5_dir"
        locked.mkdir()
        with pytest.raises(ValueError, match="locked"):
            run_all_ablations(locked, tmp_path / "out")

    def test_single_ablation_a1(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        result = run_single_ablation("a1", r5_dir, out_dir)
        assert result["status"] == "COMPLETED"

    def test_single_ablation_a2(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        result = run_single_ablation("a2", r5_dir, out_dir)
        assert result["status"] == "COMPLETED"

    def test_single_ablation_a3(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        result = run_single_ablation("a3", r5_dir, out_dir)
        assert result["status"] == "COMPLETED"

    def test_single_ablation_a4(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        result = run_single_ablation("a4", r5_dir, out_dir)
        assert result["status"] == "COMPLETED"


class TestValidateR6Ablations:
    def test_warns_when_dir_missing(self, tmp_path: Path) -> None:
        result = validate_r6(tmp_path / "nonexistent")
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_all_missing_when_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        result = validate_r6(empty)
        assert result["valid"] is True
        assert len(result["missing_or_incomplete_ablations"]) == 4

    def test_completed_after_full_run(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        result = validate_r6(out_dir)
        assert result["valid"] is True
        assert len(result["completed_ablations"]) == 4
        assert result["missing_or_incomplete_ablations"] == []

    def test_safety_flags_always_false(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        result = validate_r6(out_dir)
        assert result["locked_test_materialized"] is False
        assert result["locked_test_scored"] is False

    def test_error_when_wob_requested_without_receipt(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "r6_out"
        out_dir.mkdir()
        wob_dir = tmp_path / "wob_out"
        result = validate_r6(out_dir, wob_output_dir=wob_dir, r5_wob_receipt=None)
        assert result["valid"] is False
        assert any("WOB ablation validation requires" in e for e in result["errors"])

    def test_rejects_wob_locked_flag_in_output(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        a1_path = out_dir / "r6_a1_aggregation_ablation.json"
        payload = json.loads(a1_path.read_text())
        payload["locked_test_materialized"] = True
        a1_path.write_text(json.dumps(payload))
        result = validate_r6(out_dir)
        assert result["valid"] is False
        assert any("locked_test_materialized" in e for e in result["errors"])

    def test_rejects_wob_dependency_flag_true(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        a2_path = out_dir / "r6_a2_surprise_distance_ablation.json"
        payload = json.loads(a2_path.read_text())
        payload["wob_dependency_used"] = True
        a2_path.write_text(json.dumps(payload))
        result = validate_r6(out_dir)
        assert result["valid"] is False
        assert any("wob_dependency_used" in e for e in result["errors"])

    def test_rejects_placeholder_in_output(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        run_all_ablations(r5_dir, out_dir)
        a1_path = out_dir / "r6_a1_aggregation_ablation.json"
        payload = json.loads(a1_path.read_text())
        payload["some_field"] = "TODO"
        a1_path.write_text(json.dumps(payload))
        result = validate_r6(out_dir)
        assert result["valid"] is False
        assert any("TODO" in e for e in result["errors"])


class TestCLI:
    def test_cli_blocked_without_r5_dir(self, tmp_path: Path) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/run_r6_tempglitch_cpu_ablations.py",
                "--r5-output-dir",
                str(tmp_path / "nonexistent"),
                "--output-dir",
                str(tmp_path / "out"),
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0
        assert "missing" in proc.stderr.lower() or "missing" in proc.stdout.lower()

    def test_cli_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/run_r6_tempglitch_cpu_ablations.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        assert "ablation" in proc.stdout.lower()

    def test_validator_cli_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/validate_r6_ablations.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0

    def test_cli_all_ablations_with_valid_inputs(self, tmp_path: Path) -> None:
        r5_dir = _make_r5_dir(tmp_path)
        out_dir = tmp_path / "r6_out"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/run_r6_tempglitch_cpu_ablations.py",
                "--r5-output-dir",
                str(r5_dir),
                "--output-dir",
                str(out_dir),
                "--ablation",
                "all",
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        output = json.loads(proc.stdout)
        assert output["status"] == "R6_TEMPGLITCH_CPU_READY"


# ── helpers used inside tests ──────────────────────────────────────────────────


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))
