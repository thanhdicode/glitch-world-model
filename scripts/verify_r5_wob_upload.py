"""Verify an uploaded R5-WOB output tarball and run the R5-WOB validator.

Usage
-----
    python scripts/verify_r5_wob_upload.py \
        --tarball path/to/r5_wob_identical_episode_outputs.tar.gz \
        --sha256-file path/to/r5_wob_identical_episode_outputs.tar.gz.sha256 \
        [--failure-debug-tarball path/to/r5_wob_identical_episode_failure_debug.tar.gz] \
        [--readiness-json configs/wob_protocol/wob_expansion_readiness.json]

The script:
1. Verifies the SHA256 sidecar against the tarball.
2. Extracts the tarball safely to a temporary directory.
3. Runs ``scripts/validate_r5_wob_evaluation.py`` on the extracted output.
4. Prints a concise JSON status.
5. Never writes fake metrics or touches locked test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_READINESS = REPO_ROOT / "configs" / "wob_protocol" / "wob_expansion_readiness.json"
VALIDATOR_SCRIPT = REPO_ROOT / "scripts" / "validate_r5_wob_evaluation.py"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_expected_hash(sha256_file: Path) -> str:
    text = sha256_file.read_text().strip()
    # Support both bare hash and ``hash  filename`` format
    return text.split()[0].lower()


def _safe_extract(tarball: Path, dest: Path) -> Path:
    """Extract tarball safely, rejecting path traversal."""
    destination = dest.resolve()
    with tarfile.open(tarball, "r:gz") as tf:
        for member in tf.getmembers():
            resolved = (dest / member.name).resolve()
            if not resolved.is_relative_to(destination):
                raise RuntimeError(f"Path traversal detected in tarball member: {member.name}")
        tf.extractall(dest, filter="data")
    return dest


def _run_validator(output_dir: Path, readiness_json: Path) -> dict:
    """Run the R5-WOB validator and return its parsed JSON output."""
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
            "validator_passed": False,
            "validator_returncode": result.returncode,
            "validator_stderr": result.stderr.strip()[-500:] if result.stderr else "",
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "validator_passed": False,
            "validator_parse_error": True,
            "validator_stdout_tail": result.stdout.strip()[-500:] if result.stdout else "",
        }


def verify(
    tarball: Path,
    sha256_file: Path,
    readiness_json: Path,
    failure_debug_tarball: Path | None = None,
) -> dict:
    """Run the full intake verification and return a status dict."""
    status: dict = {
        "tarball": str(tarball),
        "sha256_file": str(sha256_file),
        "overall": "UNKNOWN",
    }

    if failure_debug_tarball is not None:
        status["failure_debug_bundle"] = str(failure_debug_tarball)
        status["failure_debug_exists"] = failure_debug_tarball.exists()

    # ── Step 1: file existence ──────────────────────────────────────────
    if not tarball.exists():
        if status.get("failure_debug_exists"):
            status["overall"] = "FAILURE_DEBUG_BUNDLE"
            status["detail"] = (
                "Main output tarball is absent; inspect the available failure-debug bundle."
            )
        else:
            status["overall"] = "MISSING_TARBALL"
            status["detail"] = f"Tarball not found: {tarball}"
        return status

    if not sha256_file.exists():
        status["overall"] = "MISSING_SHA256"
        status["detail"] = f"SHA256 sidecar not found: {sha256_file}"
        return status

    # ── Step 2: SHA256 verification ─────────────────────────────────────
    expected = _read_expected_hash(sha256_file)
    actual = _sha256_file(tarball)
    status["expected_sha256"] = expected
    status["actual_sha256"] = actual

    if actual != expected:
        status["overall"] = "HASH_MISMATCH"
        status["detail"] = "SHA256 hash does not match sidecar"
        return status

    status["sha256_verified"] = True

    # ── Step 3: safe extraction ─────────────────────────────────────────
    tmpdir = tempfile.mkdtemp(prefix="r5_wob_verify_")
    extract_dir = Path(tmpdir)
    try:
        _safe_extract(tarball, extract_dir)
    except Exception as exc:
        status["overall"] = "EXTRACTION_FAILED"
        status["detail"] = str(exc)[:300]
        return status

    status["extract_dir"] = str(extract_dir)

    # ── Step 4: locate output directory ─────────────────────────────────
    # The tarball may contain a top-level directory or files directly.
    candidates = list(extract_dir.iterdir())
    if len(candidates) == 1 and candidates[0].is_dir():
        output_dir = candidates[0]
    else:
        output_dir = extract_dir

    status["output_dir"] = str(output_dir)

    # ── Step 5: run validator ───────────────────────────────────────────
    validator_result = _run_validator(output_dir, readiness_json)
    status["validator"] = validator_result

    passed = validator_result.get("valid", validator_result.get("validator_passed"))
    if passed is True:
        status["overall"] = "VALID_OUTPUT_BUNDLE"
    else:
        status["overall"] = "VALIDATOR_FAILURE"
        # Check for specific failure patterns
        errors = validator_result.get("errors", [])
        if any("locked" in str(e).lower() for e in errors):
            status["contamination_warning"] = "POSSIBLE_LOCKED_TEST_CONTAMINATION"

    # ── Step 6: check for failure-debug bundle ──────────────────────────
    # ── Step 7: completeness heuristics ─────────────────────────────────
    expected_files = [
        "r5_wob_metrics.json",
        "r5_wob_comparison.csv",
        "r5_wob_provenance.json",
    ]
    missing = [f for f in expected_files if not (output_dir / f).exists()]
    if missing:
        status["missing_expected_files"] = missing
        if status["overall"] == "VALID_OUTPUT_BUNDLE":
            status["overall"] = "INCOMPLETE_KAGGLE_OUTPUT"

    return status


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Verify an uploaded R5-WOB output tarball.")
    p.add_argument(
        "--tarball",
        type=Path,
        required=True,
        help="Path to r5_wob_identical_episode_outputs.tar.gz",
    )
    p.add_argument(
        "--sha256-file",
        type=Path,
        required=True,
        help="Path to the .sha256 sidecar file",
    )
    p.add_argument(
        "--failure-debug-tarball",
        type=Path,
        default=None,
        help="Optional path to r5_wob_identical_episode_failure_debug.tar.gz",
    )
    p.add_argument(
        "--readiness-json",
        type=Path,
        default=DEFAULT_READINESS,
        help="Path to wob_expansion_readiness.json",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = verify(
        tarball=args.tarball,
        sha256_file=args.sha256_file,
        readiness_json=args.readiness_json,
        failure_debug_tarball=args.failure_debug_tarball,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["overall"] == "VALID_OUTPUT_BUNDLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
