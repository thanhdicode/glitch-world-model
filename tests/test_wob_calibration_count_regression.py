"""Regression tests for the R5-WOB Kaggle failure: calibration episode count mismatch.

The Kaggle run failed at baseline_scores with:
    ValueError: Canonical Gate 7 manifest has an invalid calibration episode count: 12.

Root cause: run_gate8_baselines_from_lance.run_gate8_baselines() called
validate_manifest_rows(manifest_rows) without expected_calibration_episode_count,
so it used the TempGlitch default of 2. The revised WOB binary protocol has 6
calibration episodes and 6 held-out normal evaluation episodes.

Fix: keep _WOB_CALIBRATION_EPISODE_COUNT protocol-specific and pass it explicitly.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

import scripts.run_gate8_baselines_from_lance as gate8_cli
from glitch_detection.lewm_lance_eval import MANIFEST_FIELDS, validate_manifest_rows, write_csv_rows
from scripts.run_gate8_baselines_from_lance import (
    _WOB_CALIBRATION_EPISODE_COUNT,
    run_gate8_baselines,
)

_N_WOB_CALIBRATION_EPISODES = 6
_N_WOB_EVALUATION_NORMAL = 6
_N_WOB_EVALUATION_BUGGY = 60


def _make_wob_manifest_rows() -> list[dict[str, str]]:
    """Build a minimal WOB expansion canonical manifest fixture.

    6 calibration_normal episodes, 6 evaluation_normal episodes, and 60
    evaluation_buggy rows, matching wob_expansion_eval_manifest.csv.
    """
    rows: list[dict[str, str]] = []
    # 6 calibration_normal episodes, 1 window each
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
    # 6 evaluation_normal episodes, 1 window each
    for ep_index in range(_N_WOB_EVALUATION_NORMAL):
        rows.append(
            {
                "window_id": f"eval_normal_ep{ep_index:02d}_w0",
                "source_episode_id": f"wob_eval_normal_ep{ep_index:02d}",
                "dataset_name": "normal_validation",
                "dataset_fingerprint": "aabbcc",
                "dataset_window_index": "0",
                "source": "wob-normal",
                "pair_id": f"pair_eval{ep_index:02d}",
                "category": "rendering",
                "label": "Normal",
                "split": "validation",
                "action_mode": "zero_action",
                "evaluation_role": "evaluation_normal",
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
                "evaluation_role": "evaluation_buggy",
            }
        )
    return rows


class TestWobCalibrationEpisodeCountConstant:
    def test_wob_calibration_episode_count_constant_is_6(self):
        assert _WOB_CALIBRATION_EPISODE_COUNT == 6

    def test_run_gate8_baselines_passes_wob_count_not_tempglitch_default(self):
        """Prove the call site still defaults to WOB while allowing protocol overrides."""
        signature = inspect.signature(run_gate8_baselines)
        assert (
            signature.parameters["expected_calibration_episode_count"].default
            == _WOB_CALIBRATION_EPISODE_COUNT
        )
        source = inspect.getsource(run_gate8_baselines)
        assert "expected_calibration_episode_count=expected_calibration_episode_count" in source, (
            "run_gate8_baselines must pass the protocol-specific expected "
            "calibration count to validate_manifest_rows."
        )

    def test_run_gate8_baselines_does_not_use_bare_default_of_2(self):
        """Validate there is no bare validate_manifest_rows(manifest_rows) call."""
        source = inspect.getsource(run_gate8_baselines)
        assert "validate_manifest_rows(manifest_rows)" not in source, (
            "validate_manifest_rows must always be called with an explicit "
            "expected_calibration_episode_count for the WOB protocol."
        )


class TestValidateManifestRowsWobCalibrationCount:
    def test_wob_manifest_6_calibration_episodes_is_accepted(self):
        rows = _make_wob_manifest_rows()
        validate_manifest_rows(
            rows,
            expected_calibration_episode_count=6,
            minimum_evaluation_normal_episode_count=1,
        )

    def test_wob_manifest_rejects_tempglitch_default_of_2(self):
        """This reproduces the exact Kaggle failure mode."""
        rows = _make_wob_manifest_rows()
        with pytest.raises(ValueError, match="6"):
            validate_manifest_rows(rows, expected_calibration_episode_count=2)

    def test_wob_manifest_rejects_wrong_count_of_1(self):
        rows = _make_wob_manifest_rows()
        with pytest.raises(ValueError, match="6"):
            validate_manifest_rows(rows, expected_calibration_episode_count=1)

    def test_wob_manifest_rejects_wrong_count_of_5(self):
        rows = _make_wob_manifest_rows()
        with pytest.raises(ValueError, match="6"):
            validate_manifest_rows(rows, expected_calibration_episode_count=5)

    def test_wob_manifest_has_correct_total_row_count(self):
        rows = _make_wob_manifest_rows()
        assert (
            len(rows)
            == _N_WOB_CALIBRATION_EPISODES + _N_WOB_EVALUATION_NORMAL + _N_WOB_EVALUATION_BUGGY
            == 72
        )

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
            if row["evaluation_role"] == "evaluation_buggy":
                assert row["label"].lower() == "buggy"

    def test_wob_manifest_evaluation_normal_rows_have_normal_label(self):
        rows = _make_wob_manifest_rows()
        for row in rows:
            if row["evaluation_role"] == "evaluation_normal":
                assert row["label"].lower() == "normal"

    def test_wob_manifest_no_locked_test_rows(self):
        rows = _make_wob_manifest_rows()
        for row in rows:
            assert "locked" not in row["split"].lower()
            assert row["split"].lower() != "test"

    def test_wob_manifest_exactly_6_unique_calibration_source_episode_ids(self):
        rows = _make_wob_manifest_rows()
        calib_eps = {
            r["source_episode_id"] for r in rows if r["evaluation_role"] == "calibration_normal"
        }
        assert len(calib_eps) == 6

    def test_5_calibration_episodes_triggers_kaggle_error_message(self):
        """Verify the exact error message shape from the Kaggle failure."""
        rows = _make_wob_manifest_rows()
        rows_5 = [r for r in rows if r["evaluation_role"] != "calibration_normal"]
        for ep_index in range(5):
            rows_5.append(
                {
                    "window_id": f"calib_5_ep{ep_index:02d}_w0",
                    "source_episode_id": f"ep5_{ep_index:02d}",
                    "dataset_name": "normal_validation",
                    "dataset_fingerprint": "aabbcc",
                    "dataset_window_index": "0",
                    "source": "wob-normal",
                    "pair_id": f"pair5_{ep_index:02d}",
                    "category": "rendering",
                    "label": "Normal",
                    "split": "validation",
                    "action_mode": "zero_action",
                    "evaluation_role": "calibration_normal",
                }
            )
        with pytest.raises(ValueError, match="invalid calibration episode count: 5"):
            validate_manifest_rows(rows_5, expected_calibration_episode_count=6)


def _make_tempglitch_r5_manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for ep_index in range(2):
        rows.append(
            {
                "window_id": f"temp_calib_ep{ep_index}_w0",
                "source_episode_id": f"temp_normal_ep{ep_index}",
                "dataset_name": "normal_validation",
                "dataset_fingerprint": "normal-sha",
                "dataset_window_index": str(ep_index),
                "source": f"temp_normal_ep{ep_index}",
                "pair_id": f"normal_pair_{ep_index}",
                "category": "Blinking",
                "label": "Normal",
                "split": "validation",
                "action_mode": "zero_action",
                "evaluation_role": "calibration_normal",
            }
        )
    rows.append(
        {
            "window_id": "temp_eval_normal_w0",
            "source_episode_id": "temp_normal_eval",
            "dataset_name": "normal_validation",
            "dataset_fingerprint": "normal-sha",
            "dataset_window_index": "2",
            "source": "temp_normal_eval",
            "pair_id": "normal_pair_eval",
            "category": "Blinking",
            "label": "Normal",
            "split": "validation",
            "action_mode": "zero_action",
            "evaluation_role": "evaluation",
        }
    )
    rows.append(
        {
            "window_id": "temp_eval_buggy_w0",
            "source_episode_id": "temp_buggy_eval",
            "dataset_name": "buggy_probe",
            "dataset_fingerprint": "buggy-sha",
            "dataset_window_index": "0",
            "source": "temp_buggy_eval",
            "pair_id": "buggy_pair_eval",
            "category": "Blinking",
            "label": "Buggy",
            "split": "validation",
            "action_mode": "zero_action",
            "evaluation_role": "evaluation",
        }
    )
    return rows


def test_run_gate8_baselines_accepts_tempglitch_r5_calibration_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    rows = _make_tempglitch_r5_manifest_rows()
    manifest_path = write_csv_rows(tmp_path / "r5_manifest.csv", rows, MANIFEST_FIELDS)

    monkeypatch.setattr(
        gate8_cli,
        "_validate_fingerprints",
        lambda manifest_rows, normal_lance, buggy_lance: {
            "normal_validation": "normal-sha",
            "buggy_probe": "buggy-sha",
        },
    )
    monkeypatch.setattr(
        gate8_cli, "_fit_train_centroid", lambda train_lance, batch_size: np.zeros(1)
    )

    def fake_score_target(dataset_path, manifest_rows, centroid, *, batch_size):
        return [
            {
                "window_id": row["window_id"],
                "frame_diff": "0.1",
                "feature_distance": "0.2",
            }
            for row in manifest_rows
        ]

    monkeypatch.setattr(gate8_cli, "_score_target", fake_score_target)
    monkeypatch.setattr(gate8_cli, "_git_sha", lambda: "fixture-sha")
    monkeypatch.setattr(gate8_cli, "runtime_provenance", lambda include_lewm: {"fixture": True})
    monkeypatch.setattr(
        gate8_cli.FingerprintBuilder,
        "inventory_sha256",
        staticmethod(lambda path: "train-sha"),
    )

    metadata = run_gate8_baselines(
        manifest_path=manifest_path,
        train_lance=tmp_path / "train.lance",
        normal_lance=tmp_path / "normal.lance",
        buggy_lance=tmp_path / "buggy.lance",
        output_dir=tmp_path / "out",
        expected_calibration_episode_count=2,
    )

    assert metadata["status"] == "gate8_scored"
    assert metadata["expected_calibration_episode_count"] == 2
