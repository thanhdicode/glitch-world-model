from __future__ import annotations

from pathlib import Path


def test_wob_r5_cloud_runner_files_exist():
    repo_root = Path(__file__).resolve().parents[1]
    for relative in (
        "cloud/wob_r5_eval/README.md",
        "cloud/wob_r5_eval/run_kaggle_r5_wob_eval.sh",
        "scripts/run_r5_wob_identical_episode_evaluation.py",
        "scripts/validate_r5_wob_evaluation.py",
    ):
        assert (repo_root / relative).is_file(), relative


def test_wob_r5_cloud_runner_validates_artifacts_before_eval():
    repo_root = Path(__file__).resolve().parents[1]
    script = (repo_root / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_eval.sh").read_text(
        encoding="utf-8"
    )
    assert "validate_wob_seed_artifacts.py" in script
    assert "run_r5_wob_identical_episode_evaluation.py" in script
    assert "validate_r5_wob_evaluation.py" in script
    assert "locked test" not in script.lower()


def test_wob_r5_cloud_runner_captures_failures_before_output_exists():
    repo_root = Path(__file__).resolve().parents[1]
    script = (repo_root / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_eval.sh").read_text(
        encoding="utf-8"
    )
    assert "R5_WOB_FAILURE_DEBUG_DIR" in script
    assert "runner.log" in script
    assert "failure_summary.json" in script
    assert 'write_failure_debug "$?" "$LINENO" "$BASH_COMMAND"' in script
