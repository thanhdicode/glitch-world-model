"""R6 TempGlitch ablation runner.

SCAFFOLD ONLY — do not run R6 until R5-WOB is validated and R5-XGAME is
complete.

Ablation categories:
1. CPU-safe ablations from existing R5 raw scores (aggregation, distance).
2. Threshold/calibration ablation (CPU-safe).
3. Failure-mode analysis (CPU-safe).
4. SIGReg ablation (requires GPU, Kaggle).
5. Training-budget ablation (requires GPU, Kaggle).

Usage
-----
    python scripts/run_r6_tempglitch_ablations.py \
        --r5-output-dir outputs/r5_tempglitch_identical_episode \
        --output-dir outputs/r6_tempglitch_ablations \
        --ablation aggregation \
        [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Ablation categories and their compute requirements
ABLATION_REGISTRY = {
    "aggregation": {
        "description": "Compare mean, max, top2_mean episode aggregations",
        "compute": "cpu",
        "requires_r5_scores": True,
        "requires_gpu": False,
    },
    "surprise_distance": {
        "description": "Compare L2 vs cosine surprise distance metrics",
        "compute": "cpu",
        "requires_r5_scores": True,
        "requires_gpu": False,
    },
    "threshold_calibration": {
        "description": "Sweep normal-calibrated thresholds and report F1/FPR trade-offs",
        "compute": "cpu",
        "requires_r5_scores": True,
        "requires_gpu": False,
    },
    "failure_mode": {
        "description": "Per-category and per-episode failure analysis",
        "compute": "cpu",
        "requires_r5_scores": True,
        "requires_gpu": False,
    },
    "sigreg": {
        "description": "SIGReg default vs zero — requires retraining",
        "compute": "kaggle_gpu",
        "requires_r5_scores": False,
        "requires_gpu": True,
    },
    "training_budget": {
        "description": "Reduced vs full training budget comparison",
        "compute": "kaggle_gpu",
        "requires_r5_scores": False,
        "requires_gpu": True,
    },
}


def run_aggregation_ablation(r5_dir: Path, output_dir: Path, dry_run: bool) -> dict:
    """Compare episode aggregation strategies from existing R5 raw scores."""
    comparison_csv = r5_dir / "r5_comparison.csv"
    if not comparison_csv.exists():
        return {"status": "MISSING_INPUT", "detail": str(comparison_csv)}

    if dry_run:
        return {"status": "DRY_RUN", "ablation": "aggregation"}

    # The R5 comparison already contains multiple aggregation rows.
    # This ablation groups them and reports per-aggregation summary.
    import csv

    agg_results: dict[str, list[dict]] = {}
    with open(comparison_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            agg = row.get("episode_aggregation", row.get("aggregation", "unknown"))
            agg_results.setdefault(agg, []).append(row)

    summary = {}
    for agg, rows in agg_results.items():
        aurocs = []
        for r in rows:
            try:
                aurocs.append(float(r.get("auroc", "nan")))
            except (ValueError, TypeError):
                pass
        summary[agg] = {
            "count": len(rows),
            "mean_auroc": sum(aurocs) / len(aurocs) if aurocs else None,
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "r6_aggregation_ablation.json", "w") as f:
        json.dump(summary, f, indent=2)

    return {"status": "COMPLETED", "ablation": "aggregation", "aggregations": list(summary.keys())}


def run_cpu_ablation(ablation: str, r5_dir: Path, output_dir: Path, dry_run: bool) -> dict:
    """Dispatch a CPU-safe ablation."""
    if ablation == "aggregation":
        return run_aggregation_ablation(r5_dir, output_dir, dry_run)

    # Other CPU ablations are scaffolded but not implemented yet
    return {
        "status": "SCAFFOLD_ONLY",
        "ablation": ablation,
        "detail": f"CPU ablation '{ablation}' is scaffolded but not yet implemented",
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="R6 TempGlitch ablation runner (scaffold).")
    p.add_argument(
        "--r5-output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "r5_tempglitch_identical_episode",
        help="Path to R5 TempGlitch output directory",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "r6_tempglitch_ablations",
        help="Output directory for R6 ablation results",
    )
    p.add_argument(
        "--ablation",
        choices=list(ABLATION_REGISTRY.keys()),
        required=True,
        help="Which ablation to run",
    )
    p.add_argument("--dry-run", action="store_true", help="Print plan without running")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    info = ABLATION_REGISTRY[args.ablation]

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

    result = run_cpu_ablation(args.ablation, args.r5_output_dir, args.output_dir, args.dry_run)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("COMPLETED", "DRY_RUN", "SCAFFOLD_ONLY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
