"""Regression tests: stale Lance directories are cleaned before re-materialization.

Root cause: LanceWriter(path, mode="error") in stable_worldmodel exits the process
with code 120 (via Rust process::exit) when a Lance directory already exists.
This bypasses Python's exception handling entirely — no traceback, no stdout, exit 120.

Symptom on Kaggle: Stage 2 (materialize_lance) fails immediately with exit code 120
and zero log output whenever a previous run already materialized the Lance datasets
and the stage marker subsequently becomes invalid (e.g. after a git checkout to a
newer commit that alters tracked-file hashes).

Fix: run_materialize_lance must shutil.rmtree any stale Lance directories before
calling _build_lance_from_rows / write_lance_dataset — i.e. whenever the stage is
NOT being skipped (when _maybe_skip returned None).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from glitch_detection.r5_wob_staged import (
    BUGGY_LANCE_NAME,
    NORMAL_LANCE_NAME,
    TRAIN_LANCE_NAME,
    run_materialize_lance,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stale_lance_dirs(output_dir: Path) -> dict[str, Path]:
    """Create fake .lance directories simulating a previous partial run."""
    stale: dict[str, Path] = {}
    for name in (TRAIN_LANCE_NAME, NORMAL_LANCE_NAME, BUGGY_LANCE_NAME):
        p = output_dir / name
        p.mkdir()
        (p / "stale_marker.bin").write_bytes(b"stale")
        stale[name] = p
    return stale


# ---------------------------------------------------------------------------
# Tests: constants exist
# ---------------------------------------------------------------------------


def test_lance_name_constants_defined():
    """The three Lance directory name constants must be defined."""
    assert TRAIN_LANCE_NAME, "TRAIN_LANCE_NAME must be a non-empty string"
    assert NORMAL_LANCE_NAME, "NORMAL_LANCE_NAME must be a non-empty string"
    assert BUGGY_LANCE_NAME, "BUGGY_LANCE_NAME must be a non-empty string"
    # All must be distinct
    names = {TRAIN_LANCE_NAME, NORMAL_LANCE_NAME, BUGGY_LANCE_NAME}
    assert len(names) == 3, "Lance directory name constants must be distinct"


def test_lance_name_constants_have_lance_suffix():
    """Lance directory names must end with .lance to match LanceWriter expectations."""
    for name in (TRAIN_LANCE_NAME, NORMAL_LANCE_NAME, BUGGY_LANCE_NAME):
        assert name.endswith(".lance"), f"Expected .lance suffix: {name!r}"


# ---------------------------------------------------------------------------
# Tests: stale-directory cleanup
# ---------------------------------------------------------------------------

_FAKE_PREFLIGHT = {
    "stage": "preflight",
    "schema_version": 1,
    "status": "preflight_complete",
    "smoke": False,
    "normal_root": "/fake/normal",
    "test_root": "/fake/test",
    "files": {},
}

_FAKE_READINESS = ({"eval_manifest_sha256": "aabbcc"}, [{"evaluation_role": "calibration_normal"}])


def _patch_materialize(output_dir: Path, stop_before_lance: bool = True):
    """Return a context manager that patches all heavy I/O in run_materialize_lance."""
    stop_side_effect = RuntimeError("stop-before-lance-write") if stop_before_lance else None
    return [
        patch("glitch_detection.r5_wob_staged._maybe_skip", return_value=None),
        patch(
            "glitch_detection.r5_wob_staged._validate_stage_marker",
            return_value=_FAKE_PREFLIGHT,
        ),
        patch(
            "glitch_detection.r5_wob_staged._validate_readiness_and_manifest",
            return_value=_FAKE_READINESS,
        ),
        patch("glitch_detection.r5_wob_staged._load_train_rows", return_value=[]),
        patch("glitch_detection.r5_wob_staged._render_eval_manifest", return_value=""),
        patch(
            "glitch_detection.r5_wob_staged._build_lance_from_rows",
            side_effect=stop_side_effect,
        ),
    ]


def _run_materialize(output_dir: Path) -> None:
    run_materialize_lance(
        readiness_json=Path("/fake/readiness.json"),
        eval_manifest=Path("/fake/eval_manifest.csv"),
        split_csv=Path("/fake/split.csv"),
        output_dir=output_dir,
        smoke=False,
        force=False,
    )


def test_stale_lance_dirs_cleaned_before_rematerialization():
    """Stale Lance dirs from a prior run are removed before any new LanceWriter call.

    This is the regression test for exit code 120: if the dirs are NOT cleaned,
    LanceWriter(mode='error') kills the process immediately with no Python output.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        stale = _make_stale_lance_dirs(output_dir)

        # Verify pre-condition: all three stale dirs exist
        for name, path in stale.items():
            assert path.exists(), f"Pre-condition: {name} should exist before call"

        patches = _patch_materialize(output_dir)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
        ):
            with pytest.raises(RuntimeError, match="stop-before-lance-write"):
                _run_materialize(output_dir)

        # All three stale dirs must have been removed before _build_lance_from_rows ran
        for name, path in stale.items():
            assert not path.exists(), (
                f"Stale Lance directory '{name}' was NOT cleaned before re-materialization. "
                "This would cause LanceWriter(mode='error') to call process::exit(120)."
            )


def test_stale_cleanup_removes_all_three_lance_dirs():
    """Cleanup covers all three: train, normal, and buggy Lance directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        # Only create two out of three stale dirs to verify partial-stale case
        (output_dir / TRAIN_LANCE_NAME).mkdir()
        (output_dir / BUGGY_LANCE_NAME).mkdir()

        patches = _patch_materialize(output_dir)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
        ):
            with pytest.raises(RuntimeError, match="stop-before-lance-write"):
                _run_materialize(output_dir)

        assert not (output_dir / TRAIN_LANCE_NAME).exists()
        assert not (output_dir / BUGGY_LANCE_NAME).exists()


def test_no_stale_dirs_does_not_crash():
    """When no stale Lance directories exist, cleanup is a no-op and does not crash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        # No stale dirs — just verify the cleanup path doesn't error
        patches = _patch_materialize(output_dir)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
        ):
            with pytest.raises(RuntimeError, match="stop-before-lance-write"):
                _run_materialize(output_dir)


def test_non_lance_files_in_output_dir_not_affected():
    """Cleanup must not delete unrelated files in the output dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        # Create a stale Lance dir and an unrelated file
        (output_dir / TRAIN_LANCE_NAME).mkdir()
        keeper = output_dir / "stage_preflight.json"
        keeper.write_text('{"stage": "preflight"}', encoding="utf-8")

        patches = _patch_materialize(output_dir)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
        ):
            with pytest.raises(RuntimeError, match="stop-before-lance-write"):
                _run_materialize(output_dir)

        # Unrelated file must survive
        assert keeper.exists(), "stage_preflight.json should not be deleted by Lance cleanup"
        # Stale Lance dir must be gone
        assert not (output_dir / TRAIN_LANCE_NAME).exists()


def test_smoke_stale_cleanup_uses_same_lance_names():
    """Cleanup uses the same Lance dir constants in smoke mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        _make_stale_lance_dirs(output_dir)

        smoke_preflight = {**_FAKE_PREFLIGHT, "smoke": True}
        smoke_readiness = (
            {"eval_manifest_sha256": "aabbcc"},
            [{"evaluation_role": "calibration_normal"}],
        )

        with (
            patch("glitch_detection.r5_wob_staged._maybe_skip", return_value=None),
            patch(
                "glitch_detection.r5_wob_staged._validate_stage_marker",
                return_value=smoke_preflight,
            ),
            patch(
                "glitch_detection.r5_wob_staged._validate_readiness_and_manifest",
                return_value=smoke_readiness,
            ),
            patch("glitch_detection.r5_wob_staged._load_train_rows", return_value=[]),
            patch("glitch_detection.r5_wob_staged._smoke_eval_rows", return_value=[]),
            patch("glitch_detection.r5_wob_staged._render_eval_manifest", return_value=""),
            patch(
                "glitch_detection.r5_wob_staged._build_lance_from_rows",
                side_effect=RuntimeError("stop"),
            ),
        ):
            with pytest.raises(RuntimeError, match="stop"):
                run_materialize_lance(
                    readiness_json=Path("/fake/readiness.json"),
                    eval_manifest=Path("/fake/eval_manifest.csv"),
                    split_csv=Path("/fake/split.csv"),
                    output_dir=output_dir,
                    smoke=True,
                    force=False,
                )

        for name in (TRAIN_LANCE_NAME, NORMAL_LANCE_NAME, BUGGY_LANCE_NAME):
            assert not (output_dir / name).exists(), f"{name} should be cleaned in smoke mode too"
