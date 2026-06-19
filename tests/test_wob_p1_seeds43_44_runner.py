from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_runner_scripts_include_seed_specific_output_names():
    repo_root = _repo_root()
    seed43 = (
        repo_root / "cloud" / "wob_p1_seeds43_44" / "run_kaggle_wob_p1_seed43_robust.sh"
    ).read_text(encoding="utf-8")
    seed44 = (
        repo_root / "cloud" / "wob_p1_seeds43_44" / "run_kaggle_wob_p1_seed44_robust.sh"
    ).read_text(encoding="utf-8")
    assert "wob_seed43_artifacts.tar.gz" in seed43
    assert "wob_seed43_failure_debug.tar.gz" in seed43
    assert "wob_seed44_artifacts.tar.gz" in seed44
    assert "wob_seed44_failure_debug.tar.gz" in seed44


def test_runner_scripts_do_not_contain_locked_test_materialization_or_scoring_commands():
    repo_root = _repo_root()
    scripts = [
        repo_root / "cloud" / "wob_p1_seed42" / "run_kaggle_wob_p1_seed42_robust.sh",
        repo_root / "cloud" / "wob_p1_seeds43_44" / "run_kaggle_wob_p1_seed43_robust.sh",
        repo_root / "cloud" / "wob_p1_seeds43_44" / "run_kaggle_wob_p1_seed44_robust.sh",
    ]
    forbidden = [
        "--materialize-locked",
        "--score-locked",
        "--locked-test",
        "--test-dataset",
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in scripts)
    for phrase in forbidden:
        assert phrase not in text


def test_runner_scripts_preserve_real_action_metadata():
    repo_root = _repo_root()
    seed43 = (
        repo_root / "cloud" / "wob_p1_seeds43_44" / "run_kaggle_wob_p1_seed43_robust.sh"
    ).read_text(encoding="utf-8")
    seed44 = (
        repo_root / "cloud" / "wob_p1_seeds43_44" / "run_kaggle_wob_p1_seed44_robust.sh"
    ).read_text(encoding="utf-8")
    preflight = (repo_root / "cloud" / "wob_p1_seed42" / "preflight.sh").read_text(encoding="utf-8")
    assert 'WOB_ACTION_MODE="real"' in seed43
    assert "WOB_ACTION_DIM=4" in seed43
    assert 'WOB_ACTION_MODE="real"' in seed44
    assert "WOB_ACTION_DIM=4" in seed44
    assert '"action_mode": "real"' in preflight
    assert '"action_dim": 4' in preflight


def test_runner_common_script_includes_stage_markers_and_finalization():
    script = (
        _repo_root() / "cloud" / "wob_p1_seed42" / "run_kaggle_wob_p1_seed42_robust.sh"
    ).read_text(encoding="utf-8")
    assert "=== STAGE 4: Preflight checks ===" in script
    assert "=== STAGE 7: Training ===" in script
    assert "=== STAGE 9: Artifact finalization ===" in script
    assert "finalize_artifacts.py" in script


def test_runner_common_script_refuses_to_continue_without_detected_inputs_file():
    script = (
        _repo_root() / "cloud" / "wob_p1_seed42" / "run_kaggle_wob_p1_seed42_robust.sh"
    ).read_text(encoding="utf-8")
    assert 'DETECTED_INPUTS_JSON="$WOB_P1_METADATA_ROOT/detected_inputs.json"' in script
    assert "FATAL: detect_inputs.json was not created; refusing to continue." in script


def test_runner_common_script_retries_stages_when_expected_outputs_are_missing():
    script = (
        _repo_root() / "cloud" / "wob_p1_seed42" / "run_kaggle_wob_p1_seed42_robust.sh"
    ).read_text(encoding="utf-8")
    assert '[[ ! -f "$DETECTED_INPUTS_JSON" ]]' in script
    assert '[[ ! -f "$PREFLIGHT_JSON" ]]' in script
    assert '[[ ! -f "$WOB_ROOT_METADATA" ]]' in script
    assert '[[ ! -d "$TRAIN_LANCE" ]]' in script
    assert '[[ ! -d "$VAL_LANCE" ]]' in script


def test_runner_failure_handler_exits_nonzero():
    script = (
        _repo_root() / "cloud" / "wob_p1_seed42" / "run_kaggle_wob_p1_seed42_robust.sh"
    ).read_text(encoding="utf-8")
    assert "Failure debug tarball written to $WOB_FAILURE_DEBUG_TARBALL" in script
    assert "exit 1" in script


def test_wrapper_scripts_are_shell_entrypoints():
    repo_root = _repo_root()
    for rel in [
        "cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed43_robust.sh",
        "cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed44_robust.sh",
        "cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seeds43_44_all.sh",
    ]:
        text = (repo_root / rel).read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env bash")
