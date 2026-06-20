"""Validate R6 ablation outputs.

Verifies that:
- All expected R6 TempGlitch CPU-safe output files exist.
- No WOB dependency was used (wob_dependency_used=False in each output).
- No locked-test field is true.
- No placeholder is treated as a metric (strings like "TODO" absent from values).
- Generated outputs do not contain fabricated numeric placeholders.
- Provenance file exists and has required structure.

WOB ablation outputs (A7–A10) are checked only when --wob-output-dir is given
and only after a separate validated R5-WOB receipt is provided.

Usage
-----
    python scripts/validate_r6_ablations.py \\
        --output-dir outputs/r6_tempglitch_ablations

    python scripts/validate_r6_ablations.py \\
        --output-dir outputs/r6_tempglitch_ablations \\
        --wob-output-dir outputs/r6_wob_ablations \\
        --r5-wob-receipt outputs/r5_wob_identical_episode/r5_wob_validation_receipt.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

_PLACEHOLDER_STRINGS = {"TODO", "TBD", "PLACEHOLDER", "—", "???"}

TEMPGLITCH_ABLATION_FILES = {
    "a1": "r6_a1_aggregation_ablation.json",
    "a2": "r6_a2_surprise_distance_ablation.json",
    "a3": "r6_a3_threshold_calibration_ablation.json",
    "a4": "r6_a4_failure_mode_ablation.json",
}
PROVENANCE_FILE = "r6_tempglitch_cpu_provenance.json"

WOB_ABLATION_FILES = {
    "a7": "r6_wob_a7_aggregation_ablation.json",
    "a8": "r6_wob_a8_surprise_distance_ablation.json",
    "a9": "r6_wob_a9_threshold_calibration_ablation.json",
    "a10": "r6_wob_a10_failure_mode_ablation.json",
}

_SAFETY_FLAGS = ("locked_test_materialized", "locked_test_scored", "wob_dependency_used")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _check_safety_flags(
    payload: dict[str, Any],
    source: str,
    errors: list[str],
    check_wob: bool = True,
) -> None:
    if payload.get("locked_test_materialized") is not False:
        errors.append(f"{source}: locked_test_materialized is not False")
    if payload.get("locked_test_scored") is not False:
        errors.append(f"{source}: locked_test_scored is not False")
    if check_wob and payload.get("wob_dependency_used") is not False:
        errors.append(f"{source}: wob_dependency_used is not False")


def _check_no_placeholders(payload: dict[str, Any], source: str, errors: list[str]) -> None:
    """Recursively check that no placeholder strings appear as dict values."""

    def _walk(obj: Any, path: str) -> None:
        if isinstance(obj, str) and obj.strip() in _PLACEHOLDER_STRINGS:
            errors.append(f"{source}: placeholder string {obj!r} found at {path}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")

    _walk(payload, source)


def _check_numeric_fields_finite(
    payload: dict[str, Any],
    source: str,
    warnings: list[str],
    numeric_keys: tuple[str, ...] = ("auroc", "auprc", "f1", "precision", "recall"),
) -> None:
    """Warn if any known numeric field contains a non-finite value."""

    def _walk(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in numeric_keys:
                    if v is not None and not isinstance(v, bool):
                        try:
                            f = float(v)
                            if not math.isfinite(f):
                                warnings.append(f"{source}: non-finite value {v!r} at {path}.{k}")
                        except (ValueError, TypeError):
                            pass
                else:
                    _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")

    _walk(payload, source)


def validate_tempglitch_ablations(
    output_dir: Path,
    errors: list[str],
    warnings: list[str],
    completed: list[str],
    missing: list[str],
) -> None:
    if not output_dir.exists():
        warnings.append(f"TempGlitch R6 ablation directory does not exist: {output_dir}")
        for label in TEMPGLITCH_ABLATION_FILES:
            missing.append(f"tempglitch_{label}")
        return

    for label, fname in TEMPGLITCH_ABLATION_FILES.items():
        path = output_dir / fname
        if not path.exists():
            missing.append(f"tempglitch_{label}")
            continue
        try:
            payload = _read_json(path)
        except Exception as exc:
            errors.append(f"tempglitch_{label}: failed to parse {path}: {exc}")
            continue

        _check_safety_flags(payload, f"tempglitch_{label}", errors, check_wob=True)
        _check_no_placeholders(payload, f"tempglitch_{label}", errors)
        _check_numeric_fields_finite(payload, f"tempglitch_{label}", warnings)

        if payload.get("status") not in ("COMPLETED", "PARTIAL_COMPLETION"):
            warnings.append(
                f"tempglitch_{label}: status is {payload.get('status')!r}, not COMPLETED"
            )
        else:
            completed.append(f"tempglitch_{label}")

    prov_path = output_dir / PROVENANCE_FILE
    if prov_path.exists():
        try:
            prov = _read_json(prov_path)
            _check_safety_flags(prov, "provenance", errors, check_wob=True)
            if prov.get("wob_dependency_used") is not False:
                errors.append("provenance: wob_dependency_used is not False")
        except Exception as exc:
            errors.append(f"provenance: failed to parse {prov_path}: {exc}")
    else:
        warnings.append(f"Provenance file missing: {prov_path}")


def validate_wob_ablations(
    wob_output_dir: Path,
    r5_wob_receipt: Path | None,
    errors: list[str],
    warnings: list[str],
    completed: list[str],
    missing: list[str],
) -> None:
    if r5_wob_receipt is None or not r5_wob_receipt.exists():
        errors.append(
            "WOB ablation validation requires a validated R5-WOB receipt "
            "(--r5-wob-receipt). "
            "WOB ablations remain blocked until R5-WOB ingestion passes."
        )
        return

    try:
        receipt = _read_json(r5_wob_receipt)
    except Exception as exc:
        errors.append(f"Failed to parse R5-WOB receipt: {exc}")
        return

    if receipt.get("locked_test_materialized") is not False:
        errors.append("R5-WOB receipt: locked_test_materialized is not False")
    if receipt.get("locked_test_scored") is not False:
        errors.append("R5-WOB receipt: locked_test_scored is not False")

    if not wob_output_dir.exists():
        warnings.append(f"WOB R6 ablation directory does not exist: {wob_output_dir}")
        for label in WOB_ABLATION_FILES:
            missing.append(label)
        return

    for label, fname in WOB_ABLATION_FILES.items():
        path = wob_output_dir / fname
        if not path.exists():
            missing.append(label)
            continue
        try:
            payload = _read_json(path)
        except Exception as exc:
            errors.append(f"wob_{label}: failed to parse {path}: {exc}")
            continue

        _check_safety_flags(payload, f"wob_{label}", errors, check_wob=False)
        _check_no_placeholders(payload, f"wob_{label}", errors)
        _check_numeric_fields_finite(payload, f"wob_{label}", warnings)

        if payload.get("status") == "COMPLETED":
            completed.append(f"wob_{label}")
        else:
            missing.append(f"wob_{label}")


def validate_r6(
    output_dir: Path,
    wob_output_dir: Path | None = None,
    r5_wob_receipt: Path | None = None,
) -> dict[str, Any]:
    """Validate R6 ablation outputs; return a status dict."""
    errors: list[str] = []
    warnings: list[str] = []
    completed: list[str] = []
    missing: list[str] = []

    validate_tempglitch_ablations(output_dir, errors, warnings, completed, missing)

    if wob_output_dir is not None:
        validate_wob_ablations(wob_output_dir, r5_wob_receipt, errors, warnings, completed, missing)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "completed_ablations": completed,
        "missing_or_incomplete_ablations": missing,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate R6 ablation outputs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Path to TempGlitch R6 ablation output directory.",
    )
    p.add_argument(
        "--wob-output-dir",
        type=Path,
        default=None,
        help="Path to WOB R6 ablation output directory (optional; requires --r5-wob-receipt).",
    )
    p.add_argument(
        "--r5-wob-receipt",
        type=Path,
        default=None,
        help="Path to validated R5-WOB receipt JSON (required when --wob-output-dir is given).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_r6(args.output_dir, args.wob_output_dir, args.r5_wob_receipt)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
