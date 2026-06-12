from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.kaggle_automation import KaggleOrchestrator
from glitch_detection.lewm_gate6_automation import (
    GATE6_AUTOMATION_STEPS,
    GATE6_LIVE_ACTION_FINGERPRINTS,
    Gate6AutomationConfig,
    Gate6AutomationHandlers,
)

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the resumable Gate 6 Kaggle automation.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "outputs" / "gate6" / "datasets",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=ROOT / "outputs" / "gate6" / "automation" / "lewm_gate6_pilot_v7",
    )
    parser.add_argument(
        "--dataset-slug",
        default="huynhdieuthanh/lewm-tempglitch-gate6-public-v7",
    )
    parser.add_argument(
        "--kernel-slug",
        default="huynhdieuthanh/lewm-gate6-pilot-v7",
    )
    parser.add_argument(
        "--dataset-visibility",
        choices=("private", "public"),
        default="public",
    )
    parser.add_argument(
        "--kernel-visibility",
        choices=("private", "public"),
        default="public",
    )
    parser.add_argument("--dataset-license", default="MIT")
    parser.add_argument(
        "--redistribution-allowed",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--accelerator", default="NvidiaTeslaT4")
    parser.add_argument("--poll-interval-seconds", type=int, default=60)
    parser.add_argument("--poll-timeout-seconds", type=int, default=6 * 60 * 60)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = Gate6AutomationConfig(
        repo_root=ROOT,
        source_root=args.source_root,
        run_root=args.run_root,
        dataset_slug=args.dataset_slug,
        kernel_slug=args.kernel_slug,
        dataset_visibility=args.dataset_visibility,
        kernel_visibility=args.kernel_visibility,
        dataset_license=args.dataset_license,
        redistribution_allowed=args.redistribution_allowed,
        accelerator=args.accelerator,
        poll_interval_seconds=args.poll_interval_seconds,
        poll_timeout_seconds=args.poll_timeout_seconds,
        live=args.live,
    )
    handlers = Gate6AutomationHandlers(config)
    orchestrator = KaggleOrchestrator(
        root=config.run_root,
        handlers=handlers.as_mapping(),
        steps=GATE6_AUTOMATION_STEPS,
        live_action_fingerprints=GATE6_LIVE_ACTION_FINGERPRINTS,
        dry_run=not args.live,
    )
    state = orchestrator.run()
    print(
        json.dumps(
            {
                "execution_mode": state.execution_mode,
                "current_step": state.current_step,
                "completed_steps": state.completed_steps,
                "kernel_status": state.kernel_status,
                "blocked_reason": state.blocked_reason,
                "artifact_paths": state.artifact_paths,
                "state_path": str(config.run_root / "state.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
