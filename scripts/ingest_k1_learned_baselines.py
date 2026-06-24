from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from validate_learned_baselines import validate_learned_baselines

from glitch_detection.gate6_data import sha256_file
from glitch_detection.seed_aggregation import aggregate_seed_metrics
from glitch_detection.statistics import delong_auroc_test, paired_bootstrap_delta
from glitch_detection.tempglitch_followup import (
    FOLLOWUP_COMPARISON_FIELDS,
    FOLLOWUP_EPISODE_SCORE_FIELDS,
    evaluate_followup_configuration,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_K1_OUTPUT_ROOT = ROOT / "outputs" / "learned_baselines_k1" / "learned_baselines_k1"
DEFAULT_FOLLOWUP_OUTPUT_DIR = ROOT / "outputs" / "tempglitch_followup_pair_disjoint"
AGGREGATIONS = ("mean", "max", "top2_mean")
LEARNED_BASELINES = ("video_autoencoder", "cnn_lstm", "video_transformer")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: tuple[str, ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _float_text(value: float | None) -> str:
    return "" if value is None else f"{float(value):.12g}"


def _config_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["method_family"],
        row["method"],
        row["window_scorer"],
        row["seed"],
        row["episode_aggregation"],
    )


def _aggregate_scores(values: list[float], mode: str) -> float:
    if not values:
        raise ValueError("Episode aggregation requires at least one score.")
    ordered = sorted(float(value) for value in values)
    if mode == "mean":
        return sum(ordered) / len(ordered)
    if mode == "max":
        return ordered[-1]
    if mode == "top2_mean":
        top = ordered[-2:] if len(ordered) >= 2 else ordered
        return sum(top) / len(top)
    raise ValueError(f"Unsupported aggregation mode: {mode}")


def _support_rows_from_followup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    support_rows: dict[str, dict[str, str]] = {}
    for row in rows:
        episode_id = row["source_episode_id"]
        support = {
            "source_episode_id": episode_id,
            "source": row["source"],
            "pair_id": row["pair_id"],
            "category": row["category"],
            "label": row["label"],
            "dataset_name": row["dataset_name"],
            "evaluation_role": row["evaluation_role"],
        }
        existing = support_rows.get(episode_id)
        if existing is None:
            support_rows[episode_id] = support
            continue
        if existing != support:
            raise ValueError(f"Inconsistent follow-up support metadata for {episode_id}.")
    return dict(sorted(support_rows.items()))


def _evaluation_rows(rows: list[dict[str, str]]) -> list[dict[str, float | int | str]]:
    evaluation = [
        {
            "source_episode_id": row["source_episode_id"],
            "pair_id": row["pair_id"],
            "label": 1 if row["label"].lower() == "buggy" else 0,
            "score": float(row["score"]),
        }
        for row in rows
        if row["evaluation_role"] == "evaluation"
    ]
    return sorted(evaluation, key=lambda row: (str(row["pair_id"]), str(row["source_episode_id"])))


def _load_followup_bundle(followup_output_dir: Path) -> dict[str, Any]:
    followup_metrics = _read_json(followup_output_dir / "followup_metrics.json")
    followup_episode_rows = _read_csv_rows(followup_output_dir / "followup_episode_scores.csv")
    followup_comparison_rows = _read_csv_rows(followup_output_dir / "followup_comparison.csv")
    episode_rows_by_key: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(
        list
    )
    for row in followup_episode_rows:
        episode_rows_by_key[_config_key(row)].append(row)
    return {
        "metrics": followup_metrics,
        "episode_rows": followup_episode_rows,
        "comparison_rows": followup_comparison_rows,
        "support_rows": _support_rows_from_followup(followup_episode_rows),
        "episode_rows_by_key": dict(episode_rows_by_key),
    }


def _build_learned_rows(
    *,
    k1_output_root: Path,
    support_rows: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[tuple[str, str], list[dict[str, str]]]]:
    episode_rows: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    rows_by_config: dict[tuple[str, str], list[dict[str, str]]] = {}
    for baseline_name in LEARNED_BASELINES:
        checkpoint_path = k1_output_root / f"{baseline_name}.pt"
        score_path = k1_output_root / f"{baseline_name}_validation_scores.csv"
        score_rows = _read_csv_rows(score_path)
        scores_by_source: dict[str, list[float]] = defaultdict(list)
        for row in score_rows:
            scores_by_source[row["source"]].append(float(row["score"]))
        missing_sources = sorted(set(support_rows) - set(scores_by_source))
        if missing_sources:
            raise ValueError(
                f"{baseline_name} is missing follow-up support sources: {missing_sources[:5]}"
            )
        for aggregation in AGGREGATIONS:
            config_episode_rows: list[dict[str, str]] = []
            for episode_id, support in support_rows.items():
                config_episode_rows.append(
                    {
                        "method_family": "learned_baseline",
                        "method": baseline_name,
                        "window_scorer": baseline_name,
                        "seed": "",
                        "episode_aggregation": aggregation,
                        "source_episode_id": episode_id,
                        "source": support["source"],
                        "pair_id": support["pair_id"],
                        "category": support["category"],
                        "label": support["label"],
                        "dataset_name": support["dataset_name"],
                        "evaluation_role": support["evaluation_role"],
                        "window_count": str(len(scores_by_source[episode_id])),
                        "score": _float_text(
                            _aggregate_scores(scores_by_source[episode_id], aggregation)
                        ),
                    }
                )
            evaluation = evaluate_followup_configuration(config_episode_rows, n_bootstrap=1000)
            metrics = evaluation["metrics"]
            intervals = evaluation["confidence_intervals"]
            comparison_rows.append(
                {
                    "method_family": "learned_baseline",
                    "method": baseline_name,
                    "window_scorer": baseline_name,
                    "seed": "",
                    "episode_aggregation": aggregation,
                    "raw_score_path": str(score_path),
                    "raw_score_sha256": sha256_file(score_path),
                    "checkpoint_sha256": sha256_file(checkpoint_path),
                    "threshold": _float_text(evaluation["threshold"]),
                    "threshold_source": str(evaluation["threshold_source"]),
                    "auroc": _float_text(metrics["auroc"]),
                    "auprc": _float_text(metrics["auprc"]),
                    "f1": _float_text(metrics["f1"]),
                    "precision": _float_text(metrics["precision"]),
                    "recall": _float_text(metrics["recall"]),
                    "balanced_accuracy": _float_text(metrics["balanced_accuracy"]),
                    "fpr_at_95_tpr": _float_text(metrics["fpr_at_95_tpr"]),
                    "true_positive": _float_text(metrics["true_positive"]),
                    "false_positive": _float_text(metrics["false_positive"]),
                    "false_negative": _float_text(metrics["false_negative"]),
                    "true_negative": _float_text(metrics["true_negative"]),
                    "calibration_episode_count": str(metrics["calibration_episode_count"]),
                    "evaluation_episode_count": str(metrics["evaluation_episode_count"]),
                    "positive_episode_count": str(metrics["positive_episode_count"]),
                    "negative_episode_count": str(metrics["negative_episode_count"]),
                    "calibration_episode_ids": ",".join(evaluation["calibration_episode_ids"]),
                    "confidence_interval_group_key": str(
                        evaluation["confidence_interval_group_key"]
                    ),
                    "auroc_ci_lower": _float_text(intervals["auroc"]["lower"]),
                    "auroc_ci_upper": _float_text(intervals["auroc"]["upper"]),
                    "auroc_ci_valid_bootstrap_count": str(
                        intervals["auroc"]["valid_bootstrap_count"]
                    ),
                    "f1_ci_lower": _float_text(intervals["f1"]["lower"]),
                    "f1_ci_upper": _float_text(intervals["f1"]["upper"]),
                    "f1_ci_valid_bootstrap_count": str(intervals["f1"]["valid_bootstrap_count"]),
                }
            )
            episode_rows.extend(config_episode_rows)
            rows_by_config[(baseline_name, aggregation)] = config_episode_rows
    return episode_rows, comparison_rows, rows_by_config


def _best_row(rows: list[dict[str, str]], *, method_family: str | None = None) -> dict[str, str]:
    candidates = (
        rows
        if method_family is None
        else [row for row in rows if row["method_family"] == method_family]
    )
    if not candidates:
        raise ValueError("No rows available for best-row selection.")
    return max(candidates, key=lambda row: float(row["auroc"]))


def _best_row_by_method(rows: list[dict[str, str]], method: str) -> dict[str, str]:
    candidates = [row for row in rows if row["method"] == method]
    if not candidates:
        raise ValueError(f"No rows available for method {method}.")
    return max(candidates, key=lambda row: float(row["auroc"]))


def _paired_summary(
    rows_a: list[dict[str, str]],
    rows_b: list[dict[str, str]],
) -> dict[str, Any]:
    eval_a = _evaluation_rows(rows_a)
    eval_b = _evaluation_rows(rows_b)
    labels = [int(row["label"]) for row in eval_a]
    scores_a = [float(row["score"]) for row in eval_a]
    scores_b = [float(row["score"]) for row in eval_b]
    return {
        "delta_auroc": paired_bootstrap_delta(
            eval_a, eval_b, "auroc", group_key="pair_id", n_bootstrap=1000, seed=42
        ),
        "delta_auprc": paired_bootstrap_delta(
            eval_a, eval_b, "auprc", group_key="pair_id", n_bootstrap=1000, seed=42
        ),
        "delong_auroc": delong_auroc_test(labels, scores_a, scores_b),
    }


def _markdown_table(rows: list[dict[str, str]]) -> str:
    header = (
        "| Method | Episode aggregation | AUROC | AUPRC | F1 | Precision | Recall | "
        "Balanced accuracy | FPR@95TPR | AUROC 95% CI | F1 95% CI |\n"
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |\n"
    )
    body = "".join(
        (
            f"| `{row['method']}` | `{row['episode_aggregation']}` | {row['auroc']} | {row['auprc']} | "
            f"{row['f1']} | {row['precision']} | {row['recall']} | {row['balanced_accuracy']} | "
            f"{row['fpr_at_95_tpr']} | "
            f"[{row['auroc_ci_lower']}, {row['auroc_ci_upper']}] | "
            f"[{row['f1_ci_lower']}, {row['f1_ci_upper']}] |\n"
        )
        for row in rows
    )
    return header + body


def ingest_k1_learned_baselines(
    *,
    k1_output_root: Path,
    followup_output_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    validation_receipt = validate_learned_baselines(k1_output_root)
    followup_bundle = _load_followup_bundle(followup_output_dir)
    learned_episode_rows, learned_comparison_rows, rows_by_config = _build_learned_rows(
        k1_output_root=k1_output_root,
        support_rows=followup_bundle["support_rows"],
    )

    episode_scores_path = _write_csv_rows(
        output_dir / "k1_followup_episode_scores.csv",
        learned_episode_rows,
        FOLLOWUP_EPISODE_SCORE_FIELDS,
    )
    comparison_path = _write_csv_rows(
        output_dir / "k1_followup_comparison.csv",
        learned_comparison_rows,
        FOLLOWUP_COMPARISON_FIELDS,
    )

    best_lewm_row = _best_row(followup_bundle["comparison_rows"], method_family="lewm")
    best_simple_row = _best_row(followup_bundle["comparison_rows"], method_family="baseline")
    best_frame_diff_row = _best_row_by_method(followup_bundle["comparison_rows"], "frame_diff")
    best_feature_distance_row = _best_row_by_method(
        followup_bundle["comparison_rows"], "feature_distance"
    )
    best_rows_by_method = {
        name: _best_row_by_method(learned_comparison_rows, name) for name in LEARNED_BASELINES
    }
    best_learned_row = _best_row(learned_comparison_rows)

    best_lewm_episode_rows = followup_bundle["episode_rows_by_key"][_config_key(best_lewm_row)]
    lewm_seed_rows = [
        row
        for row in followup_bundle["comparison_rows"]
        if row["method_family"] == "lewm"
        and row["window_scorer"] == best_lewm_row["window_scorer"]
        and row["episode_aggregation"] == best_lewm_row["episode_aggregation"]
    ]
    lewm_seed_aggregate = aggregate_seed_metrics(
        [
            {
                "seed": int(row["seed"]),
                "auroc": float(row["auroc"]),
                "auprc": float(row["auprc"]),
                "f1": float(row["f1"]),
                "precision": float(row["precision"]),
                "recall": float(row["recall"]),
                "balanced_accuracy": float(row["balanced_accuracy"]),
                "fpr_at_95_tpr": float(row["fpr_at_95_tpr"]),
            }
            for row in lewm_seed_rows
        ]
    )

    paired_vs_best_lewm = {
        name: _paired_summary(
            rows_by_config[(name, best_rows_by_method[name]["episode_aggregation"])],
            best_lewm_episode_rows,
        )
        for name in LEARNED_BASELINES
    }
    paired_best_learned_vs_frame_diff = _paired_summary(
        rows_by_config[(best_learned_row["method"], best_learned_row["episode_aggregation"])],
        followup_bundle["episode_rows_by_key"][_config_key(best_frame_diff_row)],
    )
    paired_best_learned_vs_feature_distance = _paired_summary(
        rows_by_config[(best_learned_row["method"], best_learned_row["episode_aggregation"])],
        followup_bundle["episode_rows_by_key"][_config_key(best_feature_distance_row)],
    )

    summary = {
        "status": "k1_learned_baselines_ingested",
        "k1_output_root": str(k1_output_root),
        "followup_output_dir": str(followup_output_dir),
        "validation_receipt_path": str(k1_output_root / "learned_baselines_validation.json"),
        "validation_receipt_sha256": sha256_file(
            k1_output_root / "learned_baselines_validation.json"
        ),
        "canonical_support": {
            "calibration_episode_ids": followup_bundle["metrics"]["calibration_episode_ids"],
            "calibration_episode_count": followup_bundle["metrics"]["manifest_summary"][
                "calibration_episode_count"
            ],
            "evaluation_normal_episode_count": followup_bundle["metrics"]["manifest_summary"][
                "evaluation_normal_episode_count"
            ],
            "evaluation_buggy_episode_count": followup_bundle["metrics"]["manifest_summary"][
                "evaluation_buggy_episode_count"
            ],
            "evaluation_total_episode_count": (
                followup_bundle["metrics"]["manifest_summary"]["evaluation_normal_episode_count"]
                + followup_bundle["metrics"]["manifest_summary"]["evaluation_buggy_episode_count"]
            ),
        },
        "validation_receipt": validation_receipt,
        "comparison_path": str(comparison_path),
        "comparison_sha256": sha256_file(comparison_path),
        "episode_scores_path": str(episode_scores_path),
        "episode_scores_sha256": sha256_file(episode_scores_path),
        "best_lewm_row": best_lewm_row,
        "best_lewm_seed_aggregate": lewm_seed_aggregate,
        "best_simple_baseline_row": best_simple_row,
        "best_frame_diff_row": best_frame_diff_row,
        "best_feature_distance_row": best_feature_distance_row,
        "best_rows_by_method": best_rows_by_method,
        "best_learned_row": best_learned_row,
        "paired_vs_best_lewm": paired_vs_best_lewm,
        "paired_best_learned_vs_frame_diff": paired_best_learned_vs_frame_diff,
        "paired_best_learned_vs_feature_distance": paired_best_learned_vs_feature_distance,
        "results": learned_comparison_rows,
    }
    summary_path = _write_json(output_dir / "k1_followup_summary.json", summary)

    report_lines = [
        "# K1 Learned Baselines on TempGlitch Follow-up Support",
        "",
        f"- Status: `{summary['status']}`",
        f"- Validation receipt SHA256: `{summary['validation_receipt_sha256']}`",
        f"- Canonical calibration episodes: `{', '.join(summary['canonical_support']['calibration_episode_ids'])}`",
        f"- Evaluation support: `{summary['canonical_support']['evaluation_normal_episode_count']}` normal-negative + "
        f"`{summary['canonical_support']['evaluation_buggy_episode_count']}` buggy-positive episodes",
        "",
        "## Best Learned Rows",
        "",
        _markdown_table([best_rows_by_method[name] for name in LEARNED_BASELINES]),
        "",
        "## Comparison Anchors",
        "",
        f"- Best LeWM row: `{best_lewm_row['window_scorer']}` seed `{best_lewm_row['seed']}` "
        f"aggregation `{best_lewm_row['episode_aggregation']}` with AUROC `{best_lewm_row['auroc']}`.",
        f"- Best simple baseline AUROC row: `{best_simple_row['method']}` aggregation "
        f"`{best_simple_row['episode_aggregation']}` with AUROC `{best_simple_row['auroc']}`.",
        f"- Best learned baseline AUROC row: `{best_learned_row['method']}` aggregation "
        f"`{best_learned_row['episode_aggregation']}` with AUROC `{best_learned_row['auroc']}`.",
    ]
    report_path = output_dir / "K1_FOLLOWUP_REPORT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    summary["summary_sha256"] = sha256_file(summary_path)
    summary["report_path"] = str(report_path)
    summary["report_sha256"] = sha256_file(report_path)
    _write_json(summary_path, summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest validated K1 learned-baseline artifacts onto the existing TempGlitch follow-up support."
    )
    parser.add_argument("--k1-output-root", type=Path, default=DEFAULT_K1_OUTPUT_ROOT)
    parser.add_argument("--followup-output-dir", type=Path, default=DEFAULT_FOLLOWUP_OUTPUT_DIR)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_K1_OUTPUT_ROOT.parent / "analysis",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = ingest_k1_learned_baselines(
        k1_output_root=args.k1_output_root.resolve(),
        followup_output_dir=args.followup_output_dir.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
