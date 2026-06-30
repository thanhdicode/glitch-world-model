from __future__ import annotations

import json
import tarfile
from pathlib import Path
from unittest.mock import patch

from glitch_detection.r5_wob_staged import _repack_seed_artifact, _validate_compact_seed_artifact
from glitch_detection.wob_kaggle_common import discover_r5_wob_input_overrides
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


def test_kc_discovers_direct_wob_seed_upload_dataset(tmp_path: Path):
    input_root = tmp_path / "kaggle" / "input"
    (input_root / "world-of-bugs-normal" / "NORMAL-TRAIN").mkdir(parents=True)
    (input_root / "world-of-bugs-test" / "TEST").mkdir(parents=True)
    seed_dataset = input_root / "lewm-wob-seeds-full"
    for seed in (42, 43, 44):
        root = seed_dataset / f"seed{seed}"
        root.mkdir(parents=True)
        (root / "best_weights.pt").write_bytes(b"weights")
        (root / "config.json").write_text("{}", encoding="utf-8")
        (root / "training_metadata.json").write_text("{}", encoding="utf-8")

    discovered = discover_r5_wob_input_overrides(input_root)

    assert discovered["NORMAL_INPUT_ROOT"].endswith("world-of-bugs-normal")
    assert discovered["TEST_INPUT_ROOT"].endswith("world-of-bugs-test")
    for seed in (42, 43, 44):
        resolved = Path(discovered[f"WOB_SEED{seed}_EXTRACTED_ROOT"])
        assert resolved.name == f"seed{seed}"
        assert resolved.parent.name == "lewm-wob-seeds-full"
    assert "WOB_SEED42_TARBALL" not in discovered


def test_kc_repack_direct_seed_root_into_expected_wob_outputs_layout(tmp_path: Path):
    direct_root = tmp_path / "seed42"
    direct_root.mkdir()
    for name in ("best_weights.pt", "config.json", "training_metadata.json"):
        (direct_root / name).write_text(name, encoding="utf-8")

    tar_path, sha_path = _repack_seed_artifact(
        direct_root, seed=42, repack_root=tmp_path / "repack"
    )

    assert tar_path.is_file()
    assert sha_path.is_file()
    with tarfile.open(tar_path, "r:gz") as archive:
        names = set(archive.getnames())

    assert "wob_outputs/wob_seed42/best_weights.pt" in names
    assert "wob_outputs/wob_seed42/config.json" in names
    assert "wob_outputs/wob_seed42/training_metadata.json" in names


def test_kc_accepts_compact_direct_seed_checkpoint_root(tmp_path: Path):
    root = tmp_path / "seed42"
    root.mkdir()
    weights = root / "best_weights.pt"
    weights.write_bytes(b"weights")
    import hashlib

    weights_sha = hashlib.sha256(b"weights").hexdigest()
    (root / "config.json").write_text('{"seed": 42}', encoding="utf-8")
    (root / "training_metadata.json").write_text(
        json.dumps(
            {
                "config": {"seed": 42},
                "target_optimizer_updates": 15000,
                "action_dim": 4,
                "updates_completed": 4000,
                "best_update": 1500,
                "best_validation_loss": 0.6093359693480057,
                "best_weights_sha256": weights_sha,
                "checkpoint_reload": {"weights_reload_verified": True},
                "validation_buggy_used_for_fit_select": False,
                "locked_test_materialized": False,
                "locked_test_scored": False,
            }
        ),
        encoding="utf-8",
    )
    (root / "validator_report.json").write_text(
        json.dumps({"status": "wob_seed42_validated"}),
        encoding="utf-8",
    )

    result = _validate_compact_seed_artifact(root, seed=42)

    assert result["mode"] == "compact_direct_seed_root"
    assert result["weights_path"].endswith("best_weights.pt")
    assert result["checkpoint_sha256"] == weights_sha
    assert result["validation_buggy_used_for_fit_select"] is False
    assert result["locked_test_materialized"] is False
    assert result["locked_test_scored"] is False
