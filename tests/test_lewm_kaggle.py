import json
from pathlib import Path

import pytest

from glitch_detection.lewm_kaggle import (
    REQUIRED_OUTPUTS,
    LeWMKaggleConfig,
    build_package_audit,
    prepare_lewm_kaggle_package,
    quota_allocation,
    render_validation_kernel,
    supports_cuda_compute_capability,
    validate_kernel_push_preflight,
    validate_lewm_kaggle_package,
    validate_lewm_smoke_artifacts,
)


def _config() -> LeWMKaggleConfig:
    return LeWMKaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-tempglitch-gate5-smoke",
        kernel_slug="huynhdieuthanh/lewm-gate5-cuda-smoke-v2",
        dataset_id="tempglitch-lewm",
        action_mode="zero_action",
        train_dataset_name="train.lance",
        validation_dataset_name="validation.lance",
    )


def test_quota_allocation_matches_locked_plan():
    allocation = quota_allocation(30)
    assert allocation == {
        "lewm_dual_primary": 15,
        "video_baselines": 7.5,
        "lewm_ablations": 4.5,
        "open_vlm": 3,
    }


def test_cuda_compute_capability_guard_rejects_p100_and_accepts_t4():
    assert supports_cuda_compute_capability(6, 0) is False
    assert supports_cuda_compute_capability(7, 5) is True


def test_inventory_fingerprint_changes_when_same_size_content_changes(tmp_path: Path):
    from glitch_detection.kaggle_automation import FingerprintBuilder

    path = tmp_path / "artifact.bin"
    path.write_bytes(b"first")
    first = FingerprintBuilder.inventory_sha256(tmp_path)
    path.write_bytes(b"other")

    assert FingerprintBuilder.inventory_sha256(tmp_path) != first


def test_kaggle_package_dry_run_is_validation_only(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()

    summary = prepare_lewm_kaggle_package(source, tmp_path / "output", _config(), dry_run=True)

    assert summary["status"] == "dry-run only"
    assert summary["locked_test_included"] is False
    assert not (tmp_path / "output").exists()
    kernel = render_validation_kernel(_config())
    assert "Locked-test execution is forbidden" in kernel
    assert 'git", "clone"' in kernel
    assert 'Path("/tmp/lewm_input")' in kernel
    assert "_shutil.copytree" in kernel
    assert 'INPUT_ROOT = Path("/kaggle/input")' in kernel
    assert "INPUT_ROOT.rglob(name)" in kernel
    assert "Expected exactly one Kaggle input directory" in kernel
    assert 'DATASET = Path("/kaggle/input")' not in kernel
    assert "/kaggle/input" not in kernel.split("train_lewm")[1]
    assert 'Path("/tmp/glitch-world-model")' in kernel
    assert "stable-worldmodel==0.1.1" in kernel
    assert "stable-worldmodel[env,train]" not in kernel
    assert 'requirements" / "lewm-runtime.txt' not in kernel
    assert "/kaggle/src/lewm-runtime.txt" not in kernel
    assert "train_lewm(" in kernel
    assert "resume=True" in kernel
    assert "Gate 5 LeWM smoke requires CUDA" in kernel
    assert "cuda_runtime_guard.json" in kernel
    assert "Unsupported GPU for current PyTorch build" in kernel


def test_kaggle_kernel_can_render_update_based_research_run():
    config = LeWMKaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-research-mvp-seed42",
        kernel_slug="huynhdieuthanh/lewm-r3-seed42",
        dataset_id="tempglitch-lewm-r3",
        action_mode="zero_action",
        train_dataset_name="tempglitch_train_normal_all_local.lance",
        validation_dataset_name="tempglitch_validation_normal_all_local.lance",
        batch_size=8,
        seed=42,
        mixed_precision=True,
        target_optimizer_updates=15000,
        evaluation_interval_updates=500,
        checkpoint_interval_updates=500,
        prove_resume=False,
        max_train_steps=None,
        max_validation_steps=None,
        pin_memory=True,
        early_stopping_patience=5,
    )

    kernel = render_validation_kernel(config)

    assert 'target_optimizer_updates=CONFIG["target_optimizer_updates"]' in kernel
    assert 'mixed_precision=CONFIG["mixed_precision"]' in kernel
    assert '"target_optimizer_updates": 15000' in kernel
    assert '"max_train_steps": null' in kernel
    assert '"max_validation_steps": null' in kernel
    assert '"pin_memory": true' in kernel
    assert '"early_stopping_patience": 5' in kernel
    assert 'CONFIG["target_optimizer_updates"] is None else first' in kernel


def test_kaggle_kernel_can_render_one_update_preflight_run():
    config = LeWMKaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-r3-seed42-private",
        kernel_slug="huynhdieuthanh/lewm-r3-seed42-preflight-ab40d21",
        dataset_id="tempglitch-lewm-r3",
        action_mode="zero_action",
        train_dataset_name="tempglitch_train_normal_all_local.lance",
        validation_dataset_name="tempglitch_validation_normal_all_local.lance",
        batch_size=8,
        seed=42,
        pin_memory=True,
        mixed_precision=True,
        target_optimizer_updates=1,
        evaluation_interval_updates=1,
        checkpoint_interval_updates=1,
        prove_resume=False,
        preflight_only=True,
        max_train_steps=None,
        max_validation_steps=None,
    )

    kernel = render_validation_kernel(config)

    assert '"preflight_only": true' in kernel
    assert '"target_optimizer_updates": 1' in kernel
    assert "preflight_passed.json" in kernel
    assert "preflight_failed.json" in kernel
    assert "unsupported_cuda_compute_capability" in kernel
    assert '"validation_buggy_used_for_fit_select": False' in kernel


def test_kaggle_preflight_requires_one_update():
    with pytest.raises(ValueError, match="preflight must run exactly one update"):
        LeWMKaggleConfig(
            dataset_slug="huynhdieuthanh/lewm-r3-seed42-private",
            kernel_slug="huynhdieuthanh/lewm-r3-seed42-preflight-bad",
            dataset_id="tempglitch-lewm-r3",
            action_mode="zero_action",
            train_dataset_name="train.lance",
            validation_dataset_name="validation.lance",
            target_optimizer_updates=2,
            evaluation_interval_updates=1,
            checkpoint_interval_updates=1,
            preflight_only=True,
        )


def test_kaggle_package_builds_dataset_and_kernel_audit_without_approval_files(
    tmp_path: Path,
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    audit = build_package_audit(package, tmp_path / "audit.json")

    assert audit["authorization"] == "standing"
    assert audit["dataset_inventory_sha256"]
    assert audit["kernel_fingerprint"]
    assert audit["locked_test_materialized"] is False
    assert audit["locked_test_scored"] is False
    assert (tmp_path / "audit.json").is_file()
    assert not list(tmp_path.rglob("*.approved.json"))
    assert not list(tmp_path.rglob("*.request.json"))
    assert (package / "kernel" / "src" / "glitch_detection" / "lewm_training.py").is_file()


def test_kaggle_config_rejects_placeholder_kernel_owner():
    with pytest.raises(ValueError, match="placeholder"):
        LeWMKaggleConfig(
            dataset_slug="huynhdieuthanh/lewm-tempglitch-gate5-smoke",
            kernel_slug="private/lewm-gate5-cuda-smoke-v2",
            dataset_id="tempglitch-lewm",
            action_mode="zero_action",
            train_dataset_name="train.lance",
            validation_dataset_name="validation.lance",
        )


def test_kaggle_config_rejects_kernel_slug_equal_to_dataset_slug():
    with pytest.raises(ValueError, match="must differ"):
        LeWMKaggleConfig(
            dataset_slug="huynhdieuthanh/lewm-tempglitch-gate5-smoke",
            kernel_slug="huynhdieuthanh/lewm-tempglitch-gate5-smoke",
            dataset_id="tempglitch-lewm",
            action_mode="zero_action",
            train_dataset_name="train.lance",
            validation_dataset_name="validation.lance",
        )


def test_kaggle_package_rejects_missing_code_file(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)
    (package / "kernel" / "lewm_validation_kernel.py").unlink()

    with pytest.raises(FileNotFoundError, match="Kernel code_file does not exist"):
        validate_lewm_kaggle_package(package)


def test_kaggle_package_rejects_dataset_source_mismatch(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)
    metadata_path = package / "kernel" / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["dataset_sources"] = ["huynhdieuthanh/other-dataset"]
    metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="dataset_sources must match"):
        validate_lewm_kaggle_package(package)


def test_kernel_push_preflight_has_no_approval_status(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    result = validate_kernel_push_preflight(package)

    assert result["authorization"] == "standing"
    assert "approval_status" not in result


def test_kaggle_package_accepts_corrected_kernel_slug(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    result = validate_lewm_kaggle_package(package)

    assert result["dataset_slug"] == "huynhdieuthanh/lewm-tempglitch-gate5-smoke"
    assert result["kernel_slug"] == "huynhdieuthanh/lewm-gate5-cuda-smoke-v2"
    assert result["kernel_slug"] != result["dataset_slug"]


def _write_valid_gate5_artifacts(tmp_path: Path) -> tuple[str, dict[str, str]]:
    for name in REQUIRED_OUTPUTS:
        (tmp_path / name).write_text("{}\n", encoding="utf-8")
    config_hash = "config-hash"
    dataset_hashes = {"train": "train-hash", "validation": "validation-hash"}
    checkpoint_hash = "checkpoint-hash"
    (tmp_path / "environment.json").write_text('{"cuda_available": true}\n', encoding="utf-8")
    (tmp_path / "training_metadata.json").write_text(
        (
            '{"device":"cuda","config_hash":"config-hash",'
            '"dataset_hashes":{"train":"train-hash","validation":"validation-hash"},'
            '"checkpoint_sha256":"checkpoint-hash"}\n'
        ),
        encoding="utf-8",
    )
    (tmp_path / "dataset_metadata.json").write_text(
        '{"dataset_hashes":{"train":"train-hash","validation":"validation-hash"}}\n',
        encoding="utf-8",
    )
    (tmp_path / "protocol_audit.json").write_text(
        '{"locked_test_materialized":false,"locked_test_scored":false}\n',
        encoding="utf-8",
    )
    (tmp_path / "resume_metadata.json").write_text(
        (
            '{"resume_proved":true,"initial_completed_epoch":1,"completed_epoch":2,'
            '"config_hash":"config-hash",'
            '"dataset_hashes":{"train":"train-hash","validation":"validation-hash"}}\n'
        ),
        encoding="utf-8",
    )
    (tmp_path / "loss_history.json").write_text(
        '[{"epoch":1,"train":{"total":1.0},"validation":{"total":0.9}}]\n',
        encoding="utf-8",
    )
    (tmp_path / "collapse_diagnostics.json").write_text(
        '{"latent_variance_mean":0.2,"latent_variance_min":0.1,"finite":true}\n',
        encoding="utf-8",
    )
    (tmp_path / "checkpoint.sha256").write_text(checkpoint_hash + "\n", encoding="utf-8")
    return config_hash, dataset_hashes


def test_strict_gate5_artifact_validation_requires_cuda_resume_and_matching_hashes(tmp_path: Path):
    config_hash, dataset_hashes = _write_valid_gate5_artifacts(tmp_path)

    result = validate_lewm_smoke_artifacts(tmp_path)

    assert result["status"] == "gate5_cuda_resume_verified"
    assert result["config_hash"] == config_hash
    assert result["dataset_hashes"] == dataset_hashes


def test_strict_gate5_artifact_validation_rejects_non_finite_loss(tmp_path: Path):
    _write_valid_gate5_artifacts(tmp_path)
    (tmp_path / "loss_history.json").write_text(
        json.dumps([{"epoch": 1, "train": {"total": float("nan")}}]) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="loss history contains non-finite"):
        validate_lewm_smoke_artifacts(tmp_path)


def test_strict_gate5_artifact_validation_rejects_invalid_collapse_diagnostics(
    tmp_path: Path,
):
    _write_valid_gate5_artifacts(tmp_path)
    (tmp_path / "collapse_diagnostics.json").write_text(
        '{"latent_variance_mean":0.2,"latent_variance_min":0.1,"finite":false}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="collapse diagnostics are not finite"):
        validate_lewm_smoke_artifacts(tmp_path)


def test_strict_gate5_artifact_validation_rejects_training_locked_test_access(
    tmp_path: Path,
):
    _write_valid_gate5_artifacts(tmp_path)
    training_path = tmp_path / "training_metadata.json"
    training = json.loads(training_path.read_text(encoding="utf-8"))
    training["locked_test_scored"] = True
    training_path.write_text(json.dumps(training) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="training metadata indicates locked-test access"):
        validate_lewm_smoke_artifacts(tmp_path)


def test_strict_gate5_artifact_validation_lists_missing_artifacts(tmp_path: Path):
    with pytest.raises(
        FileNotFoundError,
        match=r"Missing LeWM smoke artifacts: run_config\.json, environment\.json",
    ):
        validate_lewm_smoke_artifacts(tmp_path)
