from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.run_tempglitch_followup_pair_disjoint as followup_cli
from glitch_detection.tempglitch_followup import (
    build_followup_episode_rows,
    build_followup_manifest_rows,
    evaluate_followup_configuration,
    validate_followup_manifest_rows,
    validate_tempglitch_followup_output,
)


def _manifest_row(
    window_id: str,
    episode_id: str,
    pair_id: str,
    label: str,
    role: str,
) -> dict[str, str]:
    return {
        "window_id": window_id,
        "dataset_name": "normal_validation" if label == "Normal" else "buggy_probe",
        "dataset_fingerprint": "fingerprint",
        "dataset_window_index": "0",
        "source": episode_id,
        "source_episode_id": episode_id,
        "pair_id": pair_id,
        "category": "Blinking",
        "label": label,
        "split": "validation",
        "action_mode": "zero_action",
        "evaluation_role": role,
    }


def _episode_row(
    *,
    method_family: str,
    method: str,
    window_scorer: str,
    seed: str,
    episode_aggregation: str,
    episode_id: str,
    pair_id: str,
    label: str,
    role: str,
    score: float,
) -> dict[str, str]:
    return {
        "method_family": method_family,
        "method": method,
        "window_scorer": window_scorer,
        "seed": seed,
        "episode_aggregation": episode_aggregation,
        "source_episode_id": episode_id,
        "source": episode_id,
        "pair_id": pair_id,
        "category": "Blinking",
        "label": label,
        "dataset_name": "normal_validation" if label == "Normal" else "buggy_probe",
        "evaluation_role": role,
        "window_count": "1",
        "score": str(score),
    }


def test_build_followup_manifest_retags_pair_disjoint_calibration():
    rows = [
        _manifest_row("w1", "cal-a", "pair/cal-a", "Normal", "calibration_normal"),
        _manifest_row("w2", "old-cal", "pair/old-cal", "Normal", "calibration_normal"),
        _manifest_row("w3", "eval-normal", "pair/eval-normal", "Normal", "evaluation"),
        _manifest_row("w4", "eval-buggy", "pair/eval-buggy", "Buggy", "evaluation"),
    ]

    followup_rows = build_followup_manifest_rows(
        rows,
        calibration_episode_ids=("cal-a", "eval-normal"),
        expected_evaluation_normal_count=1,
        expected_evaluation_buggy_count=1,
    )
    summary = validate_followup_manifest_rows(
        followup_rows,
        calibration_episode_ids=("cal-a", "eval-normal"),
        expected_evaluation_normal_count=1,
        expected_evaluation_buggy_count=1,
    )

    assert summary["calibration_episode_ids"] == ["cal-a", "eval-normal"]
    assert summary["role_overlap"]["pair_id_overlap"] == 0


def test_followup_helpers_accept_expanded_support_parameters():
    rows = [
        _manifest_row("w1", "cal-1", "pair/cal-1", "Normal", "evaluation"),
        _manifest_row("w2", "cal-2", "pair/cal-2", "Normal", "evaluation"),
        _manifest_row("w3", "eval-normal-1", "pair/eval-normal-1", "Normal", "evaluation"),
        _manifest_row("w4", "eval-normal-2", "pair/eval-normal-2", "Normal", "evaluation"),
        _manifest_row("w5", "eval-buggy-1", "pair/eval-buggy-1", "Buggy", "evaluation"),
        _manifest_row("w6", "eval-buggy-2", "pair/eval-buggy-2", "Buggy", "evaluation"),
    ]
    followup_rows = build_followup_manifest_rows(
        rows,
        calibration_episode_ids=("cal-1", "cal-2"),
        expected_evaluation_normal_count=2,
        expected_evaluation_buggy_count=2,
    )
    summary = validate_followup_manifest_rows(
        followup_rows,
        calibration_episode_ids=("cal-1", "cal-2"),
        expected_evaluation_normal_count=2,
        expected_evaluation_buggy_count=2,
    )
    assert summary["calibration_episode_count"] == 2
    assert summary["evaluation_normal_episode_count"] == 2
    assert summary["evaluation_buggy_episode_count"] == 2


def test_build_followup_episode_rows_preserves_support_per_config():
    rows = [
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="cal-a",
            pair_id="pair/cal-a",
            label="Normal",
            role="calibration_normal",
            score=0.1,
        ),
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="old-cal",
            pair_id="pair/old-cal",
            label="Normal",
            role="calibration_normal",
            score=0.2,
        ),
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="eval-normal",
            pair_id="pair/eval-normal",
            label="Normal",
            role="evaluation",
            score=0.3,
        ),
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="eval-buggy",
            pair_id="pair/eval-buggy",
            label="Buggy",
            role="evaluation",
            score=0.9,
        ),
    ]

    followup_rows = build_followup_episode_rows(
        rows,
        calibration_episode_ids=("cal-a", "eval-normal"),
        expected_evaluation_normal_count=1,
        expected_evaluation_buggy_count=1,
        expected_config_count=1,
    )

    assert {
        row["source_episode_id"]
        for row in followup_rows
        if row["evaluation_role"] == "calibration_normal"
    } == {
        "cal-a",
        "eval-normal",
    }
    assert {
        row["source_episode_id"] for row in followup_rows if row["evaluation_role"] == "evaluation"
    } == {
        "old-cal",
        "eval-buggy",
    }


def test_evaluate_followup_configuration_reports_pair_grouped_ci_and_balanced_accuracy():
    rows = [
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="cal-a",
            pair_id="pair/cal-a",
            label="Normal",
            role="calibration_normal",
            score=0.1,
        ),
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="cal-b",
            pair_id="pair/cal-b",
            label="Normal",
            role="calibration_normal",
            score=0.2,
        ),
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="eval-normal",
            pair_id="pair/eval-normal",
            label="Normal",
            role="evaluation",
            score=0.15,
        ),
        _episode_row(
            method_family="baseline",
            method="frame_diff",
            window_scorer="frame_diff",
            seed="",
            episode_aggregation="mean",
            episode_id="eval-buggy",
            pair_id="pair/eval-buggy",
            label="Buggy",
            role="evaluation",
            score=0.9,
        ),
    ]

    result = evaluate_followup_configuration(rows, n_bootstrap=20)

    assert result["threshold_source"] == "calibration_normal_p95"
    assert result["confidence_interval_group_key"] == "pair_id"
    assert result["metrics"]["balanced_accuracy"] == pytest.approx(1.0)


def test_parse_expected_support_accepts_four_counts():
    assert followup_cli.parse_expected_support("2,60,30,30") == ("2", "60", "30", "30")


def test_parse_expected_support_rejects_bad_shape():
    with pytest.raises(Exception):
        followup_cli.parse_expected_support("2,60,30")


def test_validate_followup_manifest_rows_requires_four_calibration_episodes_by_default():
    rows = [
        _manifest_row(
            "w1",
            "Godot_Blinking_Normal_106",
            "Blinking/pair-index:106",
            "Normal",
            "calibration_normal",
        ),
        _manifest_row(
            "w2",
            "Godot_Frozen_Animation_Platformer_Normal_107",
            "Frozen Animation/pair-index:107",
            "Normal",
            "calibration_normal",
        ),
        _manifest_row("w3", "eval-normal-a", "pair/eval-normal-a", "Normal", "evaluation"),
        _manifest_row("w4", "eval-normal-b", "pair/eval-normal-b", "Normal", "evaluation"),
        _manifest_row("w5", "eval-buggy", "pair/eval-buggy", "Buggy", "evaluation"),
    ]

    with pytest.raises(ValueError, match="calibration episodes do not match"):
        validate_followup_manifest_rows(rows)


def test_validate_followup_output_requires_precision_recall_balanced_accuracy(tmp_path: Path):
    output_dir = tmp_path / "followup"
    output_dir.mkdir()
    manifest = output_dir / "followup_manifest.csv"
    manifest.write_text(
        "\n".join(
            [
                "window_id,dataset_name,dataset_fingerprint,dataset_window_index,source,source_episode_id,pair_id,category,label,split,action_mode,evaluation_role",
                "w1,normal_validation,fingerprint,0,Godot_Blinking_Normal_106,Godot_Blinking_Normal_106,pair/blinking,Blinking,Normal,validation,zero_action,calibration_normal",
                "w2,normal_validation,fingerprint,1,Godot_Frozen_Animation_Platformer_Normal_107,Godot_Frozen_Animation_Platformer_Normal_107,pair/frozen,Blinking,Normal,validation,zero_action,calibration_normal",
                "w3,normal_validation,fingerprint,2,Godot_Shooting_Error_Normal_101,Godot_Shooting_Error_Normal_101,pair/shooting-101,Blinking,Normal,validation,zero_action,calibration_normal",
                "w4,normal_validation,fingerprint,3,Godot_Teleportation_TPS_Normal_1,Godot_Teleportation_TPS_Normal_1,pair/velocity-1,Blinking,Normal,validation,zero_action,calibration_normal",
                "w5,normal_validation,fingerprint,4,eval-normal,eval-normal,pair/eval-normal,Blinking,Normal,validation,zero_action,evaluation",
                "w6,buggy_probe,fingerprint,5,eval-buggy,eval-buggy,pair/eval-buggy,Blinking,Buggy,validation,zero_action,evaluation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "followup_manifest.sha256").write_text("bad\n", encoding="utf-8")
    (output_dir / "followup_episode_scores.csv").write_text(
        "method_family,method,window_scorer,seed,episode_aggregation,source_episode_id,source,pair_id,category,label,dataset_name,evaluation_role,window_count,score\n",
        encoding="utf-8",
    )
    (output_dir / "followup_comparison.csv").write_text(
        "method_family,method,window_scorer,seed,episode_aggregation,raw_score_path,raw_score_sha256,checkpoint_sha256,threshold,threshold_source,auroc,auprc,f1,precision,recall,balanced_accuracy,fpr_at_95_tpr,true_positive,false_positive,false_negative,true_negative,calibration_episode_count,evaluation_episode_count,positive_episode_count,negative_episode_count,calibration_episode_ids,confidence_interval_group_key,auroc_ci_lower,auroc_ci_upper,auroc_ci_valid_bootstrap_count,f1_ci_lower,f1_ci_upper,f1_ci_valid_bootstrap_count\n",
        encoding="utf-8",
    )
    payload = {
        "status": "followup_complete",
        "protocol": "tempglitch_followup_pair_disjoint_nonlocked",
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "manifest_sha256": "bad",
        "comparison_sha256": "bad",
    }
    for name in (
        "followup_metrics.json",
        "followup_provenance.json",
        "followup_validator_receipt.json",
    ):
        (output_dir / name).write_text(json.dumps(payload), encoding="utf-8")
    (output_dir / "FOLLOWUP_REPORT.md").write_text("report\n", encoding="utf-8")
    (output_dir / "followup_command.txt").write_text("python cmd\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA256 sidecar"):
        validate_tempglitch_followup_output(output_dir=output_dir)
