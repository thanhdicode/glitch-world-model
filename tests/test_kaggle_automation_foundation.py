import json
from pathlib import Path

import pytest

from glitch_detection.kaggle_automation import (
    AutomationState,
    FingerprintBuilder,
    KaggleAction,
    KaggleExecutionPolicy,
    PublicReleaseSpec,
    SecurityGuard,
    SecurityViolation,
    StateStore,
)


def test_state_store_writes_atomic_backup(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.save(AutomationState(current_step="preflight"))
    store.save(AutomationState(current_step="dataset_dry_run", completed_steps=["preflight"]))

    assert store.load().current_step == "dataset_dry_run"
    previous = json.loads((tmp_path / "state.prev.json").read_text(encoding="utf-8"))
    assert previous["current_step"] == "preflight"
    assert not (tmp_path / "state.json.tmp").exists()


def test_execution_policy_authorizes_public_nonlocked_kaggle_actions():
    result = KaggleExecutionPolicy().authorize(
        KaggleAction(
            action="kernel_push",
            fingerprint="kernel-fp",
            visibility="public",
            locked_test_materialized=False,
            locked_test_scored=False,
            redistribution_allowed=True,
        )
    )

    assert result["authorized"] is True
    assert result["authorization"] == "standing"
    assert result["fingerprint"] == "kernel-fp"


@pytest.mark.parametrize("flag", ["locked_test_materialized", "locked_test_scored"])
def test_execution_policy_rejects_locked_test_without_separate_release(flag: str):
    values = {
        "action": "kernel_push",
        "fingerprint": "kernel-fp",
        "visibility": "public",
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "redistribution_allowed": True,
    }
    values[flag] = True

    with pytest.raises(SecurityViolation, match="locked test"):
        KaggleExecutionPolicy().authorize(KaggleAction(**values))


def test_execution_policy_rejects_public_dataset_without_redistribution_permission():
    with pytest.raises(SecurityViolation, match="redistribution"):
        KaggleExecutionPolicy().authorize(
            KaggleAction(
                action="dataset_create_or_version",
                fingerprint="dataset-fp",
                visibility="public",
                locked_test_materialized=False,
                locked_test_scored=False,
                redistribution_allowed=False,
            )
        )


def test_fingerprint_contains_required_components(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    split = tmp_path / "split.csv"
    package = tmp_path / "package"
    kernel = tmp_path / "kernel.py"
    manifest.write_text("manifest", encoding="utf-8")
    split.write_text("split", encoding="utf-8")
    package.mkdir()
    (package / "clip.png").write_bytes(b"frame")
    kernel.write_text("print('train')", encoding="utf-8")

    result = FingerprintBuilder().build(
        git_commit_sha="abc123",
        branch="feature",
        manifest_path=manifest,
        split_path=split,
        dataset_package_root=package,
        kernel_script_path=kernel,
        config={"accelerator": "NvidiaTeslaT4"},
        expected_partition_counts={"train_normal": 1724, "validation": 1071, "test": 1125},
    )

    assert result["git_commit_sha"] == "abc123"
    assert result["branch"] == "feature"
    assert result["manifest_sha256"]
    assert result["split_sha256"]
    assert result["dataset_package_inventory_sha256"]
    assert result["kernel_script_sha256"]
    assert result["config_sha256"]
    assert result["expected_partition_counts"]["validation"] == 1071
    assert result["combined_sha256"]


@pytest.mark.parametrize(
    "relative_path",
    [
        ".kaggle/kaggle.json",
        "access_token",
        ".env.local",
        "secret.pem",
        "id_rsa",
        "secret.p12",
    ],
)
def test_security_guard_rejects_forbidden_files(tmp_path: Path, relative_path: str):
    root = tmp_path / "package"
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("secret", encoding="utf-8")

    with pytest.raises(SecurityViolation):
        SecurityGuard().scan_package(root, package_kind="dataset")


def test_security_guard_rejects_checkpoints_in_kernel_package(tmp_path: Path):
    root = tmp_path / "kernel"
    root.mkdir()
    (root / "video_autoencoder.pt").write_bytes(b"checkpoint")

    with pytest.raises(SecurityViolation, match="checkpoint"):
        SecurityGuard().scan_package(root, package_kind="kernel")


def test_security_guard_redacts_before_logs_are_saved():
    guard = SecurityGuard()
    api_token_name = "KAGGLE_" + "API_TOKEN"
    access_token_name = "access_" + "token"
    raw = f"request failed {api_token_name}=super-secret {access_token_name}: abc123"

    redacted = guard.redact(raw)

    assert "super-secret" not in redacted
    assert "abc123" not in redacted
    assert redacted.count("<redacted>") == 2


def test_security_guard_redacts_sensitive_environment_values_without_variable_name():
    guard = SecurityGuard(environment={"KAGGLE_API_TOKEN": "environment-secret"})

    redacted = guard.redact("remote echoed environment-secret")

    assert "environment-secret" not in redacted
    assert "<redacted>" in redacted


def test_security_guard_rejects_nested_outputs_and_token_content(tmp_path: Path):
    root = tmp_path / "kernel"
    nested_output = root / "outputs" / "result.txt"
    nested_output.parent.mkdir(parents=True)
    nested_output.write_text("result", encoding="utf-8")

    with pytest.raises(SecurityViolation, match="outputs"):
        SecurityGuard().scan_package(root, package_kind="kernel")

    nested_output.unlink()
    token_name = "access_" + "token"
    (root / "config.txt").write_text(f"{token_name}: secret-value", encoding="utf-8")
    with pytest.raises(SecurityViolation, match="token-like"):
        SecurityGuard().scan_package(root, package_kind="kernel")
