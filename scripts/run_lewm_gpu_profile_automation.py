from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glitch_detection.lewm_gpu_profile_automation import (
    ProfileAutomationConfig,
    run_profile_attempt_ladder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run private LeWM GPU profile automation.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--lance-root", required=True, type=Path)
    parser.add_argument("--source-audit", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--dataset-slug", required=True)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--accelerator", default="NvidiaTeslaT4")
    parser.add_argument("--poll-interval-seconds", type=int, default=60)
    parser.add_argument("--poll-timeout-seconds", type=int, default=6 * 60 * 60)
    args = parser.parse_args()
    result = run_profile_attempt_ladder(
        ProfileAutomationConfig(
            repo_root=args.repo_root,
            lance_root=args.lance_root,
            source_audit=args.source_audit,
            run_root=args.run_root,
            dataset_slug=args.dataset_slug,
            live=args.live,
            amp=args.amp,
            accelerator=args.accelerator,
            poll_interval_seconds=args.poll_interval_seconds,
            poll_timeout_seconds=args.poll_timeout_seconds,
        )
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
