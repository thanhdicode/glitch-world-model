from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.kaggle_automation import (
    APPROVAL_STEPS,
    AutomationConfig,
    DefaultPhase6EHandlers,
    Phase6EKaggleOrchestrator,
)

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the resumable Phase 6E Kaggle state-machine automation."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and create approval requests without live upload/kernel actions.",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Allow approved live Kaggle actions. Never use during implementation verification.",
    )
    parser.add_argument("--approve-step", choices=sorted(APPROVAL_STEPS), default=None)
    parser.add_argument(
        "--automation-root",
        type=Path,
        default=ROOT / "outputs" / "kaggle_phase6e_automation",
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_phase3b",
    )
    parser.add_argument(
        "--split",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6d" / "seed_42" / "split.csv",
    )
    parser.add_argument(
        "--dataset-package-root",
        type=Path,
        default=ROOT / "outputs" / "kaggle_phase6e_dataset",
    )
    parser.add_argument(
        "--kernel-package-root",
        type=Path,
        default=ROOT / "outputs" / "kaggle_phase6e_kernel",
    )
    parser.add_argument(
        "--downloaded-root",
        type=Path,
        default=ROOT / "outputs" / "kaggle_phase6e_downloaded",
    )
    parser.add_argument(
        "--ingested-root",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6e" / "seed_42" / "ingested",
    )
    parser.add_argument(
        "--dataset-slug",
        default="thanhhuynhdieu/glitch-world-model-phase6e",
    )
    parser.add_argument(
        "--kernel-slug",
        default="thanhhuynhdieu/phase6e-video-autoencoder",
    )
    parser.add_argument("--branch", default="codex/phase6e-kaggle-video-autoencoder")
    parser.add_argument("--accelerator", default="NvidiaTeslaT4")
    parser.add_argument("--recursive-mode", choices=["zip", "tar"], default="zip")
    return parser


def build_config(args: argparse.Namespace) -> AutomationConfig:
    return AutomationConfig(
        repo_root=ROOT,
        automation_root=args.automation_root,
        processed_root=args.processed_root,
        split_path=args.split,
        dataset_package_root=args.dataset_package_root,
        kernel_package_root=args.kernel_package_root,
        downloaded_root=args.downloaded_root,
        ingested_root=args.ingested_root,
        dataset_slug=args.dataset_slug,
        kernel_slug=args.kernel_slug,
        branch=args.branch,
        accelerator=args.accelerator,
        recursive_mode=args.recursive_mode,
        dry_run=not args.live,
    )


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = build_config(args)
    handlers = DefaultPhase6EHandlers(config)
    orchestrator = Phase6EKaggleOrchestrator(
        root=config.automation_root,
        handlers=handlers.as_mapping(),
        dry_run=config.dry_run,
    )
    if args.approve_step:
        approval = orchestrator.approve_step(args.approve_step)
        print(f"Approved step: {args.approve_step}")
        print(f"Fingerprint: {approval['fingerprint']}")
        print("Approval is one-time and will be consumed when the live action starts.")
        return

    state = orchestrator.run()
    print(f"Current step: {state.current_step}")
    print(f"Completed steps: {', '.join(state.completed_steps)}")
    print(f"Requires approval: {state.requires_approval}")
    print(f"Blocked reason: {state.blocked_reason}")
    print(f"State path: {config.automation_root / 'state.json'}")
    print(json.dumps({"artifact_paths": state.artifact_paths}, indent=2))


if __name__ == "__main__":
    main()
