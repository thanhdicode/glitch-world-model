from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glitch_detection.lewm_gpu_profile_kaggle import (
    LeWMGPUProfileKaggleConfig,
    prepare_profile_kaggle_package,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare private LeWM GPU profile package.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--dataset-slug", required=True)
    parser.add_argument("--kernel-slug", required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = LeWMGPUProfileKaggleConfig(
        dataset_slug=args.dataset_slug,
        kernel_slug=args.kernel_slug,
        batch_size=args.batch_size,
        amp=args.amp,
        git_sha=_git(args.repo_root, "rev-parse", "HEAD"),
        branch=_git(args.repo_root, "branch", "--show-current"),
    )
    result = prepare_profile_kaggle_package(
        args.repo_root, args.source_root, args.output_root, config, dry_run=args.dry_run
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
