import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from glitch_detection.kaggle_automation import (
    ArtifactValidator,
    AutomationBlockedError,
    AutomationCommandError,
    CommandRunner,
    PackageValidator,
    SecurityGuard,
    is_transient_error,
)


@pytest.mark.parametrize(
    "message",
    [
        "HTTP 429 too many requests",
        "HTTP 503 service unavailable",
        "connection reset by peer",
        "temporary failure in name resolution",
        "operation timed out",
    ],
)
def test_transient_error_classifier_accepts_network_and_retryable_http(message: str):
    assert is_transient_error(message) is True


@pytest.mark.parametrize(
    "message",
    [
        "401 unauthorized",
        "GPU quota exhausted",
        "accelerator unavailable",
        "metadata invalid",
        "artifact schema mismatch",
    ],
)
def test_transient_error_classifier_rejects_non_retryable_failures(message: str):
    assert is_transient_error(message) is False


def test_command_runner_retries_transient_errors_and_redacts_before_log(tmp_path: Path):
    calls: list[int] = []
    token_name = "KAGGLE_" + "API_TOKEN"
    access_token_name = "access_" + "token"

    def executor(command: list[str]) -> SimpleNamespace:
        calls.append(1)
        if len(calls) < 3:
            raise AutomationCommandError(
                f"HTTP 503 {token_name}=secret-token",
                stderr=f"HTTP 503 {token_name}=secret-token",
            )
        return SimpleNamespace(returncode=0, stdout=f"ok {access_token_name}: hidden", stderr="")

    runner = CommandRunner(
        executor=executor,
        security_guard=SecurityGuard(),
        max_attempts=3,
        sleep=lambda _seconds: None,
    )

    result = runner.run("dataset_upload", ["kaggle", "datasets", "create"], tmp_path / "run.log")

    assert result.stdout.startswith("ok")
    assert len(calls) == 3
    log = (tmp_path / "run.log").read_text(encoding="utf-8")
    assert "secret-token" not in log
    assert "hidden" not in log
    assert "<redacted>" in log


def test_command_runner_blocks_gpu_quota_without_retry(tmp_path: Path):
    calls: list[int] = []

    def executor(command: list[str]) -> SimpleNamespace:
        calls.append(1)
        raise AutomationCommandError("GPU quota exhausted")

    runner = CommandRunner(
        executor=executor,
        security_guard=SecurityGuard(),
        max_attempts=3,
        sleep=lambda _seconds: None,
    )

    with pytest.raises(AutomationBlockedError, match="GPU quota exhausted"):
        runner.run("kernel_push_once", ["kaggle", "kernels", "push"], tmp_path / "run.log")
    assert len(calls) == 1


def test_dataset_package_requires_private_other_license_and_recursive_mode(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    (root / "tempglitch_phase3b").mkdir()
    (root / "tempglitch_phase3b" / "manifest.csv").write_text("manifest", encoding="utf-8")
    (root / "split.csv").write_text("split", encoding="utf-8")
    (root / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "id": "thanhhuynhdieu/glitch-world-model-phase6e",
                "licenses": [{"name": "other"}],
            }
        ),
        encoding="utf-8",
    )

    summary = PackageValidator(SecurityGuard()).validate_dataset(
        root,
        expected_slug="thanhhuynhdieu/glitch-world-model-phase6e",
        recursive_mode="zip",
        is_private=True,
    )

    assert summary["is_private"] is True
    assert summary["license"] == "other"
    with pytest.raises(ValueError, match="private"):
        PackageValidator(SecurityGuard()).validate_dataset(
            root,
            expected_slug="thanhhuynhdieu/glitch-world-model-phase6e",
            recursive_mode="zip",
            is_private=False,
        )


def test_kernel_package_rejects_checkpoint_and_validates_private_metadata(tmp_path: Path):
    root = tmp_path / "kernel"
    root.mkdir()
    (root / "phase6e_train_kernel.py").write_text("print('train')", encoding="utf-8")
    (root / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": "thanhhuynhdieu/phase6e-video-autoencoder",
                "code_file": "phase6e_train_kernel.py",
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "dataset_sources": ["thanhhuynhdieu/glitch-world-model-phase6e"],
            }
        ),
        encoding="utf-8",
    )

    summary = PackageValidator(SecurityGuard()).validate_kernel(
        root,
        expected_slug="thanhhuynhdieu/phase6e-video-autoencoder",
        dataset_slug="thanhhuynhdieu/glitch-world-model-phase6e",
    )

    assert summary["is_private"] is True
    (root / "checkpoint.pt").write_bytes(b"checkpoint")
    with pytest.raises(Exception, match="checkpoint"):
        PackageValidator(SecurityGuard()).validate_kernel(
            root,
            expected_slug="thanhhuynhdieu/phase6e-video-autoencoder",
            dataset_slug="thanhhuynhdieu/glitch-world-model-phase6e",
        )


def test_artifact_validator_requires_cuda_finite_scores_and_test_untouched(tmp_path: Path):
    root = tmp_path / "artifacts"
    output = tmp_path / "validated"
    root.mkdir()
    (root / "video_autoencoder.pt").write_bytes(b"checkpoint")
    (root / "training_metadata.json").write_text(json.dumps({"device": "cuda:0"}), encoding="utf-8")
    (root / "phase6e_summary.json").write_text(json.dumps({"test_scored": False}), encoding="utf-8")
    (root / "protocol_audit.json").write_text(json.dumps({"test_scored": False}), encoding="utf-8")
    with (root / "validation_scores.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["clip_id", "score"])
        writer.writeheader()
        writer.writerows([{"clip_id": "a", "score": "0.1"}, {"clip_id": "b", "score": "0.2"}])

    summary = ArtifactValidator().validate(root, output, expected_validation_rows=2)

    assert summary["status"] == "artifact validation complete"
    assert summary["test_scored"] is False
    assert (output / "artifact_validation_summary.json").is_file()
    assert (output / "artifact_validation_report.md").is_file()


def test_artifact_validator_rejects_missing_test_scored_flag(tmp_path: Path):
    root = tmp_path / "artifacts"
    root.mkdir()
    (root / "video_autoencoder.pt").write_bytes(b"checkpoint")
    (root / "training_metadata.json").write_text(json.dumps({"device": "cuda:0"}), encoding="utf-8")
    (root / "phase6e_summary.json").write_text(json.dumps({"test_scored": False}), encoding="utf-8")
    (root / "protocol_audit.json").write_text(json.dumps({}), encoding="utf-8")
    (root / "validation_scores.csv").write_text("clip_id,score\na,0.1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="explicitly contain test_scored=false"):
        ArtifactValidator().validate(root, tmp_path / "output", expected_validation_rows=1)


def test_artifact_validator_finds_nested_kaggle_output_root(tmp_path: Path):
    root = tmp_path / "downloaded"
    nested = root / "tempglitch_phase6e" / "seed_42"
    output = tmp_path / "validated"
    nested.mkdir(parents=True)
    (nested / "video_autoencoder.pt").write_bytes(b"checkpoint")
    (nested / "training_metadata.json").write_text(
        json.dumps({"device": "cuda:0"}), encoding="utf-8"
    )
    (nested / "phase6e_summary.json").write_text(
        json.dumps({"test_scored": False}), encoding="utf-8"
    )
    (nested / "protocol_audit.json").write_text(
        json.dumps({"test_scored": False}), encoding="utf-8"
    )
    (nested / "validation_scores.csv").write_text("clip_id,score\na,0.1\n", encoding="utf-8")

    summary = ArtifactValidator().validate(root, output, expected_validation_rows=1)

    assert summary["artifact_root"] == str(nested)
