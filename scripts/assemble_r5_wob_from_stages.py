from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.r5_wob_staged import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_READINESS_JSON,
    assemble_r5_wob_from_stages,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble final R5-WOB outputs from completed staged artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS_JSON)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = assemble_r5_wob_from_stages(
        output_dir=args.output_dir,
        readiness_json=args.readiness_json,
        bootstrap_seed=args.bootstrap_seed,
        n_bootstrap=args.n_bootstrap,
        smoke=args.smoke,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
