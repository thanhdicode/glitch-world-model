"""Validate R6 ablation outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _validate_controlled_pairs(output_dir: Path) -> dict[str, Any]:
    receipt_path = output_dir / "r6_ablation_receipt.json"
    pairs_path = output_dir / "r6_controlled_pairs.json"
    if not receipt_path.is_file() or not pairs_path.is_file():
        return {"status": "missing", "pair_count": 0}
    receipt = _read_json(receipt_path)
    pairs_payload = _read_json(pairs_path)
    if receipt.get("locked_test_materialized") is not False:
        raise ValueError("R6 ablation receipt must keep locked_test_materialized=false.")
    if receipt.get("locked_test_scored") is not False:
        raise ValueError("R6 ablation receipt must keep locked_test_scored=false.")
    variants = {row["variant_name"]: row for row in receipt.get("executed_variants", [])}
    pair_count = 0
    for pair in pairs_payload.get("pairs", []):
        pair_count += 1
        control = variants[pair["control_variant"]]["training_metadata"]
        treatment = variants[pair["treatment_variant"]]["training_metadata"]
        if control["dataset_hashes"] != treatment["dataset_hashes"]:
            raise ValueError(f"R6 pair {pair} does not share identical dataset hashes.")
        if control["config"]["seed"] != treatment["config"]["seed"]:
            raise ValueError(f"R6 pair {pair} does not share an identical seed.")
        if control.get("sigreg_enabled") not in {True, False}:
            raise ValueError("R6 training metadata must expose sigreg_enabled.")
        if treatment.get("sigreg_enabled") not in {True, False}:
            raise ValueError("R6 training metadata must expose sigreg_enabled.")
        if pair["pair_type"] == "sigreg":
            differing = {
                field
                for field in ("sigreg_enabled", "action_mode")
                if control.get(field) != treatment.get(field)
            }
            if differing != {"sigreg_enabled"}:
                raise ValueError(
                    f"R6 SIGReg pair must differ only in sigreg_enabled; found {sorted(differing)}."
                )
        elif pair["pair_type"] == "action_conditioning":
            differing = {
                field
                for field in ("sigreg_enabled", "action_mode")
                if control.get(field) != treatment.get(field)
            }
            if differing != {"action_mode"}:
                raise ValueError(
                    f"R6 action pair must differ only in action_mode; found {sorted(differing)}."
                )
        else:
            raise ValueError(f"Unsupported R6 pair_type: {pair['pair_type']!r}")
    return {
        "status": "validated" if pair_count else "declared_only",
        "pair_count": pair_count,
    }


def validate_r6(output_dir: Path, wob_output_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    completed: list[str] = []
    scaffolded: list[str] = []

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
        controlled = _validate_controlled_pairs(output_dir)
        if controlled["status"] == "validated":
            completed.append("controlled_pairs")
        elif controlled["status"] == "declared_only":
            scaffolded.append("controlled_pairs")

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
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--wob-output-dir", type=Path, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_r6(args.output_dir, args.wob_output_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
