"""Regression tests: the staged Kaggle shell script installs all packages needed
by every pipeline stage, including the LeWM model-loading stages (lewm_seed42/43/44).

Two layered failures were fixed in this area:

Failure 1 — stable-pretraining absent:
  stable-pretraining==0.1.7 was in requirements/lewm-runtime.txt but missing from
  the pip install block entirely. Stages 1-3 pass because they never import
  stable_pretraining. Stage 5 (lewm_seed42) is the first to call
  LeWMAdapter.load() → hydra instantiate → stable_pretraining.backbone.utils.vit_hf
  → ModuleNotFoundError, exit code 1.

Failure 2 — stable-pretraining installed with --no-deps (same symptom):
  After adding stable-pretraining to the --no-deps block (fixing failure 1 at the
  name level), its 24 transitive dependencies (lightning, timm, torchmetrics, etc.)
  were still absent. The first missing dep encountered at import time was:
    stable_pretraining/data/datasets.py → import lightning as pl
    ModuleNotFoundError: No module named 'lightning'
  Fix: install stable-pretraining in a SEPARATE pip install call WITHOUT --no-deps
  so pip resolves its full dependency tree automatically.
"""

from __future__ import annotations

import re
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "cloud" / "wob_r5_eval" / "run_kaggle_r5_wob_staged.sh"


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


def test_stable_pretraining_not_in_no_deps_block():
    """stable-pretraining must NOT be inside the --no-deps install block.

    stable-pretraining==0.1.7 has 24 transitive dependencies (lightning, timm,
    torchmetrics, submitit, wandb, …). Installing with --no-deps leaves them
    all absent. The first one encountered at import time is:

        stable_pretraining/data/datasets.py:28  import lightning as pl
        ModuleNotFoundError: No module named 'lightning'

    Fix: install stable-pretraining in a SEPARATE pip install call (without
    --no-deps) so pip resolves the full dependency tree automatically.
    """
    text = SCRIPT.read_text(encoding="utf-8")

    # Find the --no-deps block (everything between pip install --no-deps and the
    # separate stable-pretraining install or the next pip install -e)
    no_deps_match = re.search(
        r"pip install[^\n]*--no-deps(.*?)(?=\npython -m pip install|\nrun_stage|\Z)",
        text,
        re.DOTALL,
    )
    assert no_deps_match, "Expected a --no-deps pip install block in the shell script"
    no_deps_block = no_deps_match.group(1)

    assert "stable-pretraining" not in no_deps_block, (
        "stable-pretraining must NOT be inside the --no-deps pip install block. "
        "It has 24 transitive dependencies (lightning, timm, torchmetrics, etc.) "
        "that --no-deps would skip, causing ModuleNotFoundError at runtime. "
        "Install it in a separate 'pip install stable-pretraining==X.Y.Z' call."
    )
