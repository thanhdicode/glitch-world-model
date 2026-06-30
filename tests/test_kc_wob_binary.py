from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts.run_kc_wob_binary import run_kc_wob_binary
from scripts.validate_kc_wob_binary_output import validate_kc_wob_binary
from tests.test_validate_r5_wob_evaluation import _build_bundle


def test_kc_runner_skips_validate_package_in_smoke(tmp_path: Path):
    called_stages: list[str] = []

    def fake_run_stage(*, stage: str, **kwargs):
        called_stages.append(stage)
        return {"status": f"{stage}_complete"}

    with patch("scripts.run_kc_wob_binary.run_stage", side_effect=fake_run_stage):
        result = run_kc_wob_binary(
            input_root=tmp_path / "input",
            readiness_json=tmp_path / "readiness.json",
            eval_manifest=tmp_path / "eval.csv",
            split_csv=tmp_path / "split.csv",
            output_dir=tmp_path / "out",
            success_tarball=tmp_path / "out.tar.gz",
            baseline_batch_size=4,
            lewm_batch_size=2,
            device="cuda",
            bootstrap_seed=42,
            n_bootstrap=100,
            smoke=True,
            force=False,
        )

    assert result["status"] == "kc_wob_binary_smoke_complete"
    assert "validate_package" not in called_stages
    assert called_stages[-1] == "aggregate_metrics"


def test_kc_runner_full_mode_runs_validate_package(tmp_path: Path):
    called_stages: list[str] = []

    def fake_run_stage(*, stage: str, **kwargs):
        called_stages.append(stage)
        return {"status": f"{stage}_complete"}

    with patch("scripts.run_kc_wob_binary.run_stage", side_effect=fake_run_stage):
        result = run_kc_wob_binary(
            input_root=tmp_path / "input",
            readiness_json=tmp_path / "readiness.json",
            eval_manifest=tmp_path / "eval.csv",
            split_csv=tmp_path / "split.csv",
            output_dir=tmp_path / "out",
            success_tarball=tmp_path / "out.tar.gz",
            baseline_batch_size=4,
            lewm_batch_size=2,
            device="cuda",
            bootstrap_seed=42,
            n_bootstrap=1000,
            smoke=False,
            force=False,
        )

    assert result["status"] == "kc_wob_binary_complete"
    assert called_stages[-1] == "validate_package"


def test_validate_kc_wob_binary_accepts_full_bundle_with_markers(tmp_path: Path):
    output_dir, readiness_path = _build_bundle(tmp_path)
    metrics_path = output_dir / "r5_wob_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["paper_valid"] = True
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    for marker in (
        "stage_preflight.json",
        "stage_materialize_lance.json",
        "stage_baseline_scores.json",
        "stage_lewm_seed42.json",
        "stage_lewm_seed43.json",
        "stage_lewm_seed44.json",
        "stage_aggregate_metrics.json",
        "stage_validate_package.json",
    ):
        (output_dir / marker).write_text("{}", encoding="utf-8")

    result = validate_kc_wob_binary(output_dir, readiness_path)

    assert result["status"] == "kc_wob_binary_validated"
    assert result["paper_valid"] is True


def test_validate_kc_wob_binary_rejects_missing_marker(tmp_path: Path):
    output_dir, readiness_path = _build_bundle(tmp_path)
    metrics_path = output_dir / "r5_wob_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["paper_valid"] = True
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    try:
        validate_kc_wob_binary(output_dir, readiness_path)
    except ValueError as exc:
        assert "missing K-C stage marker" in str(exc)
    else:
        raise AssertionError("validator should reject missing stage markers")


def test_validate_kc_wob_binary_rejects_smoke_metrics(tmp_path: Path):
    output_dir, readiness_path = _build_bundle(tmp_path)
    metrics_path = output_dir / "r5_wob_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["paper_valid"] = False
    metrics["smoke"] = True
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
    for marker in (
        "stage_preflight.json",
        "stage_materialize_lance.json",
        "stage_baseline_scores.json",
        "stage_lewm_seed42.json",
        "stage_lewm_seed43.json",
        "stage_lewm_seed44.json",
        "stage_aggregate_metrics.json",
        "stage_validate_package.json",
    ):
        (output_dir / marker).write_text("{}", encoding="utf-8")

    try:
        validate_kc_wob_binary(output_dir, readiness_path)
    except ValueError as exc:
        assert "full non-smoke" in str(exc)
    else:
        raise AssertionError("validator should reject smoke metrics")
