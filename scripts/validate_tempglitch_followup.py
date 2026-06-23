from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a bounded TempGlitch pair-disjoint follow-up output directory."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint",
        help="Follow-up output directory to validate.",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=None,
        help="Optional explicit receipt path. Defaults to <output-dir>/followup_validator_receipt.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    from glitch_detection.tempglitch_followup import validate_tempglitch_followup_output

    args = build_parser().parse_args(argv)
    receipt_path = args.receipt_path or (args.output_dir / "followup_validator_receipt.json")
    result = validate_tempglitch_followup_output(
        output_dir=args.output_dir,
        receipt_path=receipt_path,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
