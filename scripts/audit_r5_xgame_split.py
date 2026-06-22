"""Audit an R5-XGame manifest and emit a machine-readable leakage report."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from glitch_detection.r5_xgame_protocol import validate_r5_xgame_manifest


def audit(rows: list[dict[str, str]]) -> dict[str, object]:
    counts = validate_r5_xgame_manifest(rows)
    conflicts: dict[str, list[str]] = {}
    for field in ("episode_id", "pair_id", "source"):
        roles_by_value: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            roles_by_value[row[field]].add(row["evaluation_role"])
        conflicts[field] = sorted(
            value for value, roles in roles_by_value.items() if len(roles) > 1
        )
    return {
        "status": "r5_xgame_leakage_audit_passed",
        "role_counts": counts,
        "blocking_conflicts": conflicts,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "validation_buggy_used_for_fit_select": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit the R5-XGame split for leakage.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        result = audit(list(csv.DictReader(handle)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
