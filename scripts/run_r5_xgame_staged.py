"""Validate the R5-XGame split contract before any live evaluation is authorized."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from glitch_detection.r5_xgame_protocol import validate_r5_xgame_manifest

PLANNED_OUTPUTS = (
    "r5_xgame_manifest.csv",
    "r5_xgame_window_manifest.csv",
    "r5_xgame_baseline_scores.csv",
    "r5_xgame_lewm_scores_seed42.csv",
    "r5_xgame_lewm_scores_seed43.csv",
    "r5_xgame_lewm_scores_seed44.csv",
    "r5_xgame_episode_scores.csv",
    "r5_xgame_comparison.csv",
    "r5_xgame_metrics.json",
    "R5_XGAME_REPORT.md",
    "r5_xgame_provenance.json",
)
MISSING_LIVE_REQUIREMENTS = (
    "a staged R5-XGame materialize/train/score implementation",
    "fresh seed42/43/44 artifacts trained on the frozen 36-row train_normal split",
    "Kaggle-mounted WOB archives resolving every frozen non-locked source",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the R5-XGame non-locked split.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true", help="Validate metadata only; never score.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report live-run readiness; never score."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows and (args.smoke or args.dry_run):
        print(
            json.dumps(
                {
                    "status": "awaiting_manifest_rows",
                    "manifest": str(args.manifest),
                    "smoke": args.smoke,
                    "dry_run": args.dry_run,
                    "SAFE_TO_RUN_KAGGLE": False,
                    "missing_live_requirements": list(MISSING_LIVE_REQUIREMENTS),
                    "planned_outputs": list(PLANNED_OUTPUTS),
                    "validation_buggy_used_for_fit_select": False,
                    "locked_test_materialized": False,
                    "locked_test_scored": False,
                },
                indent=2,
            )
        )
        return 0
    counts = validate_r5_xgame_manifest(rows)
    result = {
        "status": "r5_xgame_split_validated",
        "manifest": str(args.manifest),
        "counts": counts,
        "smoke": args.smoke,
        "dry_run": args.dry_run,
        "SAFE_TO_RUN_KAGGLE": False,
        "missing_live_requirements": list(MISSING_LIVE_REQUIREMENTS),
        "planned_outputs": list(PLANNED_OUTPUTS),
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
