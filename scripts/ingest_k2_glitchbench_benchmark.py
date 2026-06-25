from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from glitch_detection.gate6_data import sha256_file
from glitch_detection.seed_aggregation import aggregate_seed_metrics

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_ROOT = ROOT / "outputs" / "glitchbench_k2_download"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "glitchbench_k2_intake"
PREFERRED_LEWM_AGGREGATIONS = ("mean", "max")
REQUIRED_FILES = (
    "bundle_validation.json",
    "glitchbench_benchmark_metrics.csv",
    "glitchbench_benchmark_summary.json",
    "lewm_artifact_validation.json",
    "train_normal_manifest.csv",
    "validation_manifest.csv",
)
LEARNED_BASELINES = ("video_autoencoder", "cnn_lstm", "video_transformer")
SIMPLE_BASELINES = ("frame_diff", "feature_distance")
LEWM_SEEDS = (42, 43, 44)
LEWM_AGGREGATIONS = ("mean", "max")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _float_text(value: float) -> str:
    return f"{float(value):.12g}"


def locate_bundle_root(root: Path) -> Path:
    required = {root / name for name in REQUIRED_FILES}
    if all(path.is_file() for path in required):
        return root
    candidates = [
        path.parent
        for path in root.rglob("glitchbench_benchmark_summary.json")
        if all((path.parent / name).is_file() for name in REQUIRED_FILES)
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValueError(f"Multiple K2 bundle roots found under: {root}")
    raise FileNotFoundError(f"Could not locate a K2 bundle root under: {root}")


def _best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("No rows available for best-row selection.")
    return max(
        rows,
        key=lambda row: (
            float(row["auroc"]),
            float(row["auprc"]),
            -float(row["fpr_at_95_tpr"]),
        ),
    )


def _best_rows_by_method(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    methods = sorted({str(row["method"]) for row in rows})
    return {
        method: _best_row([row for row in rows if row["method"] == method]) for method in methods
    }


def _lewm_seed_aggregate(
    rows: list[dict[str, Any]],
) -> tuple[str, dict[str, dict[str, float | int]], list[dict[str, Any]]]:
    by_aggregation: dict[str, list[dict[str, Any]]] = {}
    for aggregation in PREFERRED_LEWM_AGGREGATIONS:
        aggregation_rows = [row for row in rows if row["aggregation"] == aggregation]
        if aggregation_rows:
            by_aggregation[aggregation] = aggregation_rows
    if not by_aggregation:
        raise ValueError("No LeWM aggregation rows available.")
    best_aggregation = max(
        by_aggregation,
        key=lambda aggregation: (
            sum(float(row["auroc"]) for row in by_aggregation[aggregation])
            / len(by_aggregation[aggregation]),
            -PREFERRED_LEWM_AGGREGATIONS.index(aggregation),
        ),
    )
    best_rows = by_aggregation[best_aggregation]
    return (
        best_aggregation,
        aggregate_seed_metrics(
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
                for row in best_rows
            ]
        ),
        best_rows,
    )


def _validate_score_file(path: Path, *, expected_count: int) -> dict[str, Any]:
    rows = _read_csv_rows(path)
    if len(rows) != expected_count:
        raise ValueError(f"Expected {expected_count} rows in {path.name}, found {len(rows)}.")
    invalid = 0
    for row in rows:
        try:
            float(row["score"])
        except (KeyError, TypeError, ValueError):
            invalid += 1
    if invalid:
        raise ValueError(f"{path.name} contains {invalid} invalid score rows.")
    return {"path": str(path), "sha256": sha256_file(path), "row_count": len(rows)}


def ingest_k2_glitchbench_benchmark(
    *,
    bundle_root: Path,
    output_dir: Path,
    tarball_path: Path | None = None,
    tarball_sha256_sidecar_path: Path | None = None,
) -> dict[str, Any]:
    bundle_root = locate_bundle_root(bundle_root)
    summary = _read_json(bundle_root / "glitchbench_benchmark_summary.json")
    bundle_validation = _read_json(bundle_root / "bundle_validation.json")
    lewm_artifact_validation = _read_json(bundle_root / "lewm_artifact_validation.json")
    metrics_rows = _read_csv_rows(bundle_root / "glitchbench_benchmark_metrics.csv")
    train_manifest_rows = _read_csv_rows(bundle_root / "train_normal_manifest.csv")
    validation_manifest_rows = _read_csv_rows(bundle_root / "validation_manifest.csv")

    if summary.get("status") != "k2_complete_lewm_and_baselines":
        raise ValueError("K2 summary status must be k2_complete_lewm_and_baselines.")
    if summary.get("baseline_only") is not False:
        raise ValueError("K2 scientific intake requires baseline_only=false.")
    if summary.get("locked_test_materialized") is not False:
        raise ValueError("K2 summary must report locked_test_materialized=false.")
    if summary.get("locked_test_scored") is not False:
        raise ValueError("K2 summary must report locked_test_scored=false.")
    if bundle_validation.get("status") != "validated":
        raise ValueError("bundle_validation.json must report status=validated.")
    if bundle_validation.get("locked_test_materialized") is not False:
        raise ValueError("bundle_validation.json must report locked_test_materialized=false.")
    if bundle_validation.get("locked_test_scored") is not False:
        raise ValueError("bundle_validation.json must report locked_test_scored=false.")

    if int(summary["train_normal_clip_count"]) != len(train_manifest_rows):
        raise ValueError("Summary train_normal_clip_count does not match train manifest rows.")
    if int(summary["validation_clip_count"]) != len(validation_manifest_rows):
        raise ValueError("Summary validation_clip_count does not match validation manifest rows.")

    expected_metric_count = (
        len(summary["simple_results"])
        + len(summary["learned_results"])
        + len(summary["lewm_results"])
    )
    if expected_metric_count != len(metrics_rows):
        raise ValueError("Metrics CSV row count does not match summary result counts.")

    method_counts = Counter(row["method"] for row in metrics_rows)
    expected_method_counts = {
        "frame_diff": 1,
        "feature_distance": 1,
        "video_autoencoder": 1,
        "cnn_lstm": 1,
        "video_transformer": 1,
        "lewm": len(LEWM_SEEDS) * len(LEWM_AGGREGATIONS),
    }
    if dict(method_counts) != expected_method_counts:
        raise ValueError(f"Unexpected method counts in metrics CSV: {dict(method_counts)}")

    for row in metrics_rows:
        if row["locked_test_materialized"] != "False":
            raise ValueError("Every metrics row must report locked_test_materialized=False.")
        if row["locked_test_scored"] != "False":
            raise ValueError("Every metrics row must report locked_test_scored=False.")
        if int(row["validation_count"]) != len(validation_manifest_rows):
            raise ValueError("Metrics validation_count does not match validation manifest rows.")

    seed_receipts = lewm_artifact_validation.get("seeds", [])
    seed_ids = [int(receipt["seed"]) for receipt in seed_receipts]
    if seed_ids != list(LEWM_SEEDS):
        raise ValueError(f"Expected LeWM seed receipts {LEWM_SEEDS}, found {seed_ids}.")

    score_receipts: dict[str, Any] = {"simple": {}, "learned": {}, "lewm": {}}
    for baseline_name in SIMPLE_BASELINES + LEARNED_BASELINES:
        score_receipts["simple" if baseline_name in SIMPLE_BASELINES else "learned"][
            baseline_name
        ] = {
            "train": _validate_score_file(
                bundle_root / f"{baseline_name}_train_scores.csv",
                expected_count=len(train_manifest_rows),
            ),
            "validation": _validate_score_file(
                bundle_root / f"{baseline_name}_validation_scores.csv",
                expected_count=len(validation_manifest_rows),
            ),
        }
        if baseline_name in LEARNED_BASELINES:
            checkpoint_path = bundle_root / f"{baseline_name}.pt"
            metadata_path = bundle_root / f"{baseline_name}_training_metadata.json"
            if not checkpoint_path.is_file():
                raise FileNotFoundError(f"Missing learned-baseline checkpoint: {checkpoint_path}")
            if not metadata_path.is_file():
                raise FileNotFoundError(f"Missing learned-baseline metadata: {metadata_path}")
            score_receipts["learned"][baseline_name]["checkpoint_sha256"] = sha256_file(
                checkpoint_path
            )
            score_receipts["learned"][baseline_name]["training_metadata_sha256"] = sha256_file(
                metadata_path
            )

    for seed in LEWM_SEEDS:
        seed_key = f"seed{seed}"
        seed_dir = bundle_root / "lewm" / seed_key
        aggregation_receipts: dict[str, Any] = {}
        for aggregation in LEWM_AGGREGATIONS:
            train_score_path = seed_dir / f"lewm_seed{seed}_{aggregation}_train_scores.csv"
            validation_score_path = (
                seed_dir / f"lewm_seed{seed}_{aggregation}_validation_scores.csv"
            )
            train_metadata_path = (
                seed_dir / f"lewm_seed{seed}_{aggregation}_train_scores_metadata.json"
            )
            validation_metadata_path = (
                seed_dir / f"lewm_seed{seed}_{aggregation}_validation_scores_metadata.json"
            )
            if not train_metadata_path.is_file() or not validation_metadata_path.is_file():
                raise FileNotFoundError(
                    f"Missing LeWM score metadata for seed{seed} aggregation {aggregation}."
                )
            aggregation_receipts[aggregation] = {
                "train": _validate_score_file(
                    train_score_path, expected_count=len(train_manifest_rows)
                ),
                "validation": _validate_score_file(
                    validation_score_path,
                    expected_count=len(validation_manifest_rows),
                ),
                "train_metadata_sha256": sha256_file(train_metadata_path),
                "validation_metadata_sha256": sha256_file(validation_metadata_path),
            }
        score_receipts["lewm"][seed_key] = aggregation_receipts

    simple_rows = [row for row in metrics_rows if row["method"] in SIMPLE_BASELINES]
    learned_rows = [row for row in metrics_rows if row["method"] in LEARNED_BASELINES]
    lewm_rows = [row for row in metrics_rows if row["method"] == "lewm"]

    best_simple_row = _best_row(simple_rows)
    best_rows_by_learned_method = _best_rows_by_method(learned_rows)
    best_learned_row = _best_row(learned_rows)
    best_lewm_row = _best_row(lewm_rows)
    best_lewm_aggregation, lewm_seed_aggregate, best_lewm_aggregation_rows = _lewm_seed_aggregate(
        lewm_rows
    )
    top_auroc = max(float(row["auroc"]) for row in metrics_rows)
    top_rows = [row for row in metrics_rows if float(row["auroc"]) == top_auroc]

    tarball_receipt: dict[str, Any] | None = None
    if tarball_path is not None:
        if not tarball_path.is_file():
            raise FileNotFoundError(f"Missing K2 tarball: {tarball_path}")
        tarball_sha256 = sha256_file(tarball_path)
        tarball_receipt = {
            "tarball_path": str(tarball_path),
            "tarball_sha256": tarball_sha256,
        }
        if tarball_sha256_sidecar_path is not None:
            if not tarball_sha256_sidecar_path.is_file():
                raise FileNotFoundError(
                    f"Missing K2 tarball SHA256 sidecar: {tarball_sha256_sidecar_path}"
                )
            sidecar_text = tarball_sha256_sidecar_path.read_text(encoding="utf-8-sig").strip()
            sidecar_sha256 = sidecar_text.split()[0].lower()
            tarball_receipt["sha256_sidecar_path"] = str(tarball_sha256_sidecar_path)
            tarball_receipt["sha256_sidecar_value"] = sidecar_sha256
            tarball_receipt["sha256_match"] = sidecar_sha256 == tarball_sha256.lower()
            if not tarball_receipt["sha256_match"]:
                raise ValueError("K2 tarball SHA256 does not match the sidecar value.")

    intake = {
        "status": "k2_glitchbench_bundle_ingested",
        "bundle_root": str(bundle_root),
        "bundle_root_sha256": {name: sha256_file(bundle_root / name) for name in REQUIRED_FILES},
        "tarball_receipt": tarball_receipt,
        "summary_status": summary["status"],
        "train_normal_clip_count": len(train_manifest_rows),
        "validation_clip_count": len(validation_manifest_rows),
        "bundle_validation": bundle_validation,
        "lewm_artifact_validation": lewm_artifact_validation,
        "best_simple_row": best_simple_row,
        "best_rows_by_learned_method": best_rows_by_learned_method,
        "best_learned_row": best_learned_row,
        "best_lewm_row": best_lewm_row,
        "best_lewm_aggregation": best_lewm_aggregation,
        "best_lewm_aggregation_rows": best_lewm_aggregation_rows,
        "best_lewm_seed_aggregate": lewm_seed_aggregate,
        "top_auroc": top_auroc,
        "top_rows": top_rows,
        "top_method_names": [str(row["method"]) for row in top_rows],
        "score_receipts": score_receipts,
        "claim_boundary": summary["claim_boundary"],
        "results": metrics_rows,
    }

    summary_path = _write_json(output_dir / "k2_glitchbench_intake_summary.json", intake)
    report_lines = [
        "# K2 GlitchBench Intake Report",
        "",
        f"- Status: `{intake['status']}`",
        f"- Summary status: `{summary['status']}`",
        f"- Tarball SHA256 verified: `{str((tarball_receipt or {}).get('sha256_match', True)).lower()}`",
        f"- Support: `{len(train_manifest_rows)}` train-normal clips, `{len(validation_manifest_rows)}` validation clips",
        (
            "- Top AUROC rows: `"
            + ", ".join(intake["top_method_names"])
            + f"` all at `{_float_text(top_auroc)}`"
        ),
        (
            f"- Best LeWM row: seed `{best_lewm_row['seed']}` aggregation "
            f"`{best_lewm_row['aggregation']}` with AUROC `{best_lewm_row['auroc']}`"
        ),
        (
            f"- Best LeWM aggregation-by-seed average: `{best_lewm_aggregation}` AUROC mean "
            f"`{_float_text(float(lewm_seed_aggregate['auroc']['mean']))}` "
            f"(population SD `{_float_text(float(lewm_seed_aggregate['auroc']['std']))}`)"
        ),
        "",
        "## Metric Snapshot",
        "",
        "| Method | Seed | Aggregation | AUROC | AUPRC | F1 | Precision | Recall | Balanced accuracy | FPR@95TPR |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics_rows:
        report_lines.append(
            f"| `{row['method']}` | `{row.get('seed', '')}` | `{row.get('aggregation', '')}` | "
            f"{row['auroc']} | {row['auprc']} | {row['f1']} | {row['precision']} | "
            f"{row['recall']} | {row['balanced_accuracy']} | {row['fpr_at_95_tpr']} |"
        )
    report_lines.extend(
        [
            "",
            "## Boundary Notes",
            "",
            "- This benchmark remains bounded to the exact frozen image-level synthetic-normal K2 split.",
            "- The AUROC 1.0 non-LeWM rows still share thresholded F1 `0.666666666667` and balanced accuracy `0.5` under the train-normal `p95` rule, so ranking and threshold calibration must be discussed separately.",
            "- No temporal-localization, cross-game generalization, SOTA, broad superiority, SIGReg, action-conditioning, or locked-test claim is supported.",
        ]
    )
    report_path = output_dir / "K2_GLITCHBENCH_REPORT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    intake["summary_path"] = str(summary_path)
    intake["summary_sha256"] = sha256_file(summary_path)
    intake["report_path"] = str(report_path)
    intake["report_sha256"] = sha256_file(report_path)
    _write_json(summary_path, intake)
    return intake


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and summarize a downloaded K2 GlitchBench benchmark bundle."
    )
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--tarball-path", type=Path, default=None)
    parser.add_argument("--tarball-sha256-sidecar-path", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = ingest_k2_glitchbench_benchmark(
        bundle_root=args.bundle_root,
        output_dir=args.output_dir,
        tarball_path=args.tarball_path,
        tarball_sha256_sidecar_path=args.tarball_sha256_sidecar_path,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
