"""Validate the frozen seed42 non-locked World of Bugs evaluation-readiness bundle.

This refuses unless every readiness invariant holds:

* WOB-P0 Kaggle audit hash recorded and equal to the expected value.
* WOB-P1 seed42 artifact hash recorded and equal to the expected value.
* The frozen evaluation manifest exists and its SHA256 matches the readiness record
  (frozen-before-scoring).
* The evaluation manifest contains zero locked rows (``split == "test"``); counts are exactly
  12 calibration-normal + 60 evaluation-buggy = 72.
* ``validation_buggy_used_for_fit_select`` is false and the calibration set is normal-only.
* The seed42 selected-checkpoint metadata block is present and consistent.
* Reporting/output paths are frozen and non-empty.
* The claim boundary and forbidden-claims list are frozen and non-empty.
* ``locked_test_materialized`` / ``locked_test_scored`` / ``evaluation_run`` are all false.

Locked status is decided only by ``split == "test"``; the upstream ``source`` directory naming
(``TEST/...``) on buggy validation rows is never treated as locked.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_READINESS_JSON = Path("configs/wob_protocol/wob_expansion_readiness.json")

EXPECTED_WOB_P0_KAGGLE_AUDIT_SHA256 = (
    "e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9"
)
EXPECTED_WOB_P1_SEED42_ARTIFACT_SHA256 = (
    "54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03"
)

EXPECTED_CALIBRATION_NORMAL = 12
EXPECTED_EVALUATION_BUGGY = 60
EXPECTED_VALIDATION_TOTAL = EXPECTED_CALIBRATION_NORMAL + EXPECTED_EVALUATION_BUGGY
EXPECTED_LOCKED_EXCLUDED = 59
EXPECTED_TRAIN_EXCLUDED = 48

CALIBRATION_ROLE = "calibration_normal"
EVALUATION_ROLE = "evaluation_buggy"

LOCKED_SPLIT_TOKEN = "test"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_manifest_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_readiness(readiness_json: Path, *, repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    _assert(readiness_json.is_file(), f"readiness record missing: {readiness_json}", errors)
    if errors:
        raise ValueError("; ".join(errors))

    readiness = _read_json(readiness_json)

    _assert(readiness.get("phase") == "wob_expansion_readiness", "phase mismatch", errors)
    _assert(readiness.get("seed") == 42, "seed must be 42", errors)

    hashes = readiness.get("recorded_artifact_hashes", {})
    _assert(
        hashes.get("wob_p0_kaggle_audit_sha256") == EXPECTED_WOB_P0_KAGGLE_AUDIT_SHA256,
        "WOB-P0 Kaggle audit hash missing or mismatched",
        errors,
    )
    _assert(
        hashes.get("wob_p1_seed42_artifact_sha256") == EXPECTED_WOB_P1_SEED42_ARTIFACT_SHA256,
        "WOB-P1 seed42 artifact hash missing or mismatched",
        errors,
    )

    # Frozen-before-scoring: the manifest file must exist and match the recorded hash.
    manifest_rel = readiness.get("eval_manifest_path", "")
    _assert(bool(manifest_rel), "eval_manifest_path is empty", errors)
    manifest_rows: list[dict[str, str]] = []
    if manifest_rel:
        manifest_path = (repo_root / manifest_rel).resolve()
        _assert(manifest_path.is_file(), f"eval manifest missing: {manifest_rel}", errors)
        if manifest_path.is_file():
            manifest_bytes = manifest_path.read_bytes()
            actual_hash = _sha256_bytes(manifest_bytes)
            _assert(
                actual_hash == readiness.get("eval_manifest_sha256"),
                "eval manifest SHA256 does not match the readiness record",
                errors,
            )
            manifest_rows = _read_manifest_rows(manifest_path)

    if manifest_rows:
        locked = [r for r in manifest_rows if (r.get("split") or "").lower() == LOCKED_SPLIT_TOKEN]
        _assert(not locked, f"eval manifest contains locked rows: {len(locked)}", errors)
        non_validation = [r for r in manifest_rows if r.get("split") != "validation"]
        _assert(not non_validation, "eval manifest contains non-validation rows", errors)

        calibration = [r for r in manifest_rows if r.get("evaluation_role") == CALIBRATION_ROLE]
        evaluation = [r for r in manifest_rows if r.get("evaluation_role") == EVALUATION_ROLE]
        _assert(
            len(calibration) == EXPECTED_CALIBRATION_NORMAL,
            f"calibration row count mismatch: {len(calibration)}",
            errors,
        )
        _assert(
            len(evaluation) == EXPECTED_EVALUATION_BUGGY,
            f"evaluation row count mismatch: {len(evaluation)}",
            errors,
        )
        _assert(
            len(manifest_rows) == EXPECTED_VALIDATION_TOTAL,
            f"eval manifest row count mismatch: {len(manifest_rows)}",
            errors,
        )
        _assert(
            all(r.get("label") == "Normal" for r in calibration),
            "calibration set contains non-normal rows (buggy must never be in fit/select)",
            errors,
        )
        _assert(
            all(r.get("label") == "Buggy" for r in evaluation),
            "evaluation set contains non-buggy rows",
            errors,
        )

    _assert(
        readiness.get("eval_manifest_row_count") == EXPECTED_VALIDATION_TOTAL,
        "readiness eval_manifest_row_count mismatch",
        errors,
    )
    calibration_block = readiness.get("calibration", {})
    evaluation_block = readiness.get("evaluation", {})
    _assert(
        calibration_block.get("count") == EXPECTED_CALIBRATION_NORMAL,
        "readiness calibration count mismatch",
        errors,
    )
    _assert(
        evaluation_block.get("count") == EXPECTED_EVALUATION_BUGGY,
        "readiness evaluation count mismatch",
        errors,
    )
    _assert(
        readiness.get("locked_rows_excluded") == EXPECTED_LOCKED_EXCLUDED,
        "locked rows excluded count mismatch",
        errors,
    )
    _assert(
        readiness.get("train_rows_excluded") == EXPECTED_TRAIN_EXCLUDED,
        "train rows excluded count mismatch",
        errors,
    )

    checkpoint = readiness.get("seed42_selected_checkpoint", {})
    _assert(checkpoint.get("seed") == 42, "checkpoint seed mismatch", errors)
    _assert(
        checkpoint.get("selection_split") == "validation_normal",
        "checkpoint selection_split must be validation_normal",
        errors,
    )
    _assert(checkpoint.get("action_dim") == 4, "checkpoint action_dim must be 4", errors)

    reporting = readiness.get("reporting", {})
    for key in ("results_doc", "output_dir", "manifest_output", "metrics_output"):
        _assert(bool(reporting.get(key)), f"reporting path not frozen: {key}", errors)

    _assert(bool(readiness.get("claim_boundary")), "claim boundary not frozen", errors)
    forbidden = readiness.get("forbidden_claims", [])
    _assert(
        isinstance(forbidden, list) and len(forbidden) > 0,
        "forbidden_claims list not frozen",
        errors,
    )

    _assert(
        readiness.get("validation_buggy_used_for_fit_select") is False,
        "validation-buggy used for fit/select",
        errors,
    )
    _assert(readiness.get("locked_test_materialized") is False, "locked test materialized", errors)
    _assert(readiness.get("locked_test_scored") is False, "locked test scored", errors)
    _assert(readiness.get("evaluation_run") is False, "evaluation already marked run", errors)

    if errors:
        raise ValueError("; ".join(errors))

    return {
        "status": "wob_expansion_readiness_passed",
        "readiness_json": str(readiness_json),
        "eval_manifest_path": manifest_rel,
        "eval_manifest_sha256": readiness.get("eval_manifest_sha256"),
        "calibration_normal_count": EXPECTED_CALIBRATION_NORMAL,
        "evaluation_buggy_count": EXPECTED_EVALUATION_BUGGY,
        "locked_rows_excluded": EXPECTED_LOCKED_EXCLUDED,
        "train_rows_excluded": EXPECTED_TRAIN_EXCLUDED,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the frozen seed42 non-locked WOB evaluation-readiness bundle."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--readiness-json", type=Path, default=ROOT / DEFAULT_READINESS_JSON)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_readiness(args.readiness_json, repo_root=args.repo_root.resolve())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
