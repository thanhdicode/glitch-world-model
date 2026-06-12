import os
import subprocess
import sys
from pathlib import Path

from glitch_detection.lewm_gpu_profile_kaggle import (
    DATASET_FILES,
    LeWMGPUProfileKaggleConfig,
    build_permitted_project_snapshot,
    prepare_profile_kaggle_package,
    render_profile_kernel,
    validate_profile_kaggle_package,
)


def _config() -> LeWMGPUProfileKaggleConfig:
    return LeWMGPUProfileKaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-profile-private",
        kernel_slug="huynhdieuthanh/lewm-profile-b8",
        batch_size=8,
        git_sha="abc",
        branch="codex/profile",
    )


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    for name in (
        "tempglitch_train_normal_all_local.lance",
        "tempglitch_validation_normal_all_local.lance",
    ):
        path = source / name
        path.mkdir(parents=True)
        (path / "data.bin").write_bytes(name.encode())
    return source


def test_snapshot_excludes_outputs_and_locked_test(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("OK = True\n")
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs" / "bad.txt").write_text("bad")
    (tmp_path / "locked_test.csv").write_text("bad")
    archive, manifest = build_permitted_project_snapshot(
        tmp_path, ["src/ok.py", "outputs/bad.txt", "locked_test.csv"]
    )
    assert archive
    assert manifest["included"] == ["src/ok.py"]


def test_profile_package_is_private_and_normal_only(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    package = tmp_path / "package"
    prepare_profile_kaggle_package(repo, _source(tmp_path), package, _config(), dry_run=False)
    assert {path.name for path in (package / "dataset").iterdir()} == DATASET_FILES
    assert "buggy" not in " ".join(DATASET_FILES).lower()
    assert validate_profile_kaggle_package(package)["kernel_slug"] == _config().kernel_slug


def test_generated_kernel_is_immutable_and_fail_closed():
    kernel = render_profile_kernel(
        _config(),
        {
            "optimizer_updates": 500,
            "validation_batches": 8,
            "fingerprint": "fp",
            "git_sha": "abc",
            "branch": "branch",
        },
    )
    assert "project_snapshot.zip" in kernel
    assert 'git", "clone"' not in kernel
    assert "LEWM_PROFILE_BOOTSTRAP_ONLY" in kernel
    assert "run_lewm_gpu_profile" in kernel
    assert "find_one_dir" in kernel
    assert "materialize" in kernel
    assert "validation_buggy" not in kernel


def test_generated_kernel_bootstraps_from_kaggle_like_cwd(tmp_path: Path):
    script = tmp_path / "script.py"
    script.write_text(
        render_profile_kernel(
            _config(),
            {"optimizer_updates": 500, "validation_batches": 8},
        )
    )
    environment = dict(os.environ)
    environment["LEWM_PROFILE_BOOTSTRAP_ONLY"] = "1"
    completed = subprocess.run(
        [sys.executable, str(script.resolve())],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "LEWM_PROFILE_BOOTSTRAP_OK" in completed.stdout
