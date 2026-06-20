"""Verify and ingest an R5-WOB success bundle or inspect a failure bundle.

This is an offline post-run gate. It verifies SHA256 sidecars, rejects unsafe
tar members, runs the frozen R5-WOB validator, and writes a validation receipt
only for a persistent, validator-passed extraction. It never runs evaluation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_READINESS = REPO_ROOT / "configs" / "wob_protocol" / "wob_expansion_readiness.json"
VALIDATOR_SCRIPT = REPO_ROOT / "scripts" / "validate_r5_wob_evaluation.py"
RECEIPT_NAME = "r5_wob_validation_receipt.json"
REQUIRED_OUTPUT_FILES = (
    "r5_wob_manifest.csv",
    "episode_scores.csv",
    "baseline_scores.csv",
    "r5_wob_metrics.json",
    "r5_wob_comparison.csv",
    "r5_wob_provenance.json",
    "R5_WOB_REPORT.md",
)

FAILURE_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "cuda_oom",
        ("cuda out of memory", "cublas_status_alloc_failed"),
        "Reduce only the failing scorer batch size, then rerun from that staged checkpoint.",
    ),
    (
        "environment_dependency",
        ("modulenotfounderror", "importerror", "no module named", "dependency conflict"),
        "Fix the lean Kaggle dependency setup and rerun preflight before any scoring stage.",
    ),
    (
        "artifact_integrity",
        ("sha256", "hash mismatch", "checksum", "unexpected seed"),
        "Re-download or remount the named artifact and rerun its validator before retrying.",
    ),
    (
        "missing_input",
        ("filenotfounderror", "missing input", "not found", "unresolved"),
        "Check the named Kaggle mount or staged file; do not alter the frozen manifest.",
    ),
    (
        "validator_failure",
        ("validationerror", "validator", "manifest hash mismatch", "locked rows present"),
        "Preserve the bundle and inspect the exact validator error before changing code.",
    ),
    (
        "data_materialization",
        ("lance", "tarfile", "decode", "corrupt"),
        "Inspect the materialization-stage inputs and retry only the failed stage after repair.",
    ),
    (
        "training_or_scoring_runtime",
        ("runtimeerror", "attributeerror", "typeerror", "valueerror"),
        "Use the captured traceback to patch the smallest failing code path, test it, then retry.",
    ),
    (
        "timeout",
        ("time limit", "timed out", "timeout"),
        "Resume from completed stage markers and split only the unfinished stage if necessary.",
    ),
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_expected_hash(sha256_file: Path) -> str:
    tokens = sha256_file.read_text(encoding="utf-8-sig").strip().split()
    if not tokens or re.fullmatch(r"[0-9a-fA-F]{64}", tokens[0]) is None:
        raise ValueError(f"Invalid SHA256 sidecar: {sha256_file}")
    return tokens[0].lower()


def _verify_sidecar(path: Path, sha256_file: Path) -> dict[str, Any]:
    expected = _read_expected_hash(sha256_file)
    actual = _sha256_file(path)
    return {
        "expected_sha256": expected,
        "actual_sha256": actual,
        "sha256_verified": expected == actual,
    }


def _safe_extract(tarball: Path, dest: Path) -> Path:
    """Extract regular files/directories while rejecting traversal and links."""
    destination = dest.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise RuntimeError(f"Extraction directory must be empty: {destination}")

    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            resolved = (destination / member.name).resolve()
            if not resolved.is_relative_to(destination):
                raise RuntimeError(f"Path traversal detected: {member.name}")
            if member.issym() or member.islnk():
                raise RuntimeError(f"Archive links are not allowed: {member.name}")
            if not (member.isdir() or member.isreg()):
                raise RuntimeError(f"Unsupported archive member type: {member.name}")
        archive.extractall(destination)
    return destination


def _locate_output_dir(extract_dir: Path) -> Path:
    direct_match = extract_dir / "r5_wob_identical_episode"
    if direct_match.is_dir():
        return direct_match
    candidates = list(extract_dir.iterdir())
    if len(candidates) == 1 and candidates[0].is_dir():
        return candidates[0]
    return extract_dir


def _run_validator(output_dir: Path, readiness_json: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(VALIDATOR_SCRIPT),
        "--output-dir",
        str(output_dir),
        "--readiness-json",
        str(readiness_json),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return {
            "valid": False,
            "returncode": result.returncode,
            "stdout_tail": result.stdout.strip()[-1000:],
            "stderr_tail": result.stderr.strip()[-2000:],
        }
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "valid": False,
            "returncode": result.returncode,
            "parse_error": True,
            "stdout_tail": result.stdout.strip()[-1000:],
        }
    payload["valid"] = payload.get("status") == "r5_wob_validated"
    return payload


def _output_hashes(output_dir: Path) -> dict[str, str]:
    return {
        name: _sha256_file(output_dir / name)
        for name in REQUIRED_OUTPUT_FILES
        if (output_dir / name).is_file()
    }


def _metric_inventory(output_dir: Path) -> dict[str, Any]:
    comparison_path = output_dir / "r5_wob_comparison.csv"
    if not comparison_path.is_file():
        return {}
    with comparison_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "comparison_rows": len(rows),
        "lewm_seeds": sorted(
            {row.get("seed", "") for row in rows if row.get("method_family") == "lewm"}
        ),
        "baselines": sorted(
            {row.get("method", "") for row in rows if row.get("method_family") == "baseline"}
        ),
    }


def _write_receipt(
    receipt_path: Path,
    *,
    bundle_sha256: str,
    readiness_json: Path,
    output_dir: Path,
    validator: dict[str, Any],
) -> None:
    receipt = {
        "schema_version": 1,
        "status": "r5_wob_validated",
        "bundle_sha256": bundle_sha256,
        "readiness_json_sha256": _sha256_file(readiness_json),
        "output_dir": str(output_dir.resolve()),
        "output_hashes": _output_hashes(output_dir),
        "metric_inventory": _metric_inventory(output_dir),
        "validator": validator,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def _verify_extracted(
    *,
    tarball: Path,
    sha256_file: Path,
    readiness_json: Path,
    extract_dir: Path,
    receipt_file: Path | None,
    write_default_receipt: bool = False,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "tarball": str(tarball),
        "sha256_file": str(sha256_file),
        "overall": "UNKNOWN",
    }
    sidecar = _verify_sidecar(tarball, sha256_file)
    status.update(sidecar)
    if not sidecar["sha256_verified"]:
        status["overall"] = "HASH_MISMATCH"
        return status

    _safe_extract(tarball, extract_dir)
    output_dir = _locate_output_dir(extract_dir)
    status["extract_dir"] = str(extract_dir)
    status["output_dir"] = str(output_dir)

    missing = [name for name in REQUIRED_OUTPUT_FILES if not (output_dir / name).is_file()]
    if missing:
        status["overall"] = "INCOMPLETE_KAGGLE_OUTPUT"
        status["missing_expected_files"] = missing
        return status

    validator = _run_validator(output_dir, readiness_json)
    status["validator"] = validator
    if validator.get("valid") is not True:
        status["overall"] = "VALIDATOR_FAILURE"
        validator_text = json.dumps(validator).lower()
        if "locked" in validator_text:
            status["contamination_warning"] = "POSSIBLE_LOCKED_TEST_CONTAMINATION"
        return status

    status["overall"] = "VALID_OUTPUT_BUNDLE"
    status["metric_inventory"] = _metric_inventory(output_dir)
    if write_default_receipt and receipt_file is None:
        receipt_file = output_dir / RECEIPT_NAME
    if receipt_file is not None:
        _write_receipt(
            receipt_file,
            bundle_sha256=sidecar["actual_sha256"],
            readiness_json=readiness_json,
            output_dir=output_dir,
            validator=validator,
        )
        status["validation_receipt"] = str(receipt_file)
    return status


def verify(
    tarball: Path,
    sha256_file: Path,
    readiness_json: Path,
    failure_debug_tarball: Path | None = None,
    *,
    extract_dir: Path | None = None,
    receipt_file: Path | None = None,
) -> dict[str, Any]:
    """Verify a success bundle and optionally persist its validated extraction."""
    if not tarball.is_file():
        if failure_debug_tarball is not None and failure_debug_tarball.is_file():
            return {
                "overall": "FAILURE_DEBUG_BUNDLE",
                "failure_debug_bundle": str(failure_debug_tarball),
                "failure_debug_exists": True,
                "detail": "Success bundle absent; inspect the failure bundle separately.",
            }
        return {"overall": "MISSING_TARBALL", "detail": f"Tarball not found: {tarball}"}
    if not sha256_file.is_file():
        return {"overall": "MISSING_SHA256", "detail": f"SHA256 sidecar not found: {sha256_file}"}
    if not readiness_json.is_file():
        return {"overall": "MISSING_READINESS", "detail": str(readiness_json)}

    try:
        if extract_dir is not None:
            return _verify_extracted(
                tarball=tarball,
                sha256_file=sha256_file,
                readiness_json=readiness_json,
                extract_dir=extract_dir,
                receipt_file=receipt_file,
                write_default_receipt=True,
            )
        with tempfile.TemporaryDirectory(prefix="r5_wob_verify_") as temp_dir:
            return _verify_extracted(
                tarball=tarball,
                sha256_file=sha256_file,
                readiness_json=readiness_json,
                extract_dir=Path(temp_dir),
                receipt_file=None,
            )
    except (OSError, tarfile.TarError, ValueError, RuntimeError) as exc:
        return {"overall": "EXTRACTION_OR_INTAKE_FAILED", "detail": str(exc)}


def _find_member_text(root: Path, filename: str) -> str:
    matches = list(root.rglob(filename))
    if not matches:
        return ""
    return matches[0].read_text(encoding="utf-8-sig", errors="replace")


def _classify_failure(text: str) -> tuple[str, str]:
    lowered = text.lower()
    for failure_class, patterns, minimal_fix in FAILURE_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return failure_class, minimal_fix
    return (
        "unknown_needs_more_logs",
        "Upload the full debug bundle and Kaggle console tail; do not retry unchanged.",
    )


def inspect_failure_debug(
    tarball: Path,
    sha256_file: Path | None = None,
) -> dict[str, Any]:
    """Safely inspect a staged failure bundle without running any experiment."""
    status: dict[str, Any] = {"failure_debug_tarball": str(tarball), "overall": "UNKNOWN"}
    if not tarball.is_file():
        return {**status, "overall": "MISSING_FAILURE_DEBUG"}
    if sha256_file is not None:
        if not sha256_file.is_file():
            return {**status, "overall": "MISSING_FAILURE_SHA256"}
        try:
            sidecar = _verify_sidecar(tarball, sha256_file)
        except ValueError as exc:
            return {**status, "overall": "INVALID_FAILURE_SHA256", "detail": str(exc)}
        status.update(sidecar)
        if not sidecar["sha256_verified"]:
            status["overall"] = "FAILURE_HASH_MISMATCH"
            return status

    try:
        with tempfile.TemporaryDirectory(prefix="r5_wob_failure_") as temp_dir:
            root = _safe_extract(tarball, Path(temp_dir))
            summary_text = _find_member_text(root, "failure_summary.json")
            log_text = _find_member_text(root, "r5_wob_staged.log")
            summary = json.loads(summary_text) if summary_text else {}
            diagnostic_text = log_text[-20000:] if log_text else summary_text
            failure_class, minimal_fix = _classify_failure(diagnostic_text)
            status.update(
                {
                    "overall": "FAILURE_CLASSIFIED",
                    "failed_stage": summary.get("phase", "unknown"),
                    "failure_class": failure_class,
                    "minimal_fix": minimal_fix,
                    "git_sha": summary.get("git_sha", "unknown"),
                    "exit_code": summary.get("exit_code"),
                    "locked_test_materialized": summary.get("locked_test_materialized", False),
                    "locked_test_scored": summary.get("locked_test_scored", False),
                    "has_failure_summary": bool(summary_text),
                    "has_staged_log": bool(log_text),
                }
            )
            if status["locked_test_materialized"] or status["locked_test_scored"]:
                status["overall"] = "LOCKED_TEST_CONTAMINATION"
                status["minimal_fix"] = "Quarantine the bundle and stop; do not reuse its outputs."
    except (OSError, tarfile.TarError, json.JSONDecodeError, RuntimeError) as exc:
        status.update({"overall": "FAILURE_DEBUG_INVALID", "detail": str(exc)})
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline R5-WOB post-run intake gate.")
    parser.add_argument("--tarball", type=Path, help="R5-WOB success tarball")
    parser.add_argument("--sha256-file", type=Path, help="Success tarball SHA256 sidecar")
    parser.add_argument(
        "--extract-dir",
        type=Path,
        help="Empty destination for persistent validated extraction and receipt",
    )
    parser.add_argument("--receipt-file", type=Path, help="Optional explicit receipt path")
    parser.add_argument("--failure-debug-tarball", type=Path, help="Failure-debug tarball")
    parser.add_argument("--failure-debug-sha256-file", type=Path, help="Failure SHA256 sidecar")
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.tarball is not None or args.sha256_file is not None:
        if args.tarball is None or args.sha256_file is None:
            print("ERROR: --tarball and --sha256-file must be provided together.", file=sys.stderr)
            return 2
        result = verify(
            args.tarball,
            args.sha256_file,
            args.readiness_json,
            extract_dir=args.extract_dir,
            receipt_file=args.receipt_file,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["overall"] == "VALID_OUTPUT_BUNDLE" else 1

    if args.failure_debug_tarball is not None:
        result = inspect_failure_debug(
            args.failure_debug_tarball,
            args.failure_debug_sha256_file,
        )
        print(json.dumps(result, indent=2))
        return 1

    print("ERROR: provide a success bundle pair or --failure-debug-tarball.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
