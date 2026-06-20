"""R5-XGAME: Cross-dataset comparison of TempGlitch R5 and WOB R5 results.

SKELETON ONLY — do not run until both R5-TempGlitch and R5-WOB outputs are
validated and ingested.

Usage
-----
    python scripts/run_r5_xgame_comparison.py \
        --tempglitch-metrics outputs/r5_tempglitch_identical_episode/r5_metrics.json \
        --wob-metrics outputs/r5_wob_identical_episode/r5_wob_metrics.json \
        --wob-validation-receipt \
            outputs/r5_wob_identical_episode/r5_wob_validation_receipt.json \
        --output-dir outputs/r5_xgame_comparison \
        [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_wob_output(output_dir: Path, receipt_path: Path) -> dict:
    """Require direct validation plus a hash-bound post-run intake receipt."""
    validator_path = REPO_ROOT / "scripts" / "validate_r5_wob_evaluation.py"
    spec = importlib.util.spec_from_file_location("r5_wob_validator", validator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load R5-WOB validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.validate_r5_wob(output_dir, module.DEFAULT_READINESS_JSON)
    if result.get("status") != "r5_wob_validated":
        raise ValueError("R5-WOB validator did not return r5_wob_validated")

    if not receipt_path.is_file():
        raise ValueError(f"R5-WOB validation receipt is missing: {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    if receipt.get("status") != "r5_wob_validated":
        raise ValueError("R5-WOB validation receipt status is not r5_wob_validated")
    if receipt.get("locked_test_materialized") is not False:
        raise ValueError("R5-WOB receipt does not keep locked_test_materialized false")
    if receipt.get("locked_test_scored") is not False:
        raise ValueError("R5-WOB receipt does not keep locked_test_scored false")

    for filename, expected_hash in receipt.get("output_hashes", {}).items():
        path = output_dir / filename
        if not path.is_file() or _sha256_file(path) != expected_hash:
            raise ValueError(f"R5-WOB receipt hash mismatch for {filename}")
    if "r5_wob_metrics.json" not in receipt.get("output_hashes", {}):
        raise ValueError("R5-WOB receipt is not bound to r5_wob_metrics.json")
    return result


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
    wob_receipt_path: Path | None,
    dry_run: bool,
) -> None:
    """Write provenance metadata."""
    provenance = {
        "stage": "R5-XGAME",
        "tempglitch_metrics_path": str(tempglitch_path),
        "wob_metrics_path": str(wob_path) if wob_path else "NOT_AVAILABLE",
        "wob_validation_receipt_path": (
            str(wob_receipt_path) if wob_receipt_path else "NOT_AVAILABLE"
        ),
        "wob_validation_receipt_sha256": (
            _sha256_file(wob_receipt_path)
            if wob_receipt_path and wob_receipt_path.is_file()
            else "NOT_AVAILABLE"
        ),
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
        "--wob-validation-receipt",
        type=Path,
        default=None,
        help="Hash-bound receipt written by verify_r5_wob_upload.py",
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

    if args.wob_metrics.name != "r5_wob_metrics.json":
        print("ERROR: --wob-metrics must name canonical r5_wob_metrics.json.", file=sys.stderr)
        return 1
    if args.wob_validation_receipt is None:
        print("ERROR: R5-XGAME requires --wob-validation-receipt.", file=sys.stderr)
        return 1

    try:
        _validate_wob_output(args.wob_metrics.parent, args.wob_validation_receipt)
    except (ImportError, KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
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
    write_provenance(
        args.output_dir,
        args.tempglitch_metrics,
        args.wob_metrics,
        args.wob_validation_receipt,
        args.dry_run,
    )
    print(f"R5-XGAME comparison written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
