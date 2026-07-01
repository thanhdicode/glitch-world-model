from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from scripts.validate_r5_wob_evaluation import validate_r5_wob


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _build_bundle(tmp_path: Path) -> tuple[Path, Path]:
    output_dir = tmp_path / "outputs" / "r5_wob_identical_episode"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, str]] = []
    for index in range(6):
        manifest_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-normal",
                "source": f"NORMAL-TRAIN/ep-{index:04d}/ep-{index:04d}.tar",
                "episode_id": f"normal/ep-{index:04d}",
                "pair_id": f"normal/ep-{index:04d}",
                "category": "Normal",
                "label": "Normal",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
                "evaluation_role": "calibration_normal",
            }
        )
    for index in range(6):
        manifest_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-normal",
                "source": f"NORMAL-TRAIN/ep-{index + 6:04d}/ep-{index + 6:04d}.tar",
                "episode_id": f"normal/ep-{index + 6:04d}",
                "pair_id": f"normal/ep-{index + 6:04d}",
                "category": "Normal",
                "label": "Normal",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
                "evaluation_role": "evaluation_normal",
            }
        )
    for index in range(60):
        manifest_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-test",
                "source": f"TEST/Bug/ep-{index:04d}/ep-{index:04d}.tar",
                "episode_id": f"Bug/ep-{index:04d}",
                "pair_id": f"Bug/ep-{index:04d}",
                "category": "Bug",
                "label": "Buggy",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
                "evaluation_role": "evaluation_buggy",
            }
        )
    manifest_path = output_dir / "r5_wob_manifest.csv"
    _write_csv(manifest_path, manifest_rows)
    readiness = {
        "eval_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "eval_manifest_row_count": 72,
    }
    readiness_path = tmp_path / "readiness.json"
    readiness_path.write_text(json.dumps(readiness), encoding="utf-8")

    episode_rows = [
        {
            "method_family": "lewm",
            "method": "lewm",
            "window_scorer": "lewm_l2_mean",
            "seed": "42",
            "episode_aggregation": "mean",
            "source_episode_id": "normal/ep-0000",
            "source": "s",
            "pair_id": "p",
            "category": "Normal",
            "label": "Normal",
            "dataset_name": "normal_validation",
            "evaluation_role": "calibration_normal",
            "window_count": "10",
            "score": "0.1",
        }
    ]
    _write_csv(output_dir / "episode_scores.csv", episode_rows)

    baseline_rows = [{"window_id": "w0", "frame_diff": "0.1", "feature_distance": "0.2"}]
    _write_csv(output_dir / "baseline_scores.csv", baseline_rows)

    comparison_rows = []
    for seed in ("42", "43", "44"):
        comparison_rows.append(
            {
                "method_family": "lewm",
                "method": "lewm",
                "window_scorer": "lewm_l2_mean",
                "seed": seed,
                "episode_aggregation": "mean",
                "raw_score_path": "x",
                "raw_score_sha256": "y",
                "checkpoint_sha256": "z",
                "threshold": "0.1",
                "threshold_source": "calibration_normal_p95",
                "auroc": "0.6",
                "auprc": "0.7",
                "f1": "0.5",
                "fpr_at_95_tpr": "0.4",
                "evaluation_episode_count": "66",
                "positive_episode_count": "60",
                "negative_episode_count": "6",
                "calibration_episode_ids": "a",
                "auroc_ci_lower": "0.5",
                "auroc_ci_upper": "0.7",
                "f1_ci_lower": "0.4",
                "f1_ci_upper": "0.6",
            }
        )
    for method in ("frame_diff", "feature_distance"):
        comparison_rows.append(
            {
                "method_family": "baseline",
                "method": method,
                "window_scorer": method,
                "seed": "",
                "episode_aggregation": "mean",
                "raw_score_path": "x",
                "raw_score_sha256": "y",
                "checkpoint_sha256": "",
                "threshold": "0.1",
                "threshold_source": "calibration_normal_p95",
                "auroc": "0.6",
                "auprc": "0.7",
                "f1": "0.5",
                "fpr_at_95_tpr": "0.4",
                "evaluation_episode_count": "66",
                "positive_episode_count": "60",
                "negative_episode_count": "6",
                "calibration_episode_ids": "a",
                "auroc_ci_lower": "0.5",
                "auroc_ci_upper": "0.7",
                "f1_ci_lower": "0.4",
                "f1_ci_upper": "0.6",
            }
        )
    _write_csv(output_dir / "r5_wob_comparison.csv", comparison_rows)

    metrics = {
        "status": "r5_wob_complete",
        "bootstrap": {"seed": 42, "n_bootstrap": 1000, "group_key": "source_episode_id"},
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": True,
    }
    (output_dir / "r5_wob_metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (output_dir / "R5_WOB_REPORT.md").write_text("# report\n", encoding="utf-8")
    provenance = {
        "outputs": {
            "r5_wob_manifest.csv": "a",
            "episode_scores.csv": "b",
            "baseline_scores.csv": "c",
            "r5_wob_metrics.json": "d",
            "r5_wob_comparison.csv": "e",
            "r5_wob_provenance.json": "f",
            "R5_WOB_REPORT.md": "g",
        },
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    (output_dir / "r5_wob_provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
    return output_dir, readiness_path


def test_validate_r5_wob_accepts_synthetic_bundle(tmp_path: Path):
    output_dir, readiness_path = _build_bundle(tmp_path)
    result = validate_r5_wob(output_dir, readiness_path)
    assert result["status"] == "r5_wob_validated"
    assert result["lewm_seeds_present"] == ["42", "43", "44"]


def test_validate_r5_wob_rejects_missing_seed(tmp_path: Path):
    output_dir, readiness_path = _build_bundle(tmp_path)
    comparison_path = output_dir / "r5_wob_comparison.csv"
    rows = [
        row
        for row in csv.DictReader(comparison_path.open("r", encoding="utf-8"))
        if row["seed"] != "44"
    ]
    _write_csv(comparison_path, rows)
    try:
        validate_r5_wob(output_dir, readiness_path)
    except ValueError as exc:
        assert "missing lewm seeds" in str(exc)
    else:
        raise AssertionError("Validator should fail when a required seed is missing.")
