"""R6 CPU-safe TempGlitch ablation runner — A1 through A4.

Reads validated R5 TempGlitch score artifacts and produces four ablation
outputs that require only CPU. All four ablations operate entirely on files
already produced by the R5 identical-episode evaluation pipeline.

Ablations
---------
A1 — Aggregation comparison
    Groups R5 comparison rows by episode_aggregation (max / mean) and
    window_aggregation and summarises AUROC, AUPRC, F1 per variant.

A2 — Surprise-distance comparison
    Groups by window_aggregation family: MSE-based (mse_max, mse_mean)
    vs L2-based (l2_max, l2_mean). Cosine distance is NOT available from
    current R5 artifacts and is recorded as NOT_AVAILABLE_FROM_CURRENT_ARTIFACTS.

A3 — Threshold calibration summary
    Reports calibration_normal_P95 thresholds and corresponding F1, precision,
    recall, FPR@95TPR for every configuration in the comparison CSV. A full
    per-threshold sweep requires per-episode raw scores not saved in the R5
    artifact family; that limitation is recorded explicitly.

A4 — Failure-mode analysis
    Uses the R5 episode manifest to show per-category episode counts and
    label distribution. Flags categories that have only normal or only buggy
    coverage, and notes where category metadata is missing.

Strict boundaries
-----------------
- No locked-test path is read or written.
- No WOB output is required or used.
- paper_valid=True only when all required R5 inputs exist and pass checks.
- Outputs go only under the nominated --output-dir.
- No fabricated metric values are written.
- Placeholder strings are never labelled as metrics.

Usage
-----
    python scripts/run_r6_tempglitch_cpu_ablations.py \\
        --r5-output-dir outputs/r5_tempglitch_identical_episode \\
        --output-dir outputs/r6_tempglitch_ablations \\
        --ablation all

    python scripts/run_r6_tempglitch_cpu_ablations.py \\
        --r5-output-dir outputs/r5_tempglitch_identical_episode \\
        --output-dir outputs/r6_tempglitch_ablations \\
        --ablation a1
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_R5_DIR = REPO_ROOT / "outputs" / "r5_tempglitch_identical_episode"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "r6_tempglitch_ablations"

_LOCKED_RE = re.compile(r"(?:^|[_\-])locked(?:[_\-]|$)", re.IGNORECASE)

_R5_COMPARISON_CSV = "r5_comparison.csv"
_R5_EPISODE_MANIFEST_CSV = "r5_episode_manifest.csv"
_R5_EVAL_JSON = "r5_episode_eval.json"

REQUIRED_R5_FILES = [_R5_COMPARISON_CSV, _R5_EPISODE_MANIFEST_CSV]
OPTIONAL_R5_FILES = [_R5_EVAL_JSON]

MSE_WINDOW_AGGREGATIONS = ("mse_max", "mse_mean")
L2_WINDOW_AGGREGATIONS = ("l2_max", "l2_mean")
BASELINE_SCORERS = ("baseline_frame_diff", "baseline_feature_distance")
EPISODE_AGGREGATIONS = ("max", "mean")

ABLATION_IDS = ("a1", "a2", "a3", "a4")


def _locked_guard(path: Path) -> None:
    if _LOCKED_RE.search(path.name):
        raise ValueError(f"R6 CPU ablation refuses locked-test path: {path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    _locked_guard(path)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_json(path: Path) -> dict[str, Any]:
    _locked_guard(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def _safe_mean(values: list[float]) -> float | None:
    finite = [v for v in values if math.isfinite(v)]
    return sum(finite) / len(finite) if finite else None


def _safe_max(values: list[float]) -> float | None:
    finite = [v for v in values if math.isfinite(v)]
    return max(finite) if finite else None


def check_r5_inputs(r5_dir: Path) -> dict[str, Any]:
    """Verify required and optional R5 inputs; return a status dict."""
    _locked_guard(r5_dir)

    missing_required: list[str] = []
    present: dict[str, str] = {}
    optional_present: dict[str, str] = {}

    for name in REQUIRED_R5_FILES:
        p = r5_dir / name
        if p.exists():
            present[name] = _sha256(p)
        else:
            missing_required.append(str(p))

    for name in OPTIONAL_R5_FILES:
        p = r5_dir / name
        if p.exists():
            optional_present[name] = _sha256(p)

    return {
        "r5_dir": str(r5_dir),
        "required_files_present": len(missing_required) == 0,
        "missing_required": missing_required,
        "present": present,
        "optional_present": optional_present,
    }


def run_a1_aggregation(
    comparison_rows: list[dict[str, str]],
    r5_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """A1 — Aggregation comparison.

    Groups R5 comparison rows by episode_aggregation (max / mean) and by
    window_aggregation. Reports mean AUROC, AUPRC, F1 per variant group.
    """
    by_ep_agg: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_win_agg: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_ep_win: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for row in comparison_rows:
        ep = row.get("episode_aggregation", "")
        win = row.get("window_aggregation", "")
        by_ep_agg[ep].append(row)
        by_win_agg[win].append(row)
        by_ep_win[(ep, win)].append(row)

    def _summarise(rows: list[dict[str, str]]) -> dict[str, Any]:
        aurocs = [_float_or_none(r.get("auroc")) for r in rows]
        auprcs = [_float_or_none(r.get("auprc")) for r in rows]
        f1s = [_float_or_none(r.get("f1")) for r in rows]
        finite_auroc = [v for v in aurocs if v is not None]
        finite_auprc = [v for v in auprcs if v is not None]
        finite_f1 = [v for v in f1s if v is not None]
        return {
            "row_count": len(rows),
            "scorers": sorted({r.get("scorer", "") for r in rows}),
            "auroc_mean": _safe_mean(finite_auroc),
            "auroc_max": _safe_max(finite_auroc),
            "auprc_mean": _safe_mean(finite_auprc),
            "auprc_max": _safe_max(finite_auprc),
            "f1_mean": _safe_mean(finite_f1),
            "f1_max": _safe_max(finite_f1),
        }

    episode_agg_summary = {ep: _summarise(rows) for ep, rows in sorted(by_ep_agg.items())}
    window_agg_summary = {win: _summarise(rows) for win, rows in sorted(by_win_agg.items())}
    cross_summary = {
        f"{ep}+{win}": _summarise(rows) for (ep, win), rows in sorted(by_ep_win.items())
    }

    best_auroc_row = max(
        comparison_rows,
        key=lambda r: _float_or_none(r.get("auroc")) or -1.0,
    )
    best_auprc_row = max(
        comparison_rows,
        key=lambda r: _float_or_none(r.get("auprc")) or -1.0,
    )

    result = {
        "ablation": "A1_aggregation",
        "status": "COMPLETED",
        "paper_note": (
            "Results are from the non-locked R5 TempGlitch validation family only. "
            "Bootstrap CIs remain wide. No superiority claim is supported."
        ),
        "episode_aggregation_summary": episode_agg_summary,
        "window_aggregation_summary": window_agg_summary,
        "cross_aggregation_summary": cross_summary,
        "best_auroc_configuration": {
            "scorer": best_auroc_row.get("scorer"),
            "window_aggregation": best_auroc_row.get("window_aggregation"),
            "episode_aggregation": best_auroc_row.get("episode_aggregation"),
            "auroc": _float_or_none(best_auroc_row.get("auroc")),
            "auprc": _float_or_none(best_auroc_row.get("auprc")),
            "f1": _float_or_none(best_auroc_row.get("f1")),
        },
        "best_auprc_configuration": {
            "scorer": best_auprc_row.get("scorer"),
            "window_aggregation": best_auprc_row.get("window_aggregation"),
            "episode_aggregation": best_auprc_row.get("episode_aggregation"),
            "auroc": _float_or_none(best_auprc_row.get("auroc")),
            "auprc": _float_or_none(best_auprc_row.get("auprc")),
            "f1": _float_or_none(best_auprc_row.get("f1")),
        },
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "wob_dependency_used": False,
        "input_sha256": _sha256(r5_dir / _R5_COMPARISON_CSV),
    }

    _write_json(output_dir / "r6_a1_aggregation_ablation.json", result)
    return result


def run_a2_surprise_distance(
    comparison_rows: list[dict[str, str]],
    r5_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """A2 — Surprise-distance comparison (MSE vs L2; cosine unavailable).

    Groups by window_aggregation family. Cosine distance was not computed
    during R5 and is NOT available from current artifacts.
    """
    lewm_rows = [r for r in comparison_rows if r.get("scorer", "").startswith("lewm")]
    baseline_rows = [r for r in comparison_rows if r.get("scorer", "") in BASELINE_SCORERS]

    mse_rows = [r for r in lewm_rows if r.get("window_aggregation", "") in MSE_WINDOW_AGGREGATIONS]
    l2_rows = [r for r in lewm_rows if r.get("window_aggregation", "") in L2_WINDOW_AGGREGATIONS]

    def _family_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
        aurocs = [_float_or_none(r.get("auroc")) for r in rows]
        auprcs = [_float_or_none(r.get("auprc")) for r in rows]
        f1s = [_float_or_none(r.get("f1")) for r in rows]
        finite_auroc = [v for v in aurocs if v is not None]
        finite_auprc = [v for v in auprcs if v is not None]
        finite_f1 = [v for v in f1s if v is not None]
        per_variant: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = f"{row.get('window_aggregation')}/{row.get('episode_aggregation')}"
            per_variant[key] = {
                "scorer": row.get("scorer"),
                "auroc": _float_or_none(row.get("auroc")),
                "auprc": _float_or_none(row.get("auprc")),
                "f1": _float_or_none(row.get("f1")),
                "auroc_ci": [
                    _float_or_none(row.get("auroc_ci_lower")),
                    _float_or_none(row.get("auroc_ci_upper")),
                ],
            }
        return {
            "row_count": len(rows),
            "auroc_mean": _safe_mean(finite_auroc),
            "auroc_max": _safe_max(finite_auroc),
            "auprc_mean": _safe_mean(finite_auprc),
            "auprc_max": _safe_max(finite_auprc),
            "f1_mean": _safe_mean(finite_f1),
            "per_variant": per_variant,
        }

    baseline_summary: dict[str, Any] = {}
    for row in baseline_rows:
        key = f"{row.get('scorer')}/{row.get('episode_aggregation')}"
        baseline_summary[key] = {
            "scorer": row.get("scorer"),
            "episode_aggregation": row.get("episode_aggregation"),
            "auroc": _float_or_none(row.get("auroc")),
            "auprc": _float_or_none(row.get("auprc")),
            "f1": _float_or_none(row.get("f1")),
        }

    result = {
        "ablation": "A2_surprise_distance",
        "status": "COMPLETED",
        "paper_note": (
            "MSE vs L2 comparison is from the non-locked R5 TempGlitch validation family only. "
            "Cosine distance was not computed during R5 and cannot be derived from current "
            "R5 artifacts. No superiority claim is supported."
        ),
        "mse_family": _family_summary(mse_rows),
        "l2_family": _family_summary(l2_rows),
        "cosine_family": {
            "status": "NOT_AVAILABLE_FROM_CURRENT_ARTIFACTS",
            "reason": (
                "Cosine surprise distance was not computed during the R5 evaluation. "
                "Current R5 score CSVs contain only mse_t1/t2/t3 and l2_t1/t2/t3 columns."
            ),
        },
        "baselines": baseline_summary,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "wob_dependency_used": False,
        "input_sha256": _sha256(r5_dir / _R5_COMPARISON_CSV),
    }

    _write_json(output_dir / "r6_a2_surprise_distance_ablation.json", result)
    return result


def run_a3_threshold_calibration(
    comparison_rows: list[dict[str, str]],
    r5_dir: Path,
    output_dir: Path,
    eval_json: dict[str, Any] | None,
) -> dict[str, Any]:
    """A3 — Threshold calibration summary.

    Reports stored threshold, F1, precision, recall, and FPR@95TPR for every
    configuration from the comparison CSV. A full per-threshold sweep requires
    per-episode scores that are not saved in the R5 artifact family.
    """
    configs: list[dict[str, Any]] = []
    for row in comparison_rows:
        threshold = _float_or_none(row.get("threshold"))
        configs.append(
            {
                "scorer": row.get("scorer"),
                "window_aggregation": row.get("window_aggregation"),
                "episode_aggregation": row.get("episode_aggregation"),
                "threshold": threshold,
                "threshold_source": row.get("threshold_source", "calibration_normal_p95"),
                "f1": _float_or_none(row.get("f1")),
                "precision": _float_or_none(row.get("precision")),
                "recall": _float_or_none(row.get("recall")),
                "fpr_at_95tpr": _float_or_none(row.get("fpr_at_95tpr")),
                "auroc": _float_or_none(row.get("auroc")),
                "auprc": _float_or_none(row.get("auprc")),
            }
        )

    calibration_episode_count: int | None = None
    if eval_json is not None:
        ep_counts = eval_json.get("episode_counts", {})
        calibration_episode_count = ep_counts.get("calibration_normal")

    thresholds = [c["threshold"] for c in configs if c["threshold"] is not None]
    threshold_range = {
        "min": min(thresholds) if thresholds else None,
        "max": max(thresholds) if thresholds else None,
        "count_distinct": len(set(thresholds)),
    }

    result = {
        "ablation": "A3_threshold_calibration",
        "status": "COMPLETED",
        "sweep_type": "single_point_per_config",
        "paper_note": (
            "Each threshold is the calibration_normal P95 of that configuration's episode scores. "
            "A full multi-point threshold sweep requires per-episode raw scores which are not "
            "saved in the current R5 artifact family. Mark sweep_complete=False."
        ),
        "sweep_complete": False,
        "missing_for_full_sweep": [
            "Per-episode prediction scores saved to CSV (not in current R5 artifacts). "
            "Re-run R5 eval with --save-episode-scores flag to enable a full sweep."
        ],
        "calibration_normal_episode_count": calibration_episode_count,
        "configurations": configs,
        "threshold_range": threshold_range,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "wob_dependency_used": False,
        "input_sha256": _sha256(r5_dir / _R5_COMPARISON_CSV),
    }

    _write_json(output_dir / "r6_a3_threshold_calibration_ablation.json", result)
    return result


def run_a4_failure_mode(
    manifest_rows: list[dict[str, str]],
    comparison_rows: list[dict[str, str]],
    r5_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """A4 — Failure-mode analysis.

    Analyses the R5 episode manifest to show per-category episode counts and
    label distribution. Reports which categories have imbalanced or absent
    coverage. Per-episode prediction data (required for episode-level
    false-positive / false-negative analysis) is not saved in the current R5
    artifact family; that limitation is noted explicitly.
    """
    eval_episodes = [r for r in manifest_rows if r.get("evaluation_role") != "calibration_normal"]
    calib_episodes = [r for r in manifest_rows if r.get("evaluation_role") == "calibration_normal"]

    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"normal": 0, "buggy": 0})
    missing_category: int = 0

    for row in eval_episodes:
        cat = row.get("category", "").strip()
        label = row.get("label", "").strip().lower()
        if not cat:
            missing_category += 1
            cat = "_MISSING_CATEGORY"
        if label in ("buggy", "normal"):
            by_category[cat][label] += 1

    category_analysis: dict[str, Any] = {}
    for cat, counts in sorted(by_category.items()):
        total = counts["normal"] + counts["buggy"]
        coverage_issue: str | None = None
        if counts["buggy"] == 0:
            coverage_issue = "NO_BUGGY_EPISODES_IN_CATEGORY"
        elif counts["normal"] == 0:
            coverage_issue = "NO_NORMAL_EPISODES_IN_CATEGORY"
        category_analysis[cat] = {
            "total": total,
            "normal": counts["normal"],
            "buggy": counts["buggy"],
            "coverage_issue": coverage_issue,
        }

    best_f1_scorer: dict[str, Any] | None = None
    worst_f1_scorer: dict[str, Any] | None = None
    if comparison_rows:
        lewm_rows = [r for r in comparison_rows if r.get("scorer", "").startswith("lewm")]
        if lewm_rows:
            valid = [(r, _float_or_none(r.get("f1"))) for r in lewm_rows]
            valid = [(r, f) for r, f in valid if f is not None]
            if valid:
                best_r, best_f = max(valid, key=lambda x: x[1])
                worst_r, worst_f = min(valid, key=lambda x: x[1])
                best_f1_scorer = {
                    "scorer": best_r.get("scorer"),
                    "window_aggregation": best_r.get("window_aggregation"),
                    "episode_aggregation": best_r.get("episode_aggregation"),
                    "f1": best_f,
                    "auroc": _float_or_none(best_r.get("auroc")),
                }
                worst_f1_scorer = {
                    "scorer": worst_r.get("scorer"),
                    "window_aggregation": worst_r.get("window_aggregation"),
                    "episode_aggregation": worst_r.get("episode_aggregation"),
                    "f1": worst_f,
                    "auroc": _float_or_none(worst_r.get("auroc")),
                }

    result = {
        "ablation": "A4_failure_mode",
        "status": "COMPLETED",
        "paper_note": (
            "Failure analysis uses the R5 episode manifest only. Per-episode predictions "
            "are not saved in the current R5 artifact family, so episode-level "
            "false-positive/false-negative breakdown is NOT AVAILABLE. Only category-level "
            "distribution is reported."
        ),
        "missing_for_full_failure_analysis": [
            "Per-episode prediction labels saved to CSV. "
            "Re-run R5 eval with --save-episode-predictions flag to enable FP/FN breakdown."
        ],
        "total_evaluation_episodes": len(eval_episodes),
        "total_calibration_episodes": len(calib_episodes),
        "episodes_with_missing_category": missing_category,
        "category_distribution": category_analysis,
        "categories_with_coverage_issue": [
            cat for cat, info in category_analysis.items() if info["coverage_issue"] is not None
        ],
        "best_f1_lewm_scorer": best_f1_scorer,
        "worst_f1_lewm_scorer": worst_f1_scorer,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "wob_dependency_used": False,
        "manifest_sha256": _sha256(r5_dir / _R5_EPISODE_MANIFEST_CSV),
    }

    _write_json(output_dir / "r6_a4_failure_mode_ablation.json", result)
    return result


def run_all_ablations(
    r5_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run A1–A4 and write a provenance summary."""
    _locked_guard(r5_dir)
    _locked_guard(output_dir)

    input_check = check_r5_inputs(r5_dir)
    if not input_check["required_files_present"]:
        missing = input_check["missing_required"]
        print(
            "ERROR: required R5 TempGlitch input files are missing:\n"
            + "\n".join(f"  {p}" for p in missing),
            file=sys.stderr,
        )
        print(
            "\nThese files are produced by the R5 identical-episode evaluation pipeline:\n"
            "  python scripts/run_r5_tempglitch_identical_episode_evaluation.py ...",
            file=sys.stderr,
        )
        return {
            "status": "BLOCKED_MISSING_R5_SCORE_FILES",
            "paper_valid": False,
            "missing_required": missing,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        }

    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_rows = _read_csv(r5_dir / _R5_COMPARISON_CSV)
    manifest_rows = _read_csv(r5_dir / _R5_EPISODE_MANIFEST_CSV)

    eval_json: dict[str, Any] | None = None
    if (r5_dir / _R5_EVAL_JSON).exists():
        eval_json = _read_json(r5_dir / _R5_EVAL_JSON)

    results: dict[str, Any] = {}

    results["a1"] = run_a1_aggregation(comparison_rows, r5_dir, output_dir)
    results["a2"] = run_a2_surprise_distance(comparison_rows, r5_dir, output_dir)
    results["a3"] = run_a3_threshold_calibration(comparison_rows, r5_dir, output_dir, eval_json)
    results["a4"] = run_a4_failure_mode(manifest_rows, comparison_rows, r5_dir, output_dir)

    all_complete = all(v.get("status") == "COMPLETED" for v in results.values())

    provenance = {
        "status": "R6_TEMPGLITCH_CPU_READY" if all_complete else "PARTIAL_COMPLETION",
        "paper_valid": all_complete,
        "ablations_run": list(results.keys()),
        "r5_dir": str(r5_dir),
        "output_dir": str(output_dir),
        "input_files": {name: sha for name, sha in input_check["present"].items()},
        "optional_input_files": {
            name: sha for name, sha in input_check["optional_present"].items()
        },
        "protocol_notes": [
            "All ablations use validated R5 TempGlitch non-locked identical-episode outputs.",
            "No locked test was materialized or scored.",
            "No WOB dependency was used.",
            "Cosine distance is NOT_AVAILABLE_FROM_CURRENT_ARTIFACTS.",
            "A3 threshold sweep is single-point (per-episode scores not saved in R5 artifacts).",
            "A4 failure mode is category-level only (per-episode predictions not saved).",
        ],
        "claim_boundary": [
            "Do not claim SIGReg benefit (A5 not run).",
            "Do not claim action-conditioning benefit (A11 not run).",
            "Do not claim superiority or SOTA.",
            "Do not claim WOB or cross-game generalization.",
            "All results are from the non-locked validation family only.",
        ],
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "wob_dependency_used": False,
        "results_summary": {
            ablation: {
                "status": r.get("status"),
                "output_file": str(output_dir / f"r6_{ablation}_ablation.json"),
            }
            for ablation, r in results.items()
        },
    }

    _write_json(output_dir / "r6_tempglitch_cpu_provenance.json", provenance)
    provenance["ablation_results"] = results
    return provenance


def run_single_ablation(
    ablation: str,
    r5_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run a single ablation (a1–a4)."""
    _locked_guard(r5_dir)

    input_check = check_r5_inputs(r5_dir)
    if not input_check["required_files_present"]:
        missing = input_check["missing_required"]
        print(
            "ERROR: required R5 TempGlitch input files are missing:\n"
            + "\n".join(f"  {p}" for p in missing),
            file=sys.stderr,
        )
        return {
            "status": "BLOCKED_MISSING_R5_SCORE_FILES",
            "paper_valid": False,
            "missing_required": missing,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_rows = _read_csv(r5_dir / _R5_COMPARISON_CSV)
    manifest_rows = _read_csv(r5_dir / _R5_EPISODE_MANIFEST_CSV)

    eval_json: dict[str, Any] | None = None
    if (r5_dir / _R5_EVAL_JSON).exists():
        eval_json = _read_json(r5_dir / _R5_EVAL_JSON)

    if ablation == "a1":
        return run_a1_aggregation(comparison_rows, r5_dir, output_dir)
    if ablation == "a2":
        return run_a2_surprise_distance(comparison_rows, r5_dir, output_dir)
    if ablation == "a3":
        return run_a3_threshold_calibration(comparison_rows, r5_dir, output_dir, eval_json)
    if ablation == "a4":
        return run_a4_failure_mode(manifest_rows, comparison_rows, r5_dir, output_dir)

    raise ValueError(f"Unknown ablation: {ablation!r}. Expected one of {ABLATION_IDS} or 'all'.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="R6 CPU-safe TempGlitch ablation runner (A1–A4).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--r5-output-dir",
        type=Path,
        default=DEFAULT_R5_DIR,
        help="Path to validated R5 TempGlitch identical-episode output directory.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for R6 ablation results.",
    )
    p.add_argument(
        "--ablation",
        choices=list(ABLATION_IDS) + ["all"],
        default="all",
        help="Which ablation to run (a1/a2/a3/a4/all). Default: all.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.ablation == "all":
        result = run_all_ablations(args.r5_output_dir, args.output_dir)
    else:
        result = run_single_ablation(args.ablation, args.r5_output_dir, args.output_dir)

    print(json.dumps(result, indent=2))

    status = result.get("status", "")
    if status in ("COMPLETED", "R6_TEMPGLITCH_CPU_READY"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
