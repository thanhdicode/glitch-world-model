"""Validate R6 ablation outputs.

Usage
-----
    python scripts/validate_r6_ablations.py \
        --output-dir outputs/r6_tempglitch_ablations \
        [--wob-output-dir outputs/r6_wob_ablations]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_r6(output_dir: Path, wob_output_dir: Path | None = None) -> dict:
    """Validate R6 ablation outputs and return a status dict."""
    errors: list[str] = []
    warnings: list[str] = []
    completed: list[str] = []
    scaffolded: list[str] = []

    # Check TempGlitch ablation outputs
    if not output_dir.exists():
        warnings.append(f"TempGlitch ablation dir not found: {output_dir}")
    else:
        agg_file = output_dir / "r6_aggregation_ablation.json"
        if agg_file.exists():
            completed.append("aggregation")
        else:
            scaffolded.append("aggregation")

        for name in ["surprise_distance", "threshold_calibration", "failure_mode"]:
            result_file = output_dir / f"r6_{name}_ablation.json"
            if result_file.exists():
                completed.append(name)
            else:
                scaffolded.append(name)

    # Check WOB ablation outputs
    if wob_output_dir is not None:
        if not wob_output_dir.exists():
            warnings.append(f"WOB ablation dir not found: {wob_output_dir}")
        else:
            for name in [
                "aggregation",
                "surprise_distance",
                "threshold_calibration",
                "failure_mode",
                "action_conditioning",
            ]:
                result_file = wob_output_dir / f"r6_wob_{name}_ablation.json"
                if result_file.exists():
                    completed.append(f"wob_{name}")
                else:
                    scaffolded.append(f"wob_{name}")

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "completed_ablations": completed,
        "scaffolded_ablations": scaffolded,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate R6 ablation outputs.")
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Path to TempGlitch R6 ablation output directory",
    )
    p.add_argument(
        "--wob-output-dir",
        type=Path,
        default=None,
        help="Path to WOB R6 ablation output directory (optional)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_r6(args.output_dir, args.wob_output_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
