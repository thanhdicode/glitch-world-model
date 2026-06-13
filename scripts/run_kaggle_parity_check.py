from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glitch_detection.lewm_gpu_profile_kaggle import (  # noqa: E402
    LeWMGPUProfileKaggleConfig,
    render_profile_kernel,
)

TRAIN_DATASET = "tempglitch_train_normal_all_local.lance"
VALIDATION_DATASET = "tempglitch_validation_normal_all_local.lance"


def run_utf8_subprocess(command: list[str], *, cwd: Path, environment: dict[str, str]) -> Any:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def kernel_entrypoint_is_guarded(source: str) -> bool:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        if "__name__" not in ast.unparse(node.test) or "__main__" not in ast.unparse(node.test):
            continue
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "main"
            for child in ast.walk(node)
        ):
            return True
    return False


def _spawn_probe_source() -> str:
    return """import multiprocessing as mp

def worker(value):
    return value + 1

def main():
    context = mp.get_context("spawn")
    with context.Pool(1) as pool:
        assert pool.map(worker, [1, 2]) == [2, 3]
    print("SPAWN_PARITY_OK")

if __name__ == "__main__":
    main()
"""


def run_kaggle_parity_check(
    repo_root: Path,
    lance_root: Path,
    output: Path,
    *,
    git_sha: str,
) -> dict[str, Any]:
    required = [lance_root / TRAIN_DATASET, lance_root / VALIDATION_DATASET]
    missing = [str(path) for path in required if not path.is_dir()]
    if missing:
        raise FileNotFoundError(
            "parity requires local research MVP Lance datasets: " + ", ".join(missing)
        )
    config = LeWMGPUProfileKaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-parity-private",
        kernel_slug="huynhdieuthanh/lewm-parity-kernel",
        batch_size=8,
        git_sha=git_sha,
        branch="parity",
        amp=True,
    )
    kernel = render_profile_kernel(
        config,
        {"optimizer_updates": 500, "validation_batches": 8, "git_sha": git_sha},
    )
    if not kernel_entrypoint_is_guarded(kernel):
        raise RuntimeError("Rendered Kaggle kernel entrypoint is not protected by __main__ guard.")
    environment = dict(os.environ)
    environment.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    with tempfile.TemporaryDirectory(prefix="lewm-kaggle-parity-") as temporary:
        root = Path(temporary)
        kernel_path = root / "rendered_kernel.py"
        kernel_path.write_text(kernel, encoding="utf-8")
        bootstrap_environment = {
            **environment,
            "LEWM_PROFILE_BOOTSTRAP_ONLY": "1",
        }
        bootstrap = run_utf8_subprocess(
            [sys.executable, str(kernel_path)], cwd=root, environment=bootstrap_environment
        )
        if bootstrap.returncode or "LEWM_PROFILE_BOOTSTRAP_OK" not in bootstrap.stdout:
            raise RuntimeError("Rendered Kaggle kernel bootstrap parity failed.")
        spawn_path = root / "spawn_probe.py"
        spawn_path.write_text(_spawn_probe_source(), encoding="utf-8")
        spawn = run_utf8_subprocess(
            [sys.executable, str(spawn_path)], cwd=root, environment=environment
        )
        if spawn.returncode or "SPAWN_PARITY_OK" not in spawn.stdout:
            raise RuntimeError("Spawn parity failed: " + (spawn.stderr or spawn.stdout))
    receipt = {
        "pass": True,
        "git_sha": git_sha,
        "kernel_guard_verified": True,
        "rendered_kernel_bootstrap_verified": True,
        "spawn_verified": True,
        "utf8_decode_policy": "utf-8/errors=replace",
        "train_dataset_present": True,
        "validation_normal_dataset_present": True,
        "validation_buggy_used": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "training_performed": False,
        "evidence_class": "infrastructure-parity-only",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the offline Kaggle parity gate.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--lance-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=args.repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout.strip()
    print(
        json.dumps(
            run_kaggle_parity_check(args.repo_root, args.lance_root, args.output, git_sha=git_sha),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
