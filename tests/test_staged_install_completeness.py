"""Regression test: the staged Kaggle shell script installs all packages needed
by every pipeline stage, including the LeWM model-loading stages (lewm_seed42/43/44).

Root cause of previous failure: stable-pretraining==0.1.7 was present in
requirements/lewm-runtime.txt but absent from the pip install block in
run_kaggle_r5_wob_staged.sh. Stages 1-3 (preflight, materialize_lance,
baseline_scores) do not import stable_pretraining, so they passed. Stage 5
(lewm_seed42) is the first to call LeWMAdapter.load() → hydra instantiate →
stable_pretraining.backbone.utils.vit_hf → ModuleNotFoundError, exit code 1.

This test parses the shell script to verify the install block explicitly lists
every package whose absence would silently break a downstream stage.
"""

from __future__ import annotations

import re
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_staged.sh"


def _extract_pip_packages(script_text: str) -> set[str]:
    """Return the set of bare package names found in the pip install block."""
    install_match = re.search(
        r"pip install.*?(?=\n\s*python -m pip install -e|\nrun_stage|\Z)",
        script_text,
        re.DOTALL,
    )
    assert install_match, "Could not locate pip install block in shell script"
    block = install_match.group()
    names: set[str] = set()
    for token in re.findall(r'"([A-Za-z0-9_\-]+)==[^"]*"', block):
        names.add(token.lower().replace("-", "_").replace("_", "-").lower())
    return names


def _normalise(pkg: str) -> str:
    return pkg.lower().replace("_", "-")


def test_script_exists():
    assert SCRIPT.is_file(), f"Shell script not found: {SCRIPT}"


def test_stable_worldmodel_installed():
    """stable-worldmodel must be present (required by all Lance and LeWM stages)."""
    text = SCRIPT.read_text(encoding="utf-8")
    assert "stable-worldmodel" in text, (
        "stable-worldmodel must appear in the pip install block of run_kaggle_r5_wob_staged.sh"
    )


def test_stable_pretraining_installed():
    """stable-pretraining must be present (required by lewm_seed42/43/44 stages).

    stable_pretraining.backbone.utils.vit_hf is referenced as the Hydra _target_
    in the LeWM checkpoint config. Without it, LeWMAdapter.load() raises:
      ModuleNotFoundError: No module named 'stable_pretraining'
    exiting with code 1 immediately when lewm_seed42 starts.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    assert "stable-pretraining" in text, (
        "stable-pretraining must appear in the pip install block of run_kaggle_r5_wob_staged.sh. "
        "It is required by lewm_seed42/43/44 stages via stable_pretraining.backbone.utils.vit_hf."
    )


def test_hydra_core_installed():
    """hydra-core must be present (used by LeWMAdapter.load via hydra.utils.instantiate)."""
    text = SCRIPT.read_text(encoding="utf-8")
    assert "hydra-core" in text, (
        "hydra-core must appear in the pip install block of run_kaggle_r5_wob_staged.sh"
    )


def test_lancedb_installed():
    """lancedb must be present (required by materialize_lance stage)."""
    text = SCRIPT.read_text(encoding="utf-8")
    assert "lancedb" in text, (
        "lancedb must appear in the pip install block of run_kaggle_r5_wob_staged.sh"
    )


def test_stable_pretraining_version_pinned():
    """stable-pretraining must be version-pinned for reproducibility."""
    text = SCRIPT.read_text(encoding="utf-8")
    match = re.search(r'"stable-pretraining==([^"]+)"', text)
    assert match, (
        "stable-pretraining must be version-pinned (e.g. stable-pretraining==0.1.7) "
        "in run_kaggle_r5_wob_staged.sh"
    )
    version = match.group(1)
    assert version == "0.1.7", (
        f"stable-pretraining is pinned to {version!r} but lewm-runtime.txt requires 0.1.7. "
        "Update both files to keep versions in sync."
    )


def test_stable_pretraining_matches_lewm_runtime():
    """Version in the shell script must match requirements/lewm-runtime.txt."""
    runtime_txt = Path(__file__).parent.parent / "requirements" / "lewm-runtime.txt"
    if not runtime_txt.exists():
        return
    runtime_content = runtime_txt.read_text(encoding="utf-8")
    rt_match = re.search(r"stable-pretraining==([^\s#]+)", runtime_content)
    if rt_match is None:
        return
    expected_version = rt_match.group(1)

    script_text = SCRIPT.read_text(encoding="utf-8")
    sh_match = re.search(r'"stable-pretraining==([^"]+)"', script_text)
    assert sh_match, "stable-pretraining missing from shell script"
    actual_version = sh_match.group(1)

    assert actual_version == expected_version, (
        f"Version mismatch: shell script has stable-pretraining=={actual_version} "
        f"but lewm-runtime.txt requires =={expected_version}. "
        "Keep both files in sync."
    )
