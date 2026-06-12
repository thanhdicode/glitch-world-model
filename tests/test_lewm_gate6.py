import base64
import json
import os
import re
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from glitch_detection.lewm_gate6 import (
    GATE6_REQUIRED_OUTPUTS,
    Gate6KaggleConfig,
    build_source_archive,
    prepare_gate6_kaggle_package,
    render_gate6_kernel,
    validate_gate6_artifacts,
    validate_gate6_kaggle_package,
)


def _config() -> Gate6KaggleConfig:
    return Gate6KaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-tempglitch-gate6-pilot",
        kernel_slug="huynhdieuthanh/lewm-gate6-pilot-v1",
        dataset_id="tempglitch-lewm-gate6",
        train_dataset_name="train.lance",
        validation_dataset_name="validation.lance",
        buggy_probe_dataset_name="buggy.lance",
    )


def test_gate6_package_requires_three_datasets_and_stays_locked(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        (source / name).mkdir()
    summary = prepare_gate6_kaggle_package(source, tmp_path / "package", _config(), dry_run=True)
    kernel = render_gate6_kernel(_config(), "c291cmNl")

    assert summary["locked_test_included"] is False
    assert "normal_only_training" in kernel
    assert "score_lance_probe" in kernel
    assert "Locked-test execution is forbidden" in kernel
    assert "base64.b64decode" in kernel
    assert "SOURCE_ARCHIVE_B64" in kernel
    assert 'PACKAGE_ROOT / "glitch_detection_src.zip"' not in kernel


def test_gate6_materialized_package_archives_lance_directories(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        dataset = source / name
        dataset.mkdir()
        (dataset / "data.bin").write_bytes(b"lance")

    package = tmp_path / "package"
    prepare_gate6_kaggle_package(source, package, _config(), dry_run=False)

    assert (package / "dataset" / "train.lance.zip").is_file()
    assert not (package / "dataset" / "train.lance").exists()
    assert not (package / "kernel" / "glitch_detection_src.zip").exists()
    kernel = (package / "kernel" / "lewm_gate6_kernel.py").read_text(encoding="utf-8")
    assert "base64.b64decode" in kernel


def test_gate6_source_archive_contains_python_package_without_caches(tmp_path: Path):
    source = tmp_path / "src" / "glitch_detection"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("", encoding="utf-8")
    (source / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    cache = source / "__pycache__"
    cache.mkdir()
    (cache / "module.pyc").write_bytes(b"cache")

    archive = build_source_archive(tmp_path / "src")

    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        assert bundle.namelist() == [
            "glitch_detection/__init__.py",
            "glitch_detection/module.py",
        ]


def test_gate6_embedded_bootstrap_runs_from_kaggle_like_cwd(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    archive = build_source_archive(repo_root / "src")
    kernel = render_gate6_kernel(
        _config(),
        base64.b64encode(archive).decode("ascii"),
    )
    script = tmp_path / "kaggle_src" / "script.py"
    script.parent.mkdir()
    script.write_text(kernel, encoding="utf-8")
    work = tmp_path / "kaggle_working"
    work.mkdir()
    environment = dict(os.environ)
    environment["GATE6_BOOTSTRAP_ONLY"] = "1"
    environment["GATE6_CODE_ROOT"] = str((tmp_path / "gate6_code").resolve())

    completed = subprocess.run(
        [sys.executable, str(script.resolve())],
        cwd=work,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "GATE6_BOOTSTRAP_OK" in completed.stdout


def test_gate6_generated_kernel_has_no_local_windows_path_or_auxiliary_source_file():
    kernel = render_gate6_kernel(_config(), "c291cmNl")

    assert not re.search(r"[A-Za-z]:\\", kernel)
    assert "glitch_detection_src.zip" not in kernel
    assert "SOURCE_ARCHIVE_B64" in kernel


def test_gate6_package_validator_accepts_single_file_kernel(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        dataset = source / name
        dataset.mkdir()
        (dataset / "data.bin").write_bytes(b"lance")
    package = tmp_path / "package"
    prepare_gate6_kaggle_package(source, package, _config(), dry_run=False)

    result = validate_gate6_kaggle_package(package)

    assert result["dataset_slug"] == _config().dataset_slug
    assert result["kernel_slug"] == _config().kernel_slug
    assert result["locked_test_materialized"] is False


def test_gate6_package_validator_rejects_auxiliary_zip(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        (source / name).mkdir()
    package = tmp_path / "package"
    prepare_gate6_kaggle_package(source, package, _config(), dry_run=False)
    (package / "kernel" / "source.zip").write_bytes(b"not needed")

    with pytest.raises(ValueError, match="auxiliary files"):
        validate_gate6_kaggle_package(package)


def test_gate6_package_validator_rejects_windows_path(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        (source / name).mkdir()
    package = tmp_path / "package"
    prepare_gate6_kaggle_package(source, package, _config(), dry_run=False)
    script = package / "kernel" / "lewm_gate6_kernel.py"
    script.write_text(script.read_text(encoding="utf-8") + '\nPATH = r"C:\\private"\n')

    with pytest.raises(ValueError, match="Windows absolute path"):
        validate_gate6_kaggle_package(package)


def _write_valid_artifacts(root: Path) -> None:
    for name in GATE6_REQUIRED_OUTPUTS:
        (root / name).write_text("{}\n", encoding="utf-8")
    (root / "environment.json").write_text('{"cuda_available":true}\n', encoding="utf-8")
    (root / "training_metadata.json").write_text(
        '{"device":"cuda","completed_epoch":1,"checkpoint_sha256":"hash",'
        '"locked_test_materialized":false,"locked_test_scored":false}\n',
        encoding="utf-8",
    )
    normal = '"normal_only_training":true,"normal_only_validation":true'
    (root / "dataset_metadata.json").write_text("{" + normal + "}\n", encoding="utf-8")
    (root / "protocol_audit.json").write_text(
        "{" + normal + ',"locked_test_materialized":false,"locked_test_scored":false}\n',
        encoding="utf-8",
    )
    (root / "loss_history.json").write_text(
        '[{"epoch":1,"train":[{"loss":1.0}],"validation":[{"loss":0.9}]}]\n',
        encoding="utf-8",
    )
    (root / "collapse_diagnostics.json").write_text(
        '{"finite":true,"latent_variance_mean":0.2,"latent_variance_min":0.1}\n',
        encoding="utf-8",
    )
    (root / "checkpoint_reload.json").write_text(
        '{"checkpoint_reload_verified":true,"best_weights_sha256":"best","best_epoch":1}\n',
        encoding="utf-8",
    )
    (root / "encoding_proof.json").write_text(
        '{"normal_validation":{"finite":true,"surprise_mean":0.2},'
        '"nonlocked_buggy_validation":{"finite":true,"surprise_mean":0.3}}\n',
        encoding="utf-8",
    )
    (root / "checkpoint.sha256").write_text("hash\n", encoding="utf-8")


def test_gate6_validator_accepts_strict_artifacts(tmp_path: Path):
    _write_valid_artifacts(tmp_path)

    result = validate_gate6_artifacts(tmp_path)

    assert result["status"] == "gate6_passed"
    assert result["locked_test_scored"] is False


def test_gate6_validator_rejects_buggy_training(tmp_path: Path):
    _write_valid_artifacts(tmp_path)
    metadata = json.loads((tmp_path / "dataset_metadata.json").read_text())
    metadata["normal_only_training"] = False
    (tmp_path / "dataset_metadata.json").write_text(json.dumps(metadata))

    with pytest.raises(ValueError, match="not normal-only"):
        validate_gate6_artifacts(tmp_path)


# ---------------------------------------------------------------------------
# Regression tests: nested Kaggle Lance mount fix
# ---------------------------------------------------------------------------


def test_generated_kernel_does_not_contain_old_len_guard():
    """The old brittle guard must be absent from the generated kernel."""
    kernel = render_gate6_kernel(_config(), "c291cmNl")
    assert "len(directories) + len(archives) != 1" not in kernel


def test_generated_kernel_contains_select_lance_candidate():
    """The new helper function must be present in the generated kernel."""
    kernel = render_gate6_kernel(_config(), "c291cmNl")
    assert "_select_lance_candidate" in kernel


def test_generated_kernel_handles_nested_same_name_candidates():
    """_select_lance_candidate logic must strip ancestor entries, keeping deepest leaf."""
    kernel = render_gate6_kernel(_config(), "c291cmNl")
    # The ancestor-stripping logic must be present.
    assert "startswith(str(c) +" in kernel or 'str(other).startswith(str(c) + "/"' in kernel


def test_generated_kernel_materializes_into_tmp_gate6_input():
    """/tmp/gate6_input must be the destination, never /kaggle/input."""
    kernel = render_gate6_kernel(_config(), "c291cmNl")
    assert "/tmp/gate6_input" in kernel
    # Datasets must not be read directly from the Kaggle input mount.
    assert "copytree(INPUT_ROOT" not in kernel
    assert "shutil.copytree(INPUT_ROOT" not in kernel


def test_generated_kernel_still_embeds_source_archive():
    """SOURCE_ARCHIVE_B64 must still be present (self-contained kernel requirement)."""
    kernel = render_gate6_kernel(_config(), "c291cmNl")
    assert "SOURCE_ARCHIVE_B64" in kernel
    assert "base64.b64decode" in kernel


def test_gate6_package_validator_still_allows_only_metadata_and_code(tmp_path: Path):
    """Package validation must still reject any auxiliary file in the kernel directory."""
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        dataset = source / name
        dataset.mkdir()
        (dataset / "data.bin").write_bytes(b"lance")
    package = tmp_path / "package"
    prepare_gate6_kaggle_package(source, package, _config(), dry_run=False)

    # Baseline: should pass.
    result = validate_gate6_kaggle_package(package)
    assert result["locked_test_materialized"] is False

    # Adding a spurious file must be rejected.
    (package / "kernel" / "extra.zip").write_bytes(b"extra")
    with pytest.raises(ValueError, match="auxiliary files"):
        validate_gate6_kaggle_package(package)
