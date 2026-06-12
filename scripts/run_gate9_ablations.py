from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from glitch_detection.evaluate import auroc, average_precision, binary_metrics
from glitch_detection.lewm_adapter import sha256_file
from glitch_detection.lewm_lance_eval import (
    read_csv_rows,
    runtime_provenance,
    validate_manifest_rows,
    validate_score_alignment,
    write_csv_rows,
)

COMPARISON_FIELDS = (
    "scorer",
    "auroc",
    "auprc",
    "pr_auc",
    "threshold",
    "threshold_source",
    "precision",
    "recall",
    "f1",
    "evaluation_window_count",
    "positive_window_count",
)


def validate_gate9_alignment(
    manifest_rows: list[dict[str, str]],
    lewm_rows: list[dict[str, str]],
    baseline_rows: list[dict[str, str]],
) -> None:
    validate_score_alignment(manifest_rows, lewm_rows)
    expected_ids = [row["window_id"] for row in manifest_rows]
    if expected_ids != [row["window_id"] for row in baseline_rows]:
        raise ValueError("Baseline rows must match the canonical manifest in exact ordered form.")
    for row in baseline_rows:
        for field in ("frame_diff", "feature_distance"):
            if not math.isfinite(float(row[field])):
                raise ValueError(f"Baseline score field {field} must be finite.")


def aggregate_lewm_rows(rows: list[dict[str, str]]) -> dict[str, list[float]]:
    output = {
        "lewm_mse_mean": [],
        "lewm_mse_max": [],
        "lewm_mse_top2_mean": [],
        "lewm_l2_mean": [],
        "lewm_l2_max": [],
        "lewm_l2_top2_mean": [],
    }
    for row in rows:
        for distance in ("mse", "l2"):
            values = np.asarray(
                [float(row[f"{distance}_t{index}"]) for index in range(1, 4)],
                dtype=np.float64,
            )
            if not np.isfinite(values).all():
                raise ValueError("Gate 9 requires finite LeWM transition scores.")
            output[f"lewm_{distance}_mean"].append(float(values.mean()))
            output[f"lewm_{distance}_max"].append(float(values.max()))
            output[f"lewm_{distance}_top2_mean"].append(float(np.partition(values, 1)[1:].mean()))
    return output


def _evaluate_scorer(
    name: str,
    values: list[float],
    manifest_rows: list[dict[str, str]],
) -> dict[str, Any]:
    calibration_indices = [
        index
        for index, row in enumerate(manifest_rows)
        if row["evaluation_role"] == "calibration_normal"
    ]
    evaluation_indices = [
        index for index, row in enumerate(manifest_rows) if row["evaluation_role"] == "evaluation"
    ]
    calibration_values = [values[index] for index in calibration_indices]
    if not calibration_values:
        raise ValueError(f"{name} has no calibration-normal scores.")
    threshold = float(np.percentile(calibration_values, 95, method="linear"))
    labels = [int(manifest_rows[index]["label"].lower() == "buggy") for index in evaluation_indices]
    evaluation_values = [values[index] for index in evaluation_indices]
    if not labels or not any(labels) or all(labels):
        raise ValueError("Gate 9 evaluation requires both normal and buggy windows.")
    predictions = [int(value >= threshold) for value in evaluation_values]
    f1_metrics = binary_metrics(labels, predictions)
    auprc = average_precision(labels, evaluation_values)
    metric_auroc = auroc(labels, evaluation_values)
    if auprc is None or metric_auroc is None:
        raise ValueError(f"{name} produced undefined primary metrics.")
    calibration_episodes = sorted(
        {manifest_rows[index]["source_episode_id"] for index in calibration_indices}
    )
    return {
        "scorer": name,
        "auroc": metric_auroc,
        "auprc": auprc,
        "pr_auc": auprc,
        "threshold": threshold,
        "threshold_percentile": 95,
        "threshold_source": "calibration_normal_p95",
        "calibration_window_count": len(calibration_indices),
        "calibration_episode_ids": calibration_episodes,
        "evaluation_window_count": len(evaluation_indices),
        "positive_window_count": sum(labels),
        "negative_window_count": len(labels) - sum(labels),
        **f1_metrics,
    }


def evaluate_gate9_rows(
    manifest_rows: list[dict[str, str]],
    lewm_rows: list[dict[str, str]],
    baseline_rows: list[dict[str, str]],
) -> dict[str, Any]:
    validate_gate9_alignment(manifest_rows, lewm_rows, baseline_rows)
    scorer_values = aggregate_lewm_rows(lewm_rows)
    scorer_values.update(
        {
            "baseline_frame_diff": [float(row["frame_diff"]) for row in baseline_rows],
            "baseline_feature_distance": [float(row["feature_distance"]) for row in baseline_rows],
        }
    )
    if any(not math.isfinite(value) for values in scorer_values.values() for value in values):
        raise ValueError("Gate 9 scorer inputs must all be finite.")
    metrics = {
        name: _evaluate_scorer(name, values, manifest_rows)
        for name, values in scorer_values.items()
    }
    evaluation_rows = [row for row in manifest_rows if row["evaluation_role"] == "evaluation"]
    positive_count = sum(row["label"].lower() == "buggy" for row in evaluation_rows)
    buggy_episodes = sorted(
        {row["source_episode_id"] for row in evaluation_rows if row["label"].lower() == "buggy"}
    )
    return {
        "status": "gate9_evaluated",
        "protocol": "validation_only_nonlocked_window_level_pilot",
        "primary_metrics": ["auroc", "auprc"],
        "secondary_metric": "f1_at_calibration_normal_p95",
        "metrics": metrics,
        "class_prevalence": {
            "evaluation_window_count": len(evaluation_rows),
            "positive_window_count": positive_count,
            "negative_window_count": len(evaluation_rows) - positive_count,
            "positive_fraction": positive_count / len(evaluation_rows),
        },
        "buggy_episode_ids": buggy_episodes,
        "pilot_limitations": [
            "Window rows within an episode are correlated.",
            "The evaluation contains only one non-locked buggy episode.",
            "The Gate 6 checkpoint is a one-epoch, 16-step training pilot.",
            "These metrics do not support broad superiority or temporal-localization claims.",
        ],
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def run_gate9(
    *,
    manifest_path: Path,
    lewm_scores_path: Path,
    baseline_scores_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    manifest_rows = read_csv_rows(manifest_path)
    lewm_rows = read_csv_rows(lewm_scores_path)
    baseline_rows = read_csv_rows(baseline_scores_path)
    validate_manifest_rows(manifest_rows)
    result = evaluate_gate9_rows(manifest_rows, lewm_rows, baseline_rows)
    result.update(
        {
            "manifest_sha256": sha256_file(manifest_path),
            "lewm_scores_sha256": sha256_file(lewm_scores_path),
            "baseline_scores_sha256": sha256_file(baseline_scores_path),
            "environment": runtime_provenance(include_lewm=False),
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "ablation_results.json"
    comparison_path = write_csv_rows(
        output_dir / "comparison.csv",
        list(result["metrics"].values()),
        COMPARISON_FIELDS,
    )
    result["comparison_sha256"] = sha256_file(comparison_path)
    results_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["results_path"] = str(results_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate Gate 7 LeWM and Gate 8 baselines with frozen P95 thresholds."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--lewm-scores", required=True, type=Path)
    parser.add_argument("--baseline-scores", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    for path in (args.manifest, args.lewm_scores, args.baseline_scores):
        if not path.is_file():
            raise FileNotFoundError(f"Missing Gate 9 input: {path}")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "manifest_sha256": sha256_file(args.manifest),
                    "lewm_scores_sha256": sha256_file(args.lewm_scores),
                    "baseline_scores_sha256": sha256_file(args.baseline_scores),
                    "output_dir": str(args.output_dir),
                    "locked_test_materialized": False,
                    "locked_test_scored": False,
                },
                indent=2,
            )
        )
        return
    print(
        json.dumps(
            run_gate9(
                manifest_path=args.manifest,
                lewm_scores_path=args.lewm_scores,
                baseline_scores_path=args.baseline_scores,
                output_dir=args.output_dir,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
