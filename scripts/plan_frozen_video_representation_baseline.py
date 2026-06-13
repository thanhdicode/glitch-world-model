from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glitch_detection.frozen_video_representation import (  # noqa: E402
    FrozenVideoRepresentationConfig,
    plan_frozen_video_representation_baseline,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan the optional frozen video-representation baseline."
    )
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--candidate",
        dest="candidates",
        action="append",
        default=None,
        help="Optional candidate name; may be passed multiple times.",
    )
    parser.add_argument("--allow-downloads", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = FrozenVideoRepresentationConfig(
        candidates=tuple(args.candidates or ("videomae-small", "timesformer-small")),
        allow_downloads=args.allow_downloads,
        blocks_lewm_critical_path=False,
    )
    print(json.dumps(plan_frozen_video_representation_baseline(args.output_root, config), indent=2))


if __name__ == "__main__":
    main()
