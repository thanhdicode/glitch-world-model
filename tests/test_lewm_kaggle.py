from pathlib import Path

from glitch_detection.lewm_kaggle import (
    REQUIRED_OUTPUTS,
    LeWMKaggleConfig,
    prepare_lewm_kaggle_package,
    quota_allocation,
    render_validation_kernel,
    request_package_approvals,
    validate_lewm_smoke_artifacts,
)


def _config() -> LeWMKaggleConfig:
    return LeWMKaggleConfig(
        dataset_slug="user/lewm-private",
        kernel_slug="user/lewm-smoke",
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
    assert "train_lewm(" in kernel
    assert "resume=True" in kernel
    assert "Gate 5 LeWM smoke requires CUDA" in kernel


def test_kaggle_package_creates_separate_fingerprint_bound_requests(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    requests = request_package_approvals(package, tmp_path / "approvals")

    dataset = requests["dataset_upload_approval"]
    kernel = requests["kernel_push_approval"]
    assert dataset["fingerprint"] != kernel["fingerprint"]
    assert dataset["one_time_use"] is True
    assert kernel["one_time_use"] is True
    assert requests["live_actions_performed"] is False
    assert (package / "kernel" / "src" / "glitch_detection" / "lewm_training.py").is_file()


def test_strict_gate5_artifact_validation_requires_cuda_resume_and_matching_hashes(tmp_path: Path):
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
    (tmp_path / "checkpoint.sha256").write_text(checkpoint_hash + "\n", encoding="utf-8")

    result = validate_lewm_smoke_artifacts(tmp_path)

    assert result["status"] == "gate5_cuda_resume_verified"
    assert result["config_hash"] == config_hash
    assert result["dataset_hashes"] == dataset_hashes
