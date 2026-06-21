"""Regression tests for the R5-WOB Kaggle failure: calibration episode count mismatch.

The Kaggle run failed at baseline_scores with:
    ValueError: Canonical Gate 7 manifest has an invalid calibration episode count: 12.

Root cause: run_gate8_baselines_from_lance.run_gate8_baselines() called
validate_manifest_rows(manifest_rows) without expected_calibration_episode_count,
so it used the TempGlitch default of 2. The WOB expansion protocol has 12 calibration
episodes.

Fix: added _WOB_CALIBRATION_EPISODE_COUNT = 12 constant and passed it explicitly.
"""

from __future__ import annotations

import inspect

import pytest

from glitch_detection.lewm_lance_eval import validate_manifest_rows
from scripts.run_gate8_baselines_from_lance import (
    _WOB_CALIBRATION_EPISODE_COUNT,
    run_gate8_baselines,
)

_N_WOB_CALIBRATION_EPISODES = 12
_N_WOB_EVALUATION_BUGGY = 60


def _make_wob_manifest_rows() -> list[dict[str, str]]:
    """Build a minimal WOB expansion canonical manifest fixture.

    12 calibration_normal episodes (normal label) and 60 evaluation_buggy rows
    (buggy label), matching the shape of wob_expansion_eval_manifest.csv.
    """
    rows: list[dict[str, str]] = []
    # 12 calibration_normal episodes, 1 window each
    for ep_index in range(_N_WOB_CALIBRATION_EPISODES):
        rows.append(
            {
                "window_id": f"calib_ep{ep_index:02d}_w0",
                "source_episode_id": f"wob_normal_ep{ep_index:02d}",
                "dataset_name": "normal_validation",
                "dataset_fingerprint": "aabbcc",
                "dataset_window_index": "0",
                "source": "wob-normal",
                "pair_id": f"pair{ep_index:02d}",
                "category": "rendering",
                "label": "Normal",
                "split": "validation",
                "action_mode": "zero_action",
                "evaluation_role": "calibration_normal",
            }
        )
    # 60 evaluation_buggy rows, 1 window each
    for bug_index in range(_N_WOB_EVALUATION_BUGGY):
        rows.append(
            {
                "window_id": f"buggy_ep{bug_index:02d}_w0",
                "source_episode_id": f"wob_buggy_ep{bug_index:02d}",
                "dataset_name": "buggy_probe",
                "dataset_fingerprint": "ddeeff",
                "dataset_window_index": "0",
                "source": "wob-buggy",
                "pair_id": f"pair_b{bug_index:02d}",
                "category": "rendering",
                "label": "Buggy",
                "split": "validation",
                "action_mode": "zero_action",
                "evaluation_role": "evaluation",
            }
        )
    return rows


class TestWobCalibrationEpisodeCountConstant:
    def test_wob_calibration_episode_count_constant_is_12(self):
        assert _WOB_CALIBRATION_EPISODE_COUNT == 12

    def test_run_gate8_baselines_passes_wob_count_not_tempglitch_default(self):
        """Prove the call site no longer uses the bare default of 2."""
        source = inspect.getsource(run_gate8_baselines)
        assert "expected_calibration_episode_count=_WOB_CALIBRATION_EPISODE_COUNT" in source, (
            "run_gate8_baselines must pass _WOB_CALIBRATION_EPISODE_COUNT to "
            "validate_manifest_rows, not the TempGlitch default of 2."
        )

    def test_run_gate8_baselines_does_not_use_bare_default_of_2(self):
        """Validate there is no bare validate_manifest_rows(manifest_rows) call."""
        source = inspect.getsource(run_gate8_baselines)
        assert "validate_manifest_rows(manifest_rows)" not in source, (
            "validate_manifest_rows must always be called with an explicit "
            "expected_calibration_episode_count for the WOB protocol."
        )


class TestValidateManifestRowsWobCalibrationCount:
    def test_wob_manifest_12_calibration_episodes_is_accepted(self):
        rows = _make_wob_manifest_rows()
        validate_manifest_rows(rows, expected_calibration_episode_count=12)

    def test_wob_manifest_rejects_tempglitch_default_of_2(self):
        """This reproduces the exact Kaggle failure mode."""
        rows = _make_wob_manifest_rows()
        with pytest.raises(ValueError, match="12"):
            validate_manifest_rows(rows, expected_calibration_episode_count=2)

    def test_wob_manifest_rejects_wrong_count_of_1(self):
        rows = _make_wob_manifest_rows()
        with pytest.raises(ValueError, match="12"):
            validate_manifest_rows(rows, expected_calibration_episode_count=1)

    def test_wob_manifest_rejects_wrong_count_of_11(self):
        rows = _make_wob_manifest_rows()
        with pytest.raises(ValueError, match="12"):
            validate_manifest_rows(rows, expected_calibration_episode_count=11)

    def test_wob_manifest_has_correct_total_row_count(self):
        rows = _make_wob_manifest_rows()
        assert len(rows) == _N_WOB_CALIBRATION_EPISODES + _N_WOB_EVALUATION_BUGGY == 72

    def test_wob_manifest_all_window_ids_are_unique(self):
        rows = _make_wob_manifest_rows()
        window_ids = [r["window_id"] for r in rows]
        assert len(window_ids) == len(set(window_ids))

    def test_wob_manifest_calibration_rows_have_normal_label(self):
        rows = _make_wob_manifest_rows()
        for row in rows:
            if row["evaluation_role"] == "calibration_normal":
                assert row["label"].lower() == "normal"

    def test_wob_manifest_evaluation_buggy_rows_have_buggy_label(self):
        rows = _make_wob_manifest_rows()
        for row in rows:
            if row["evaluation_role"] == "evaluation":
                assert row["label"].lower() == "buggy"

    def test_wob_manifest_no_locked_test_rows(self):
        rows = _make_wob_manifest_rows()
        for row in rows:
            assert "locked" not in row["split"].lower()
            assert row["split"].lower() != "test"

    def test_wob_manifest_exactly_12_unique_calibration_source_episode_ids(self):
        rows = _make_wob_manifest_rows()
        calib_eps = {
            r["source_episode_id"] for r in rows if r["evaluation_role"] == "calibration_normal"
        }
        assert len(calib_eps) == 12

    def test_11_calibration_episodes_triggers_kaggle_error_message(self):
        """Verify the exact error message shape from the Kaggle failure."""
        rows = _make_wob_manifest_rows()
        rows_11 = [r for r in rows if r["evaluation_role"] != "calibration_normal"]
        for ep_index in range(11):
            rows_11.append(
                {
                    "window_id": f"calib_11_ep{ep_index:02d}_w0",
                    "source_episode_id": f"ep11_{ep_index:02d}",
                    "dataset_name": "normal_validation",
                    "dataset_fingerprint": "aabbcc",
                    "dataset_window_index": "0",
                    "source": "wob-normal",
                    "pair_id": f"pair11_{ep_index:02d}",
                    "category": "rendering",
                    "label": "Normal",
                    "split": "validation",
                    "action_mode": "zero_action",
                    "evaluation_role": "calibration_normal",
                }
            )
        with pytest.raises(ValueError, match="invalid calibration episode count: 11"):
            validate_manifest_rows(rows_11, expected_calibration_episode_count=12)
