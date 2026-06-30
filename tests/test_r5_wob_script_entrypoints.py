from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"


def test_r5_wob_entrypoints_work_with_src_only_pythonpath():
    """Catch notebook-style failures where repo root is absent but src is available.

    The staged scripts are often invoked as:
        python scripts/run_r5_wob_stage.py ...

    In that execution mode Python does not automatically add the repo root to
    sys.path, so top-level non-packaged imports like ``cloud.*`` break even if
    ``glitch_detection`` itself is importable. This regression test forces the
    subprocess to see only ``src`` on PYTHONPATH and verifies the wrappers still
    reach argparse help successfully.
    """

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    scripts = [
        REPO_ROOT / "scripts" / "run_r5_wob_stage.py",
        REPO_ROOT / "scripts" / "validate_r5_wob_stage_outputs.py",
        REPO_ROOT / "scripts" / "assemble_r5_wob_from_stages.py",
        REPO_ROOT / "scripts" / "run_kc_wob_binary.py",
        REPO_ROOT / "scripts" / "validate_kc_wob_binary_output.py",
    ]

    for script in scripts:
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, (
            f"{script.name} failed with src-only PYTHONPATH.\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
        assert "usage:" in completed.stdout.lower()
