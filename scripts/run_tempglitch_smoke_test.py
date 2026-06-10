from __future__ import annotations

import argparse
from pathlib import Path

from glitch_detection.compare_experiments import build_comparison_rows, write_comparison_markdown
from glitch_detection.dataset_report import build_report, write_markdown_report
from glitch_detection.evaluate import evaluate_scores
from glitch_detection.preprocess import preprocess_input
from glitch_detection.score_clips import run_scorer
from glitch_detection.tempglitch import (
    DEFAULT_CATEGORIES,
    combine_manifests,
    download_tempglitch_subset,
    read_tempglitch_metadata,
    write_tempglitch_full_video_labels,
)

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a TempGlitch subset smoke test.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=ROOT / "data" / "raw" / "tempglitch_smoke",
        help="Raw TempGlitch subset directory.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_smoke",
        help="Processed output directory.",
    )
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=ROOT / "outputs",
        help="Experiment output directory.",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=[DEFAULT_CATEGORIES[0]],
        help="TempGlitch categories to sample from.",
    )
    parser.add_argument(
        "--limit-per-group",
        type=int,
        default=1,
        help="Number of videos to download per category and label group.",
    )
    parser.add_argument("--clip-length", type=int, default=16)
    parser.add_argument("--stride", type=int, default=16)
    parser.add_argument("--size", type=int, default=128)
    parser.add_argument(
        "--scorer",
        action="append",
        dest="scorers",
        default=None,
        help="Repeat to run multiple scorers. Defaults to frame_diff, feature_distance, mini_latent.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    scorers = args.scorers or ["frame_diff", "feature_distance", "mini_latent"]
    samples, metadata_path, _ = download_tempglitch_subset(
        output_dir=args.raw_dir,
        categories=args.categories,
        limit_per_group=args.limit_per_group,
    )

    manifest_paths: list[Path] = []
    for row in read_tempglitch_metadata(metadata_path):
        source = row["source"]
        video_path = args.raw_dir / Path(row["local_video_path"])
        manifest_path = preprocess_input(
            input_path=video_path,
            output_dir=args.processed_dir / source,
            clip_length=args.clip_length,
            stride=args.stride,
            size=args.size,
            fps=None,
        )
        manifest_paths.append(manifest_path)

    combined_manifest_path = combine_manifests(
        manifest_paths=manifest_paths,
        output_path=args.processed_dir / "manifest.csv",
    )
    labels_path = write_tempglitch_full_video_labels(
        metadata_path=metadata_path,
        manifest_path=combined_manifest_path,
        output_path=ROOT / "data" / "raw" / "tempglitch_smoke_labels.csv",
    )

    metric_entries: list[tuple[str, Path]] = []
    for scorer_name in scorers:
        experiment_name = f"tempglitch_smoke_{scorer_name}"
        scores_path = args.outputs_dir / f"{experiment_name}_scores.csv"
        metrics_path = args.outputs_dir / f"{experiment_name}_metrics.json"
        report_path = args.outputs_dir / f"{experiment_name}_report.md"
        run_scorer(
            scorer_name,
            combined_manifest_path,
            labels_path,
            scores_path,
            allow_evaluation_label_fitting=True,
        )
        evaluate_scores(scores_path, labels_path, metrics_path, allow_fit_threshold=True)
        report = build_report(
            name=experiment_name,
            manifest_path=combined_manifest_path,
            labels_path=labels_path,
            scores_path=scores_path,
            metrics_path=metrics_path,
        )
        write_markdown_report(report, report_path)
        metric_entries.append((scorer_name, metrics_path))

    comparison_path = args.outputs_dir / "tempglitch_smoke_comparison.md"
    rows = build_comparison_rows(metric_entries)
    write_comparison_markdown(rows, comparison_path)

    print(f"Downloaded videos: {len(samples)}")
    print(f"Manifest:          {combined_manifest_path}")
    print(f"Labels:            {labels_path}")
    print(f"Comparison:        {comparison_path}")
    for row in rows:
        print(
            f"{row['name']}: F1={row.get('f1'):.3f}, "
            f"AUROC={row.get('auroc'):.3f}, Precision={row.get('precision'):.3f}, "
            f"Recall={row.get('recall'):.3f}"
        )


if __name__ == "__main__":
    main()
