"""Validate an R5-XGAME cross-dataset comparison output directory.

Usage
-----
    python scripts/validate_r5_xgame_comparison.py \
        --output-dir outputs/r5_xgame_comparison
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def validate_r5_xgame(output_dir: Path) -> dict:
    """Validate R5-XGAME comparison outputs and return a status dict."""
    errors: list[str] = []
    warnings: list[str] = []

    # Required files
    comparison_csv = output_dir / "r5_xgame_comparison.csv"
    provenance_json = output_dir / "r5_xgame_provenance.json"

    if not comparison_csv.exists():
        errors.append(f"Missing comparison CSV: {comparison_csv}")
    if not provenance_json.exists():
        errors.append(f"Missing provenance JSON: {provenance_json}")

    # Check provenance
    if provenance_json.exists():
        with open(provenance_json) as f:
            prov = json.load(f)
        if prov.get("locked_test_materialized"):
            errors.append("CRITICAL: locked_test_materialized is True")
        if prov.get("locked_test_scored"):
            errors.append("CRITICAL: locked_test_scored is True")
        if prov.get("wob_status") != "VALIDATED":
            errors.append(f"WOB status is {prov.get('wob_status')!r}, not VALIDATED")
        receipt_hash = prov.get("wob_validation_receipt_sha256")
        if not receipt_hash or receipt_hash == "NOT_AVAILABLE":
            errors.append("WOB validation receipt hash is missing")

    # Check comparison CSV
    datasets_seen: set[str] = set()
    todo_count = 0
    row_count = 0
    if comparison_csv.exists():
        with open(comparison_csv, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                datasets_seen.add(row.get("dataset", ""))
                if "TODO" in row.values():
                    todo_count += 1

        if "TempGlitch" not in datasets_seen:
            errors.append("No TempGlitch rows in comparison CSV")
        if "WorldOfBugs" not in datasets_seen:
            errors.append("No WorldOfBugs rows in comparison CSV")
        if todo_count > 0:
            errors.append(f"{todo_count} rows contain TODO placeholders")

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": row_count,
        "datasets": sorted(datasets_seen),
        "todo_rows": todo_count,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate R5-XGAME comparison outputs.")
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Path to R5-XGAME comparison output directory",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_r5_xgame(args.output_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
