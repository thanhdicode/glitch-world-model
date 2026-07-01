from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "r5_wob_identical_episode"
DEFAULT_READINESS_JSON = ROOT / "configs" / "wob_protocol" / "wob_expansion_readiness.json"
EXPECTED_SEEDS = {"42", "43", "44"}
EXPECTED_BASELINES = {"frame_diff", "feature_distance"}
EXPECTED_CALIBRATION_NORMAL = 6
EXPECTED_EVALUATION_NORMAL = 6
EXPECTED_EVALUATION_BUGGY = 60
EXPECTED_EVALUATION_EPISODES = EXPECTED_EVALUATION_NORMAL + EXPECTED_EVALUATION_BUGGY


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _finite_or_blank(value: str) -> bool:
    if value == "":
        return True
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def validate_r5_wob(output_dir: Path, readiness_json: Path) -> dict[str, Any]:
    errors: list[str] = []
    readiness = _read_json(readiness_json)
    required_files = {
        "manifest": output_dir / "r5_wob_manifest.csv",
        "episode_scores": output_dir / "episode_scores.csv",
        "baseline_scores": output_dir / "baseline_scores.csv",
        "metrics": output_dir / "r5_wob_metrics.json",
        "comparison": output_dir / "r5_wob_comparison.csv",
        "provenance": output_dir / "r5_wob_provenance.json",
        "report": output_dir / "R5_WOB_REPORT.md",
    }
    for label, path in required_files.items():
        _assert(path.is_file(), f"missing required output: {label} -> {path}", errors)
    if errors:
        raise ValueError("; ".join(errors))

    manifest_rows = _read_csv(required_files["manifest"])
    _assert(
        len(manifest_rows) == readiness["eval_manifest_row_count"],
        "frozen eval manifest row count mismatch",
        errors,
    )
    manifest_hash = hashlib_sha256(required_files["manifest"])
    _assert(
        manifest_hash == readiness["eval_manifest_sha256"],
        "frozen eval manifest hash mismatch against readiness freeze",
        errors,
    )
    calibration = [row for row in manifest_rows if row["evaluation_role"] == "calibration_normal"]
    evaluation_normal = [
        row for row in manifest_rows if row["evaluation_role"] == "evaluation_normal"
    ]
    evaluation_buggy = [
        row for row in manifest_rows if row["evaluation_role"] == "evaluation_buggy"
    ]
    _assert(
        len(calibration) == EXPECTED_CALIBRATION_NORMAL,
        f"expected {EXPECTED_CALIBRATION_NORMAL} calibration-normal rows",
        errors,
    )
    _assert(
        len(evaluation_normal) == EXPECTED_EVALUATION_NORMAL,
        f"expected {EXPECTED_EVALUATION_NORMAL} evaluation-normal rows",
        errors,
    )
    _assert(
        len(evaluation_buggy) == EXPECTED_EVALUATION_BUGGY,
        f"expected {EXPECTED_EVALUATION_BUGGY} evaluation-buggy rows",
        errors,
    )
    _assert(
        not [row for row in manifest_rows if row["split"] == "train"], "train rows present", errors
    )
    _assert(
        not [row for row in manifest_rows if row["split"] == "test"], "locked rows present", errors
    )
    _assert(
        all(row["label"] == "Normal" for row in calibration),
        "calibration rows not all normal",
        errors,
    )
    _assert(
        all(row["label"] == "Normal" for row in evaluation_normal),
        "evaluation-normal rows not all normal",
        errors,
    )
    _assert(
        all(row["label"] == "Buggy" for row in evaluation_buggy),
        "evaluation-buggy rows not all buggy",
        errors,
    )

    metrics = _read_json(required_files["metrics"])
    comparison_rows = _read_csv(required_files["comparison"])
    provenance = _read_json(required_files["provenance"])

    _assert(metrics.get("status") == "r5_wob_complete", "metrics status mismatch", errors)
    _assert(
        metrics.get("validation_buggy_used_for_fit_select") is False,
        "validation-buggy leakage flag true",
        errors,
    )
    _assert(
        metrics.get("locked_test_materialized") is False, "locked_test_materialized true", errors
    )
    _assert(metrics.get("locked_test_scored") is False, "locked_test_scored true", errors)
    _assert(
        metrics.get("evaluation_run") is True,
        "evaluation_run must be true after successful run",
        errors,
    )
    bootstrap = metrics.get("bootstrap", {})
    _assert(bool(bootstrap.get("n_bootstrap")), "bootstrap configuration missing", errors)
    _assert(bool(bootstrap.get("group_key")), "bootstrap group_key missing", errors)

    seeds_present = {row["seed"] for row in comparison_rows if row["method_family"] == "lewm"}
    _assert(
        seeds_present == EXPECTED_SEEDS,
        f"missing lewm seeds in comparison: {seeds_present}",
        errors,
    )
    baselines_present = {
        row["method"] for row in comparison_rows if row["method_family"] == "baseline"
    }
    _assert(
        baselines_present == EXPECTED_BASELINES,
        f"missing baselines in comparison: {baselines_present}",
        errors,
    )

    for row in comparison_rows:
        _assert(
            int(row["evaluation_episode_count"]) == EXPECTED_EVALUATION_EPISODES,
            f"comparison evaluation_episode_count must be {EXPECTED_EVALUATION_EPISODES}: {row}",
            errors,
        )
        _assert(
            int(row["positive_episode_count"]) == EXPECTED_EVALUATION_BUGGY,
            f"comparison positive_episode_count must be {EXPECTED_EVALUATION_BUGGY}: {row}",
            errors,
        )
        _assert(
            int(row["negative_episode_count"]) == EXPECTED_EVALUATION_NORMAL,
            f"comparison negative_episode_count must be {EXPECTED_EVALUATION_NORMAL}: {row}",
            errors,
        )
        for field in (
            "auroc",
            "auprc",
            "f1",
            "fpr_at_95_tpr",
            "auroc_ci_lower",
            "auroc_ci_upper",
            "f1_ci_lower",
            "f1_ci_upper",
        ):
            _assert(
                _finite_or_blank(row[field]),
                f"comparison field {field} is not finite or blank: {row}",
                errors,
            )
        for field in ("auroc", "fpr_at_95_tpr"):
            _assert(row[field] != "", f"comparison field {field} must not be blank", errors)

    outputs = provenance.get("outputs", {})
    for key in (
        "r5_wob_manifest.csv",
        "episode_scores.csv",
        "baseline_scores.csv",
        "r5_wob_metrics.json",
        "r5_wob_comparison.csv",
        "r5_wob_provenance.json",
        "R5_WOB_REPORT.md",
    ):
        _assert(bool(outputs.get(key)), f"provenance hash missing for {key}", errors)
    _assert(
        provenance.get("locked_test_materialized") is False,
        "provenance locked_test_materialized true",
        errors,
    )
    _assert(
        provenance.get("locked_test_scored") is False,
        "provenance locked_test_scored true",
        errors,
    )

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "r5_wob_validated",
        "output_dir": str(output_dir),
        "frozen_eval_manifest_sha256": manifest_hash,
        "comparison_rows": len(comparison_rows),
        "lewm_seeds_present": sorted(seeds_present),
        "baselines_present": sorted(baselines_present),
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def hashlib_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the R5-WOB non-locked identical-episode evaluation bundle."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS_JSON)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(validate_r5_wob(args.output_dir, args.readiness_json), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
