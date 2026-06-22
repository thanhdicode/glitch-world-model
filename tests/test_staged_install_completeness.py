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
XGAME_SCRIPT = (
    Path(__file__).parent.parent / "cloud" / "wob_r5_xgame" / "run_kaggle_r5_xgame_staged.sh"
)
KAGGLE_RUNTIME = Path(__file__).parent.parent / "requirements" / "kaggle_runtime.txt"
_LANCEDB_MIN_VERSION = "0.30.0"
_PYLANCE_MIN_VERSION = "4.0.0"


def _parse_pin(text: str, package: str) -> str:
    match = re.search(rf'"{re.escape(package)}==([^"]+)"', text)
    assert match, f"{package} must be version-pinned in run_kaggle_r5_wob_staged.sh"
    return match.group(1)


def _parse_runtime_pin(package: str) -> str:
    text = KAGGLE_RUNTIME.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(package)}==([^\s#]+)$", text, re.MULTILINE)
    assert match, f"{package} must be version-pinned in requirements/kaggle_runtime.txt"
    return match.group(1)


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


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


def test_lancedb_pin_meets_stable_worldmodel_floor():
    """stable-worldmodel 0.1.1 expects a LanceDB API with DBConnection.list_tables()."""
    version = _parse_pin(SCRIPT.read_text(encoding="utf-8"), "lancedb")
    assert _version_tuple(version) >= _version_tuple(_LANCEDB_MIN_VERSION), (
        f"lancedb=={version} is too old for stable-worldmodel 0.1.1. "
        f"Pin at least {_LANCEDB_MIN_VERSION} so LanceWriter.__enter__ can call "
        "DBConnection.list_tables()."
    )


def test_pylance_pin_meets_stable_worldmodel_floor():
    """stable-worldmodel 0.1.1 metadata requires pylance>=4.0.0."""
    version = _parse_pin(SCRIPT.read_text(encoding="utf-8"), "pylance")
    assert _version_tuple(version) >= _version_tuple(_PYLANCE_MIN_VERSION), (
        f"pylance=={version} is below the stable-worldmodel 0.1.1 metadata floor "
        f"of {_PYLANCE_MIN_VERSION}."
    )


def test_lancedb_and_pylance_match_optional_runtime_file():
    """Keep the staged shell script aligned with requirements/kaggle_runtime.txt."""
    script_text = SCRIPT.read_text(encoding="utf-8")
    assert _parse_pin(script_text, "lancedb") == _parse_runtime_pin("lancedb")
    assert _parse_pin(script_text, "pylance") == _parse_runtime_pin("pylance")


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


# --- R5-XGame launcher install-completeness ---------------------------------
#
# The R5-XGame staged launcher (cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh)
# was originally written without any runtime install block: it only ran
# `pip install -e .`, so the materialize stage crashed with
#   ModuleNotFoundError: No module named 'stable_worldmodel'
# followed by LeWMDataUnavailableError. These tests enforce that the X-Game
# launcher installs the same isolated LeWM runtime the R5-WOB launcher does, so
# a future edit that drops a dependency is caught in CI rather than on Kaggle.


def test_xgame_script_exists():
    assert XGAME_SCRIPT.is_file(), f"Shell script not found: {XGAME_SCRIPT}"


def test_xgame_stable_worldmodel_installed():
    """stable-worldmodel must be present (required by materialize/baseline/score stages)."""
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    assert "stable-worldmodel" in text, (
        "stable-worldmodel must appear in the pip install block of "
        "run_kaggle_r5_xgame_staged.sh"
    )


def test_xgame_stable_pretraining_installed():
    """stable-pretraining must be present (required by train_lewm/lewm_score stages)."""
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    assert "stable-pretraining" in text, (
        "stable-pretraining must appear in the pip install block of "
        "run_kaggle_r5_xgame_staged.sh. It is required by train_lewm/lewm_score via "
        "stable_pretraining.backbone.utils.vit_hf."
    )


def test_xgame_hydra_core_installed():
    """hydra-core must be present (used by LeWMAdapter.load via hydra.utils.instantiate)."""
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    assert "hydra-core" in text, (
        "hydra-core must appear in the pip install block of run_kaggle_r5_xgame_staged.sh"
    )


def test_xgame_lancedb_installed():
    """lancedb must be present (required by the materialize stage)."""
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    assert "lancedb" in text, (
        "lancedb must appear in the pip install block of run_kaggle_r5_xgame_staged.sh"
    )


def test_xgame_lancedb_pin_meets_stable_worldmodel_floor():
    """stable-worldmodel 0.1.1 expects a LanceDB API with DBConnection.list_tables()."""
    version = _parse_pin(XGAME_SCRIPT.read_text(encoding="utf-8"), "lancedb")
    assert _version_tuple(version) >= _version_tuple(_LANCEDB_MIN_VERSION), (
        f"lancedb=={version} is too old for stable-worldmodel 0.1.1. "
        f"Pin at least {_LANCEDB_MIN_VERSION}."
    )


def test_xgame_pylance_pin_meets_stable_worldmodel_floor():
    """stable-worldmodel 0.1.1 metadata requires pylance>=4.0.0."""
    version = _parse_pin(XGAME_SCRIPT.read_text(encoding="utf-8"), "pylance")
    assert _version_tuple(version) >= _version_tuple(_PYLANCE_MIN_VERSION), (
        f"pylance=={version} is below the stable-worldmodel 0.1.1 metadata floor "
        f"of {_PYLANCE_MIN_VERSION}."
    )


def test_xgame_lancedb_and_pylance_match_optional_runtime_file():
    """Keep the X-Game launcher aligned with requirements/kaggle_runtime.txt."""
    script_text = XGAME_SCRIPT.read_text(encoding="utf-8")
    assert _parse_pin(script_text, "lancedb") == _parse_runtime_pin("lancedb")
    assert _parse_pin(script_text, "pylance") == _parse_runtime_pin("pylance")


def test_xgame_stable_pretraining_version_matches_runtime():
    """stable-pretraining must be pinned to the version in lewm-runtime.txt (0.1.7)."""
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r'"stable-pretraining==([^"]+)"', text)
    assert match, "stable-pretraining must be version-pinned in run_kaggle_r5_xgame_staged.sh"
    assert match.group(1) == "0.1.7", (
        f"stable-pretraining is pinned to {match.group(1)!r} but lewm-runtime.txt requires 0.1.7."
    )


def test_xgame_stable_pretraining_not_in_no_deps_block():
    """stable-pretraining must NOT be inside the --no-deps install block.

    Its 24 transitive dependencies (lightning, timm, torchmetrics, …) would be
    skipped by --no-deps, causing ModuleNotFoundError at training time.
    """
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    no_deps_match = re.search(
        r"pip install[^\n]*--no-deps(.*?)(?=\npython -m pip install|\Z)",
        text,
        re.DOTALL,
    )
    assert no_deps_match, "Expected a --no-deps pip install block in the X-Game launcher"
    assert "stable-pretraining" not in no_deps_match.group(1), (
        "stable-pretraining must NOT be inside the --no-deps pip install block. "
        "Install it in a separate 'pip install stable-pretraining==X.Y.Z' call."
    )


def test_xgame_verifies_runtime_imports_before_stages():
    """The launcher must fail fast by importing the runtime before the stage loop."""
    text = XGAME_SCRIPT.read_text(encoding="utf-8")
    assert "stable_worldmodel.data" in text, (
        "The X-Game launcher must verify 'from stable_worldmodel.data import ...' before "
        "running stages so a missing runtime fails in seconds, not after materialize."
    )
    verify_index = text.find("stable_worldmodel.data")
    stage_index = text.find("--stage materialize")
    if stage_index == -1:
        stage_index = text.find("for stage in")
    assert verify_index != -1 and stage_index != -1 and verify_index < stage_index, (
        "The import-verification step must run before the materialize stage."
    )
