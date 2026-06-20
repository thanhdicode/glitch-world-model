from __future__ import annotations

from pathlib import Path


def test_wob_r5_cloud_runner_files_exist():
    repo_root = Path(__file__).resolve().parents[1]
    for relative in (
        "cloud/wob_r5_eval/README.md",
        "cloud/wob_r5_eval/run_kaggle_r5_wob_eval.sh",
        "cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh",
        "scripts/run_r5_wob_identical_episode_evaluation.py",
        "scripts/validate_r5_wob_evaluation.py",
        "scripts/run_r5_wob_stage.py",
        "scripts/validate_r5_wob_stage_outputs.py",
        "scripts/assemble_r5_wob_from_stages.py",
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


def test_wob_r5_staged_runner_uses_stage_entrypoints():
    repo_root = Path(__file__).resolve().parents[1]
    script = (repo_root / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_staged.sh").read_text(
        encoding="utf-8"
    )
    assert "run_r5_wob_stage.py" in script
    assert "validate_r5_wob_stage_outputs.py" in script
    assert "preflight" in script
    assert "lewm_seed44" in script
    assert "R5_WOB_BASELINE_BATCH_SIZE" in script
    assert "R5_WOB_LEWM_BATCH_SIZE" in script


def test_wob_r5_cloud_runner_captures_failures_before_output_exists():
    repo_root = Path(__file__).resolve().parents[1]
    script = (repo_root / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_eval.sh").read_text(
        encoding="utf-8"
    )
    assert "R5_WOB_FAILURE_DEBUG_DIR" in script
    assert "runner.log" in script
    assert "failure_summary.json" in script
    assert 'write_failure_debug "$?" "$LINENO" "$BASH_COMMAND"' in script


def test_wob_r5_staged_runner_captures_failure_logs():
    repo_root = Path(__file__).resolve().parents[1]
    script = (repo_root / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_staged.sh").read_text(
        encoding="utf-8"
    )
    assert "r5_wob_staged.log" in script
    assert "failure_summary.json" in script
    assert "write_debug_tarball" in script
