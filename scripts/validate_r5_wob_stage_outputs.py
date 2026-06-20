from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.r5_wob_staged import DEFAULT_OUTPUT_DIR, validate_stage_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate staged R5-WOB markers and output hashes."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(validate_stage_outputs(args.output_dir, smoke=args.smoke), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
