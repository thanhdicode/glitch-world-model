from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from glitch_detection.r5_tempglitch_eval import (
    _lewm_window_scores,
    aggregate_episode_scores,
    available_lewm_window_scorers,
    evaluate_episode_configuration,
    lewm_window_scorer_schema,
    load_verified_r5_metrics_artifact,
    omitted_lewm_window_scorers,
    parse_seed_artifact_roots,
    planned_output_paths,
    refuse_locked_test_path,
)


def _manifest(window_id: str, episode: str, label: str, role: str) -> dict[str, str]:
    return {
        "window_id": window_id,
        "dataset_name": "normal_validation" if label == "Normal" else "buggy_probe",
        "dataset_fingerprint": "fingerprint",
        "dataset_window_index": "0",
        "source": episode,
        "source_episode_id": episode,
        "pair_id": f"pair/{episode}",
        "category": "Blinking",
        "label": label,
        "split": "validation",
        "action_mode": "zero_action",
        "evaluation_role": role,
    }


def _score(window_id: str, value: float) -> dict[str, str]:
    return {"window_id": window_id, "score": str(value)}


def test_r5_refuses_locked_test_paths():
    with pytest.raises(ValueError, match="locked-test-looking"):
        refuse_locked_test_path(Path("data/locked_test/tempglitch.lance"), description="input")
    with pytest.raises(ValueError, match="locked-test-looking"):
        refuse_locked_test_path(Path("data/lock/test/tempglitch.lance"), description="input")


def test_parse_seed_artifact_roots_supports_repeated_and_comma_separated_values():
    roots = parse_seed_artifact_roots(["a,b", " c "])

    assert roots == [Path("a"), Path("b"), Path("c")]


def test_episode_aggregation_is_deterministic():
    manifest_rows = [
        _manifest("w1", "episode-a", "Normal", "calibration_normal"),
        _manifest("w2", "episode-a", "Normal", "calibration_normal"),
        _manifest("w3", "episode-b", "Buggy", "evaluation"),
        _manifest("w4", "episode-b", "Buggy", "evaluation"),
    ]
    score_rows = [
        _score("w1", 0.1),
        _score("w2", 0.3),
        _score("w3", 0.2),
        _score("w4", 0.9),
    ]

    first = aggregate_episode_scores(
        manifest_rows,
        score_rows,
        window_scorer="frame_diff",
        episode_aggregation="top2_mean",
        method_family="baseline",
        method="frame_diff",
        seed=None,
    )
    second = aggregate_episode_scores(
        manifest_rows,
        score_rows,
        window_scorer="frame_diff",
        episode_aggregation="top2_mean",
        method_family="baseline",
        method="frame_diff",
        seed=None,
    )

    assert first == second
    assert [row["score"] for row in first] == ["0.2", "0.55"]


def test_all_methods_require_identical_manifest_alignment():
    manifest_rows = [
        _manifest("w1", "episode-a", "Normal", "calibration_normal"),
        _manifest("w2", "episode-b", "Buggy", "evaluation"),
    ]
    misaligned = [_score("w2", 0.2), _score("w1", 0.1)]

    with pytest.raises(ValueError, match="exact ordered R5 manifest"):
        aggregate_episode_scores(
            manifest_rows,
            misaligned,
            window_scorer="frame_diff",
            episode_aggregation="mean",
            method_family="baseline",
            method="frame_diff",
            seed=None,
        )


def test_feature_distance_fit_policy_is_normal_calibrated_only():
    episode_rows = [
        {
            **_manifest("w1", "cal-a", "Normal", "calibration_normal"),
            "method_family": "baseline",
            "method": "feature_distance",
            "window_scorer": "feature_distance",
            "seed": "",
            "episode_aggregation": "mean",
            "window_count": "1",
            "score": "0.1",
        },
        {
            **_manifest("w2", "cal-b", "Normal", "calibration_normal"),
            "method_family": "baseline",
            "method": "feature_distance",
            "window_scorer": "feature_distance",
            "seed": "",
            "episode_aggregation": "mean",
            "window_count": "1",
            "score": "0.3",
        },
        {
            **_manifest("w3", "eval-normal", "Normal", "evaluation"),
            "method_family": "baseline",
            "method": "feature_distance",
            "window_scorer": "feature_distance",
            "seed": "",
            "episode_aggregation": "mean",
            "window_count": "1",
            "score": "0.2",
        },
        {
            **_manifest("w4", "eval-buggy", "Buggy", "evaluation"),
            "method_family": "baseline",
            "method": "feature_distance",
            "window_scorer": "feature_distance",
            "seed": "",
            "episode_aggregation": "mean",
            "window_count": "1",
            "score": "0.9",
        },
    ]

    result = evaluate_episode_configuration(episode_rows, n_bootstrap=20)

    assert result["threshold_source"] == "calibration_normal_p95"
    assert result["calibration_episode_ids"] == ["cal-a", "cal-b"]
    assert result["metrics"]["evaluation_episode_count"] == 2
    assert result["confidence_intervals"]["auroc"]["group_key"] == "source_episode_id"


def test_metric_report_loader_requires_real_metrics_artifact(tmp_path: Path):
    missing = tmp_path / "r5_metrics.json"
    with pytest.raises(FileNotFoundError, match="Missing R5 metrics artifact"):
        load_verified_r5_metrics_artifact(missing)

    payload = {
        "status": "r5_complete",
        "manifest_sha256": "abc",
        "results": [],
    }
    missing.write_text(json.dumps(payload), encoding="utf-8")
    assert load_verified_r5_metrics_artifact(missing)["status"] == "r5_complete"


def test_planned_output_paths_include_seed_specific_lewm_files(tmp_path: Path):
    outputs = planned_output_paths(tmp_path, [44, 43])

    assert str(tmp_path / "lewm_scores_seed43.csv") in outputs
    assert str(tmp_path / "lewm_scores_seed44.csv") in outputs
    assert str(tmp_path / "r5_metrics.json") in outputs


def test_lewm_window_scorer_schema_omits_missing_cosine_gap_without_fake_scores():
    row = {
        "window_id": "w1",
        "mse_t1": "1.0",
        "mse_t2": "2.0",
        "mse_t3": "3.0",
        "l2_t1": "4.0",
        "l2_t2": "5.0",
        "l2_t3": "6.0",
    }

    available = available_lewm_window_scorers(row.keys())
    omitted = omitted_lewm_window_scorers(row.keys())
    schema = lewm_window_scorer_schema(row.keys())
    scores = _lewm_window_scores(row, window_scorers=available)

    assert available == (
        "lewm_mse_mean",
        "lewm_mse_max",
        "lewm_mse_top2_mean",
        "lewm_l2_mean",
        "lewm_l2_max",
        "lewm_l2_top2_mean",
    )
    assert all("cosine_gap" not in scorer for scorer in scores)
    assert {item["window_scorer"] for item in omitted} == {
        "lewm_cosine_gap_mean",
        "lewm_cosine_gap_max",
        "lewm_cosine_gap_top2_mean",
    }
    assert schema["available_window_scorers"] == list(available)


def test_lewm_window_scores_include_cosine_gap_when_fields_exist():
    row = {
        "window_id": "w1",
        "mse_t1": "1.0",
        "mse_t2": "2.0",
        "mse_t3": "3.0",
        "l2_t1": "4.0",
        "l2_t2": "5.0",
        "l2_t3": "6.0",
        "cosine_gap_t1": "0.1",
        "cosine_gap_t2": "0.2",
        "cosine_gap_t3": "0.6",
    }

    scores = _lewm_window_scores(
        row,
        window_scorers=available_lewm_window_scorers(row.keys()),
    )

    assert scores["lewm_cosine_gap_mean"] == pytest.approx(0.3)
    assert scores["lewm_cosine_gap_max"] == pytest.approx(0.6)
    assert scores["lewm_cosine_gap_top2_mean"] == pytest.approx(0.4)


def test_lewm_window_scores_fail_if_requested_fields_are_missing():
    row = {
        "window_id": "w1",
        "mse_t1": "1.0",
        "mse_t2": "2.0",
        "mse_t3": "3.0",
    }

    with pytest.raises(ValueError, match="missing required scorer fields"):
        _lewm_window_scores(row, window_scorers=("lewm_l2_mean",))


def test_r5_dry_run_prints_planned_output_structure(tmp_path: Path):
    train = tmp_path / "train.lance"
    validation_normal = tmp_path / "validation_normal.lance"
    validation_buggy = tmp_path / "validation_buggy.lance"
    output_dir = tmp_path / "outputs"
    seed_root = tmp_path / "seed43"
    for path in (train, validation_normal, validation_buggy, seed_root):
        path.mkdir(parents=True)

    (seed_root / "cloud_runtime_preflight.json").write_text(
        json.dumps({"status": "passed", "gpus": [{"compute_capability": [7, 5]}]}),
        encoding="utf-8",
    )
    (seed_root / "preflight_passed.json").write_text(
        json.dumps({"status": "passed"}), encoding="utf-8"
    )
    metadata = {
        "config": {"seed": 43},
        "target_optimizer_updates": 15000,
        "updates_completed": 3000,
        "stopped_early": True,
        "stopped_early_reason": "early_stopping_patience",
        "loss_history": [0.1],
        "validation_history": [0.2],
        "collapse_diagnostics": {"finite": True},
        "checkpoint_reload": {
            "weights_reload_verified": True,
            "optimizer_reload_verified": True,
            "scheduler": {"reload_verified": True},
            "reloaded_global_step": 3000,
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "config_hash": "config-hash",
        "dataset_hashes": {"train": "train-hash", "validation": "validation-hash"},
        "best_update": 500,
        "best_validation_loss": 0.6,
        "best_weights_sha256": "dummyhash",
        "checkpoint_sha256": "resumehash",
    }
    for filename in (
        "training_metadata.json",
        "loss_history.json",
        "validation_history.json",
        "collapse_diagnostics.json",
        "best_checkpoint_metadata.json",
    ):
        payload = metadata if filename == "training_metadata.json" else {"finite": True}
        if filename == "loss_history.json":
            payload = [0.1]
        if filename == "validation_history.json":
            payload = [0.2]
        if filename == "best_checkpoint_metadata.json":
            payload = {"selection_split": "validation_normal"}
        (seed_root / filename).write_text(json.dumps(payload), encoding="utf-8")
    for filename in ("checkpoint_weights.pt", "weights.pt", "best_weights.pt"):
        (seed_root / filename).write_bytes(b"weights")
    (seed_root / "config.json").write_text("{}", encoding="utf-8")

    sha = hashlib.sha256(b"weights").hexdigest()
    metadata["best_weights_sha256"] = sha
    metadata["checkpoint_sha256"] = sha
    (seed_root / "training_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_r5_tempglitch_identical_episode_evaluation.py",
            "--train-lance",
            str(train),
            "--validation-normal-lance",
            str(validation_normal),
            "--validation-buggy-lance",
            str(validation_buggy),
            "--seed-artifact-root",
            str(seed_root),
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "dry-run"
    assert payload["locked_test_materialized"] is False
    assert str(output_dir / "r5_metrics.json") in payload["planned_outputs"]
