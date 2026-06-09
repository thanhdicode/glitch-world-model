from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from glitch_detection.analysis import write_markdown_table
from glitch_detection.evaluate import read_scores
from glitch_detection.manifest import read_labels
from glitch_detection.splits import read_split_csv
from glitch_detection.video_eval import (
    AGGREGATIONS,
    aggregate_scores_by_source,
    build_video_level_rows,
    calibrate_video_threshold,
    compute_video_level_metrics,
    evaluate_video_with_fixed_threshold,
    source_labels_from_intervals,
    write_json,
    write_video_comparison,
    write_video_rows_csv,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORERS = ["frame_diff", "feature_distance", "mini_latent"]


def require_input_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}. Expected path: {path}")
    return path


def find_input_file(directory: Path, filename: str, description: str) -> Path:
    expected = directory / filename
    if expected.is_file():
        return expected
    candidates = sorted(directory.glob(f"*{filename}"))
    if len(candidates) == 1:
        return candidates[0]
    candidate_text = ", ".join(str(path) for path in candidates) or "none"
    raise FileNotFoundError(
        f"Missing {description}. Expected path: {expected}. Detected candidates: {candidate_text}"
    )


def category_metrics(rows: list[dict[str, Any]], threshold: float) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("category", "unknown"))].append(row)
    return {
        category: compute_video_level_metrics(category_rows, threshold)
        for category, category_rows in sorted(grouped.items())
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate TempGlitch scores at video level.")
    parser.add_argument("--experiment-name", default="tempglitch_phase3b")
    parser.add_argument("--processed-dir", type=Path, default=None)
    parser.add_argument("--input-outputs-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--scorer", action="append", dest="scorers", default=None)
    parser.add_argument("--aggregation", nargs="+", default=list(AGGREGATIONS))
    parser.add_argument("--top-k", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    processed_dir = args.processed_dir or ROOT / "data" / "processed" / args.experiment_name
    input_outputs_dir = args.input_outputs_dir or ROOT / "outputs" / args.experiment_name
    output_dir = args.output_dir or ROOT / "outputs" / f"{args.experiment_name}_video_level"
    scorers = args.scorers or list(DEFAULT_SCORERS)

    split_path = require_input_file(processed_dir / "split.csv", "TempGlitch split metadata")
    validation_labels_path = require_input_file(
        processed_dir / "validation_labels.csv", "validation labels"
    )
    test_labels_path = require_input_file(processed_dir / "test_labels.csv", "test labels")
    split_rows = read_split_csv(split_path)
    validation_sources = {row.source for row in split_rows if row.split == "validation"}
    test_sources = {row.source for row in split_rows if row.split == "test"}
    validation_labels = source_labels_from_intervals(
        read_labels(validation_labels_path), validation_sources
    )
    test_labels = source_labels_from_intervals(read_labels(test_labels_path), test_sources)

    summary_rows: list[dict[str, Any]] = []
    for scorer in scorers:
        validation_scores_path = find_input_file(
            input_outputs_dir, f"{scorer}_val_scores.csv", f"validation scores for {scorer}"
        )
        test_scores_path = find_input_file(
            input_outputs_dir, f"{scorer}_test_scores.csv", f"test scores for {scorer}"
        )
        validation_clip_rows = read_scores(validation_scores_path)
        test_clip_rows = read_scores(test_scores_path)
        for aggregation in args.aggregation:
            validation_rows = build_video_level_rows(
                aggregate_scores_by_source(validation_clip_rows, aggregation, args.top_k),
                validation_labels,
                split_rows,
            )
            test_rows = build_video_level_rows(
                aggregate_scores_by_source(test_clip_rows, aggregation, args.top_k),
                test_labels,
                split_rows,
            )
            prefix = f"{scorer}_{aggregation}"
            write_video_rows_csv(
                validation_rows, output_dir / f"{prefix}_validation_video_scores.csv"
            )
            write_video_rows_csv(test_rows, output_dir / f"{prefix}_test_video_scores.csv")

            calibration = calibrate_video_threshold(validation_rows, aggregation, scorer)
            evaluation = evaluate_video_with_fixed_threshold(test_rows, calibration)
            write_json(calibration, output_dir / f"{prefix}_video_calibration.json")
            write_json(evaluation, output_dir / f"{prefix}_test_video_metrics.json")

            per_category = category_metrics(test_rows, float(calibration["threshold"]))
            write_json(per_category, output_dir / f"{prefix}_category_video_metrics.json")
            write_markdown_table(
                per_category,
                output_dir / f"{prefix}_category_video_metrics.md",
                title=f"{scorer} {aggregation} Category Video Metrics",
            )
            summary_rows.append(evaluation)

    summary = {
        "experiment_name": args.experiment_name,
        "label_limitation": "binary per-video labels; no temporal span claims",
        "threshold_policy": "select on validation videos; apply unchanged to test videos",
        "top_k": args.top_k,
        "results": summary_rows,
    }
    write_json(summary, output_dir / "video_level_summary.json")
    comparison_path = write_video_comparison(summary_rows, output_dir / "video_level_comparison.md")

    print(f"Video-level evaluations: {len(summary_rows)}")
    print(f"Comparison: {comparison_path}")
    for row in summary_rows:
        metrics = row["test_metrics"]
        print(
            f"{row['scorer']}/{row['aggregation']}: AUROC={metrics['auroc']:.3f}, "
            f"F1={metrics['f1']:.3f}, threshold={row['threshold']:.6g}"
        )
    print("Warning: binary per-video labels only; no temporal span claims.")


if __name__ == "__main__":
    main()
