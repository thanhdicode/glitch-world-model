"""R5-XGAME: Cross-dataset comparison of TempGlitch R5 and WOB R5 results.

SKELETON ONLY — do not run until both R5-TempGlitch and R5-WOB outputs are
validated and ingested.

Usage
-----
    python scripts/run_r5_xgame_comparison.py \
        --tempglitch-metrics outputs/r5_tempglitch_identical_episode/r5_metrics.json \
        --wob-metrics outputs/r5_wob_identical_episode/r5_wob_metrics.json \
        --output-dir outputs/r5_xgame_comparison \
        [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_metrics(path: Path) -> dict:
    """Load and return a metrics JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    with open(path) as f:
        return json.load(f)


def _validate_wob_output(output_dir: Path) -> None:
    """Require a validator-passed R5-WOB directory before cross-dataset output."""
    validator_path = REPO_ROOT / "scripts" / "validate_r5_wob_evaluation.py"
    spec = importlib.util.spec_from_file_location("r5_wob_validator", validator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load R5-WOB validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_r5_wob(output_dir, module.DEFAULT_READINESS_JSON)


def _extract_best_rows(metrics: dict, dataset_name: str) -> list[dict]:
    """Extract the best AUROC/AUPRC rows per method family from metrics.

    Returns a list of dicts with keys:
        dataset, method, seed, scorer, aggregation, auroc, auprc
    """
    rows = []
    results = metrics.get("results", metrics.get("episode_results", []))
    if isinstance(results, list):
        for r in results:
            rows.append(
                {
                    "dataset": dataset_name,
                    "method": r.get("method", "unknown"),
                    "seed": r.get("seed", ""),
                    "scorer": r.get("scorer", r.get("window_scorer", "")),
                    "aggregation": r.get("aggregation", r.get("episode_aggregation", "")),
                    "auroc": r.get("auroc", ""),
                    "auprc": r.get("auprc", ""),
                }
            )
    return rows


def build_comparison_table(
    tempglitch_metrics: dict,
    wob_metrics: dict | None,
) -> list[dict]:
    """Build a cross-dataset comparison table.

    If wob_metrics is None, WOB rows are marked as TODO.
    """
    rows = _extract_best_rows(tempglitch_metrics, "TempGlitch")
    if wob_metrics is not None:
        rows.extend(_extract_best_rows(wob_metrics, "WorldOfBugs"))
    else:
        rows.append(
            {
                "dataset": "WorldOfBugs",
                "method": "TODO",
                "seed": "TODO",
                "scorer": "TODO",
                "aggregation": "TODO",
                "auroc": "TODO",
                "auprc": "TODO",
            }
        )
    return rows


def write_comparison_csv(rows: list[dict], output_path: Path) -> None:
    """Write the comparison table to CSV."""
    fieldnames = ["dataset", "method", "seed", "scorer", "aggregation", "auroc", "auprc"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_provenance(
    output_dir: Path,
    tempglitch_path: Path,
    wob_path: Path | None,
    dry_run: bool,
) -> None:
    """Write provenance metadata."""
    provenance = {
        "stage": "R5-XGAME",
        "tempglitch_metrics_path": str(tempglitch_path),
        "wob_metrics_path": str(wob_path) if wob_path else "NOT_AVAILABLE",
        "wob_status": "VALIDATED" if wob_path and wob_path.exists() else "PENDING",
        "dry_run": dry_run,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    with open(output_dir / "r5_xgame_provenance.json", "w") as f:
        json.dump(provenance, f, indent=2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="R5-XGAME: Cross-dataset comparison (skeleton).")
    p.add_argument(
        "--tempglitch-metrics",
        type=Path,
        default=REPO_ROOT / "outputs" / "r5_tempglitch_identical_episode" / "r5_metrics.json",
        help="Path to TempGlitch R5 metrics JSON",
    )
    p.add_argument(
        "--wob-metrics",
        type=Path,
        default=None,
        help="Path to WOB R5 metrics JSON (omit if not yet available)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "r5_xgame_comparison",
        help="Output directory for comparison artifacts",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Load TempGlitch metrics
    if not args.tempglitch_metrics.exists():
        print(f"ERROR: TempGlitch metrics not found: {args.tempglitch_metrics}", file=sys.stderr)
        return 1

    tempglitch = _load_metrics(args.tempglitch_metrics)

    if args.wob_metrics is None or not args.wob_metrics.exists():
        if args.dry_run:
            print("DRY RUN: R5-XGAME remains closed until a validated R5-WOB metrics file exists.")
            return 0
        print("ERROR: R5-XGAME requires a validated --wob-metrics file.", file=sys.stderr)
        return 1

    try:
        _validate_wob_output(args.wob_metrics.parent)
    except (ImportError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: R5-WOB validation gate is closed: {exc}", file=sys.stderr)
        return 1

    wob = _load_metrics(args.wob_metrics)

    # Build comparison
    rows = build_comparison_table(tempglitch, wob)

    if args.dry_run:
        print(f"DRY RUN: Would write {len(rows)} rows to {args.output_dir}")
        print(json.dumps(rows[:3], indent=2))
        return 0

    # Write outputs
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_comparison_csv(rows, args.output_dir / "r5_xgame_comparison.csv")
    write_provenance(args.output_dir, args.tempglitch_metrics, args.wob_metrics, args.dry_run)
    print(f"R5-XGAME comparison written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
