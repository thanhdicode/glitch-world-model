"""R6 WOB ablation runner.

SCAFFOLD ONLY — do not run until R5-WOB is validated.

WOB-specific ablation categories:
1. Aggregation ablation (CPU-safe, reuses R5-WOB raw scores).
2. Surprise-distance ablation (CPU-safe).
3. Threshold/calibration ablation (CPU-safe).
4. Failure-mode analysis (CPU-safe).
5. Action-conditioning ablation: zero-action vs real-action (requires GPU).
6. SIGReg ablation on WOB (requires GPU).

Usage
-----
    python scripts/run_r6_wob_ablations.py \
        --r5-wob-output-dir outputs/r5_wob_identical_episode \
        --output-dir outputs/r6_wob_ablations \
        --ablation aggregation \
        [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

WOB_ABLATION_REGISTRY = {
    "aggregation": {
        "description": "Compare mean, max, top2_mean episode aggregations on WOB",
        "compute": "cpu",
        "requires_gpu": False,
    },
    "surprise_distance": {
        "description": "Compare L2 vs cosine surprise distance on WOB",
        "compute": "cpu",
        "requires_gpu": False,
    },
    "threshold_calibration": {
        "description": "Sweep normal-calibrated thresholds on WOB scores",
        "compute": "cpu",
        "requires_gpu": False,
    },
    "failure_mode": {
        "description": "Per-game and per-episode WOB failure analysis",
        "compute": "cpu",
        "requires_gpu": False,
    },
    "action_conditioning": {
        "description": "Zero-action vs real-action WOB comparison (requires retraining)",
        "compute": "kaggle_gpu",
        "requires_gpu": True,
    },
    "sigreg": {
        "description": "SIGReg default vs zero on WOB (requires retraining)",
        "compute": "kaggle_gpu",
        "requires_gpu": True,
    },
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="R6 WOB ablation runner (scaffold).")
    p.add_argument(
        "--r5-wob-output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "r5_wob_identical_episode",
        help="Path to R5-WOB output directory",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "r6_wob_ablations",
        help="Output directory for R6 WOB ablation results",
    )
    p.add_argument(
        "--ablation",
        choices=list(WOB_ABLATION_REGISTRY.keys()),
        required=True,
        help="Which ablation to run",
    )
    p.add_argument("--dry-run", action="store_true", help="Print plan without running")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    info = WOB_ABLATION_REGISTRY[args.ablation]

    if not args.dry_run:
        print(
            "ERROR: R6 execution remains closed until validated R5-WOB and R5-XGAME "
            "outputs are available. Use --dry-run for scaffold inspection only.",
            file=sys.stderr,
        )
        return 1

    if info["requires_gpu"]:
        print(
            f"ERROR: Ablation '{args.ablation}' requires GPU (Kaggle). Do not run locally.",
            file=sys.stderr,
        )
        return 1

    result = {
        "status": "SCAFFOLD_ONLY",
        "ablation": args.ablation,
        "description": info["description"],
        "compute": info["compute"],
        "dry_run": args.dry_run,
        "detail": f"WOB ablation '{args.ablation}' is scaffolded but not yet implemented",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
