import csv
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import glitch_detection.kaggle_automation as kaggle_automation
from glitch_detection.kaggle_automation import (
    ArtifactValidator,
    AutomationBlockedError,
    AutomationCommandError,
    AutomationConfig,
    CommandRunner,
    DefaultPhase6EHandlers,
    PackageValidator,
    PublicReleaseSpec,
    SecurityGuard,
    SecurityViolation,
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


def test_default_executor_rejects_kaggle_semantic_error_with_zero_exit(
    monkeypatch: pytest.MonkeyPatch,
):
    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout="Kernel push error: Maximum batch GPU session count of 2 reached.",
            stderr="",
        )

    monkeypatch.setattr("glitch_detection.kaggle_automation.subprocess.run", run)

    with pytest.raises(AutomationCommandError, match="reported an error"):
        CommandRunner._default_executor(["python", "-c", "kaggle", "kernels", "push"])


def test_command_runner_blocks_maximum_batch_gpu_sessions_without_retry(tmp_path: Path):
    calls = 0

    def executor(command: list[str]) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        raise AutomationCommandError("Maximum batch GPU session count of 2 reached.")

    runner = CommandRunner(executor=executor, max_attempts=3, sleep=lambda _seconds: None)

    with pytest.raises(AutomationBlockedError, match="Maximum batch GPU session count"):
        runner.run("kernel_push", ["kaggle", "kernels", "push"], tmp_path / "run.log")
    assert calls == 1


def test_public_release_scan_requires_license_and_redistribution(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    (root / "manifest.csv").write_text("source\nclip-a\n", encoding="utf-8")

    with pytest.raises(SecurityViolation, match="license"):
        SecurityGuard().scan_public_release(
            root,
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility="public",
                license_name="",
                redistribution_allowed=True,
            ),
        )

    with pytest.raises(SecurityViolation, match="redistribution"):
        SecurityGuard().scan_public_release(
            root,
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility="public",
                license_name="MIT",
                redistribution_allowed=False,
            ),
        )


def test_public_release_scan_rejects_locked_test_path(tmp_path: Path):
    root = tmp_path / "dataset"
    path = root / "locked_test" / "manifest.csv"
    path.parent.mkdir(parents=True)
    path.write_text("source\nclip-a\n", encoding="utf-8")

    with pytest.raises(SecurityViolation, match="locked-test path"):
        SecurityGuard().scan_public_release(
            root,
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility="public",
                license_name="MIT",
                redistribution_allowed=True,
            ),
        )


def test_default_executor_enables_utf8_environment(monkeypatch: pytest.MonkeyPatch):
    captured_environment: dict[str, str] = {}
    captured_options: dict[str, object] = {}

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured_environment.update(kwargs["env"])  # type: ignore[arg-type]
        captured_options.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr("glitch_detection.kaggle_automation.subprocess.run", run)

    CommandRunner._default_executor(["kaggle", "kernels", "output"])

    assert captured_environment["PYTHONUTF8"] == "1"
    assert captured_environment["PYTHONIOENCODING"] == "utf-8"
    assert captured_options["encoding"] == "utf-8"
    assert captured_options["errors"] == "replace"
    assert os.environ.get("PYTHONUTF8") is None


def test_default_executor_replaces_non_utf8_subprocess_output():
    result = CommandRunner._default_executor(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([0x8f]))"]
    )

    assert result.returncode == 0
    assert result.stdout == "\ufffd"


def test_atomic_json_writer_retries_transient_windows_replace_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    destination = tmp_path / "state.json"
    real_replace = os.replace
    calls = 0

    def replace(source: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError("transient Windows file lock")
        real_replace(source, target)

    monkeypatch.setattr(kaggle_automation.os, "replace", replace)
    monkeypatch.setattr(kaggle_automation.time, "sleep", lambda _seconds: None)

    kaggle_automation._write_json_atomic(destination, {"status": "ok"})

    assert calls == 2
    assert json.loads(destination.read_text(encoding="utf-8")) == {"status": "ok"}


def test_dataset_package_supports_configured_visibility_and_recursive_mode(tmp_path: Path):
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
    public = PackageValidator(SecurityGuard()).validate_dataset(
        root,
        expected_slug="thanhhuynhdieu/glitch-world-model-phase6e",
        recursive_mode="zip",
        is_private=False,
    )
    assert public["is_private"] is False


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
    metadata = json.loads((root / "kernel-metadata.json").read_text(encoding="utf-8"))
    metadata["is_private"] = False
    (root / "kernel-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    public = PackageValidator(SecurityGuard()).validate_kernel(
        root,
        expected_slug="thanhhuynhdieu/phase6e-video-autoencoder",
        dataset_slug="thanhhuynhdieu/glitch-world-model-phase6e",
        expected_visibility="public",
    )
    assert public["is_private"] is False
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


def test_generated_kernel_installs_repo_and_uses_main_branch(tmp_path: Path):
    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=tmp_path / "dataset",
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
    )

    script = DefaultPhase6EHandlers(config)._render_kernel_script()

    assert '"git", "clone", "--branch", "main"' in script
    assert '"pip", "install", "-e", str(repo), "--no-deps"' in script
    assert 'input_root = Path("/kaggle/input")' in script
    assert 'input_root.rglob("manifest.csv")' in script
    assert '"--manifest", str(manifest)' in script
    assert '"--split", str(split)' in script
    assert '"--clips-root", str(clips_root)' in script


def test_kaggle_command_uses_console_entrypoint_instead_of_python_module(tmp_path: Path):
    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=tmp_path / "dataset",
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
    )

    command = DefaultPhase6EHandlers(config)._kaggle("datasets", "list", "--mine")

    assert command[:3] == [
        sys.executable,
        "-c",
        "from kaggle.cli import main; main()",
    ]
    assert command[3:] == ["datasets", "list", "--mine"]


def test_artifact_download_filters_out_unrelated_kernel_outputs(tmp_path: Path):
    commands: list[list[str]] = []

    def executor(command: list[str]) -> SimpleNamespace:
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=tmp_path / "dataset",
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
    )
    handlers = DefaultPhase6EHandlers(
        config,
        command_runner=CommandRunner(executor=executor, max_attempts=1),
    )

    handlers.artifact_download(SimpleNamespace())

    command = commands[0]
    pattern = command[command.index("--file-pattern") + 1]
    assert "video_autoencoder\\.pt" in pattern
    assert "validation_scores\\.csv" in pattern
    assert "train_normal_manifest\\.csv" in pattern
    assert "glitch-world-model" not in pattern


def test_live_auth_failure_blocks_without_starting_interactive_login(tmp_path: Path):
    commands: list[list[str]] = []

    def executor(command: list[str]) -> SimpleNamespace:
        commands.append(command)
        raise AutomationCommandError("Authentication required")

    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=tmp_path / "dataset",
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
        dry_run=False,
    )
    runner = CommandRunner(
        executor=executor,
        security_guard=SecurityGuard(),
        max_attempts=1,
    )
    handlers = DefaultPhase6EHandlers(config, command_runner=runner)

    with pytest.raises(AutomationBlockedError, match="Kaggle authentication required"):
        handlers.auth_check_or_request_login(SimpleNamespace())

    assert len(commands) == 1
    assert "auth" not in commands[0]


def test_missing_dataset_forbidden_status_falls_back_to_create(tmp_path: Path):
    commands: list[list[str]] = []

    def executor(command: list[str]) -> SimpleNamespace:
        commands.append(command)
        if "status" in command:
            raise AutomationCommandError(
                "Command failed",
                stderr="403 Client Error: Forbidden",
            )
        return SimpleNamespace(returncode=0, stdout="created", stderr="")

    dataset_root = tmp_path / "dataset"
    dataset_root.mkdir()
    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=dataset_root,
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
        dry_run=False,
    )
    runner = CommandRunner(
        executor=executor,
        security_guard=SecurityGuard(),
        max_attempts=1,
    )
    handlers = DefaultPhase6EHandlers(config, command_runner=runner)

    config.automation_root.mkdir(parents=True)
    (config.automation_root / "dataset_fingerprint.json").write_text(
        json.dumps({"dataset_package_inventory_sha256": "inventory-fp"}),
        encoding="utf-8",
    )
    updates = handlers.dataset_create_or_version(
        SimpleNamespace(
            dataset_uploaded_fingerprint=None,
            dataset_uploaded_inventory_sha256=None,
            dataset_fingerprint="dataset-fp",
        )
    )

    assert updates == {
        "dataset_uploaded_fingerprint": "dataset-fp",
        "dataset_uploaded_inventory_sha256": "inventory-fp",
    }
    assert len(commands) == 2
    assert "status" in commands[0]
    assert "create" in commands[1]


def test_kernel_package_generation_requires_ready_dataset(tmp_path: Path):
    def executor(_command: list[str]) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout="creating", stderr="")

    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=tmp_path / "dataset",
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
        dry_run=False,
    )
    runner = CommandRunner(
        executor=executor,
        security_guard=SecurityGuard(),
        max_attempts=1,
    )
    handlers = DefaultPhase6EHandlers(config, command_runner=runner)

    with pytest.raises(AutomationBlockedError, match="not ready"):
        handlers.kernel_package_generate(SimpleNamespace(dataset_fingerprint="dataset-fp"))

    assert not config.kernel_package_root.exists()


def test_ready_unchanged_dataset_inventory_skips_reupload(tmp_path: Path):
    commands: list[list[str]] = []

    def executor(command: list[str]) -> SimpleNamespace:
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="ready", stderr="")

    config = AutomationConfig(
        repo_root=tmp_path,
        automation_root=tmp_path / "automation",
        processed_root=tmp_path / "processed",
        split_path=tmp_path / "split.csv",
        dataset_package_root=tmp_path / "dataset",
        kernel_package_root=tmp_path / "kernel",
        downloaded_root=tmp_path / "downloaded",
        ingested_root=tmp_path / "ingested",
        dry_run=False,
    )
    config.automation_root.mkdir(parents=True)
    (config.automation_root / "dataset_fingerprint.json").write_text(
        json.dumps({"dataset_package_inventory_sha256": "inventory-fp"}),
        encoding="utf-8",
    )
    runner = CommandRunner(
        executor=executor,
        security_guard=SecurityGuard(),
        max_attempts=1,
    )
    handlers = DefaultPhase6EHandlers(config, command_runner=runner)

    updates = handlers.dataset_create_or_version(
        SimpleNamespace(
            dataset_uploaded_fingerprint="old-dataset-fp",
            dataset_uploaded_inventory_sha256="inventory-fp",
            dataset_fingerprint="new-dataset-fp",
        )
    )

    assert updates == {
        "dataset_uploaded_fingerprint": "new-dataset-fp",
        "dataset_uploaded_inventory_sha256": "inventory-fp",
    }
    assert len(commands) == 1
    assert "status" in commands[0]
