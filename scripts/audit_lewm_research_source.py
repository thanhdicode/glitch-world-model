from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_research import (
    LeWMResearchProtocol,
    audit_local_research_source,
    write_research_audit,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit non-locked TempGlitch research inputs.")
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--video-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--minimum-train-normal", type=int, default=30)
    parser.add_argument("--minimum-validation-normal", type=int, default=10)
    parser.add_argument("--minimum-validation-buggy", type=int, default=15)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    protocol = LeWMResearchProtocol(
        seed=args.seed,
        minimum_train_normal_episodes=args.minimum_train_normal,
        minimum_validation_normal_episodes=args.minimum_validation_normal,
        minimum_validation_buggy_episodes=args.minimum_validation_buggy,
    )
    payload = audit_local_research_source(
        args.metadata,
        args.split,
        args.video_root,
        protocol,
    )
    write_research_audit(payload, args.output)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
