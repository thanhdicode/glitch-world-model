from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from glitch_detection import feature_distance, frame_diff, mini_latent
from glitch_detection.calibration import calibrate_threshold, evaluate_with_fixed_threshold
from glitch_detection.manifest import ClipRecord, clip_has_glitch, read_labels, read_manifest
from glitch_detection.preprocess import extract_video_frames, preprocess_frames
from glitch_detection.splits import (
    SplitRecord,
    assign_video_splits,
    filter_labels_by_sources,
    filter_manifest_by_sources,
    read_split_csv,
    sources_for_split,
    write_split_csv,
)
from glitch_detection.tempglitch import (
    DATASET_PAGE_URL,
    DEFAULT_CATEGORIES,
    combine_manifests,
    download_tempglitch_subset,
    read_tempglitch_metadata,
    write_tempglitch_full_video_labels,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORERS = ["frame_diff", "feature_distance", "mini_latent"]


def write_scores_csv(
    records: list[ClipRecord], scores: dict[str, float], output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "score": f"{scores[record.clip_id]:.8f}",
                }
            )
    return output_path


def preprocess_tempglitch_videos(
    raw_dir: Path,
    processed_dir: Path,
    metadata_path: Path,
    clip_length: int,
    stride: int,
    size: int,
) -> Path:
    manifest_paths: list[Path] = []
    for row in read_tempglitch_metadata(metadata_path):
        source = row["source"]
        video_path = raw_dir / Path(row["local_video_path"])
        source_dir = processed_dir / source
        frames_dir, fps = extract_video_frames(
            video_path, source_dir / "frames" / source, size=size
        )
        manifest_paths.append(
            preprocess_frames(
                input_path=frames_dir,
                output_dir=source_dir,
                clip_length=clip_length,
                stride=stride,
                size=size,
                fps=fps,
            )
        )
    return combine_manifests(manifest_paths, processed_dir / "manifest.csv")


def normal_train_records(manifest_path: Path, split_records: list[SplitRecord]) -> list[ClipRecord]:
    normal_sources = {
        record.source
        for record in split_records
        if record.split == "train" and record.label == "Normal"
    }
    return [record for record in read_manifest(manifest_path) if record.source in normal_sources]


def score_validation_and_test(
    scorer_name: str,
    train_manifest_path: Path,
    validation_manifest_path: Path,
    test_manifest_path: Path,
    split_records: list[SplitRecord],
    outputs_dir: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    validation_scores_path = outputs_dir / f"{scorer_name}_val_scores.csv"
    test_scores_path = outputs_dir / f"{scorer_name}_test_scores.csv"
    validation_records = read_manifest(validation_manifest_path)
    test_records = read_manifest(test_manifest_path)

    fit_metadata: dict[str, Any] = {"fit_split": "none", "fit_normal_clip_count": 0}
    if scorer_name == "frame_diff":
        frame_diff.score_manifest(validation_manifest_path, validation_scores_path)
        frame_diff.score_manifest(test_manifest_path, test_scores_path)
    elif scorer_name == "feature_distance":
        train_records = normal_train_records(train_manifest_path, split_records)
        centroid = feature_distance.fit_centroid(train_records)
        write_scores_csv(
            validation_records,
            feature_distance.score_records_with_centroid(validation_records, centroid),
            validation_scores_path,
        )
        write_scores_csv(
            test_records,
            feature_distance.score_records_with_centroid(test_records, centroid),
            test_scores_path,
        )
        fit_metadata = {"fit_split": "train", "fit_normal_clip_count": len(train_records)}
    elif scorer_name == "mini_latent":
        train_records = normal_train_records(train_manifest_path, split_records)
        model = mini_latent.fit_model(train_records)
        write_scores_csv(
            validation_records,
            mini_latent.score_records_with_model(validation_records, model),
            validation_scores_path,
        )
        write_scores_csv(
            test_records,
            mini_latent.score_records_with_model(test_records, model),
            test_scores_path,
        )
        fit_metadata = {"fit_split": "train", "fit_normal_clip_count": len(train_records)}
    else:
        raise ValueError(f"Unsupported split-aware scorer: {scorer_name}")

    return validation_scores_path, test_scores_path, fit_metadata


def write_comparison(results: list[dict[str, Any]], output_path: Path) -> Path:
    lines = [
        "# Phase 3/4 TempGlitch Comparison",
        "",
        "| Scorer | Val threshold | Test precision | Test recall | Test F1 | Test AUROC |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| {result['scorer']} | {result['validation_threshold']:.6g} | "
            f"{result['test_metrics']['precision']:.6g} | "
            f"{result['test_metrics']['recall']:.6g} | "
            f"{result['test_metrics']['f1']:.6g} | "
            f"{result['test_metrics']['auroc']:.6g} |"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def positive_clip_counts(
    manifest_path: Path,
    labels_path: Path,
    split_records: list[SplitRecord],
) -> dict[str, int]:
    labels = read_labels(labels_path)
    records = read_manifest(manifest_path)
    return {
        split: sum(
            int(clip_has_glitch(record.source, record.start_frame, record.end_frame, labels))
            for record in records
            if record.source in sources_for_split(split_records, split)
        )
        for split in ["train", "validation", "test"]
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run leakage-aware TempGlitch split experiments.")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw" / "tempglitch_phase3")
    parser.add_argument(
        "--processed-dir", type=Path, default=ROOT / "data" / "processed" / "tempglitch_phase3"
    )
    parser.add_argument("--outputs-dir", type=Path, default=ROOT / "outputs" / "tempglitch_phase3")
    parser.add_argument("--categories", nargs="+", default=list(DEFAULT_CATEGORIES))
    parser.add_argument("--limit-per-group", type=int, default=3)
    parser.add_argument("--clip-length", type=int, default=16)
    parser.add_argument("--stride", type=int, default=16)
    parser.add_argument("--size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scorer", action="append", dest="scorers", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    scorers = args.scorers or list(DEFAULT_SCORERS)
    if args.limit_per_group < 3:
        raise SystemExit(
            "Leakage-aware validation calibration requires at least 3 videos per category/label."
        )

    samples, metadata_path, _ = download_tempglitch_subset(
        output_dir=args.raw_dir,
        categories=args.categories,
        limit_per_group=args.limit_per_group,
    )
    manifest_path = preprocess_tempglitch_videos(
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        metadata_path=metadata_path,
        clip_length=args.clip_length,
        stride=args.stride,
        size=args.size,
    )
    labels_path = write_tempglitch_full_video_labels(
        metadata_path=metadata_path,
        manifest_path=manifest_path,
        output_path=args.processed_dir / "labels.csv",
    )
    split_path = write_split_csv(
        args.processed_dir / "split.csv",
        assign_video_splits(read_tempglitch_metadata(metadata_path), seed=args.seed),
    )
    split_records = read_split_csv(split_path)

    split_manifest_paths: dict[str, Path] = {}
    split_label_paths: dict[str, Path] = {}
    for split in ["train", "validation", "test"]:
        sources = sources_for_split(split_records, split)
        split_manifest_paths[split] = filter_manifest_by_sources(
            manifest_path,
            sources,
            args.processed_dir / f"{split}_manifest.csv",
        )
        split_label_paths[split] = filter_labels_by_sources(
            labels_path,
            sources,
            args.processed_dir / f"{split}_labels.csv",
        )

    results: list[dict[str, Any]] = []
    for scorer_name in scorers:
        validation_scores_path, test_scores_path, fit_metadata = score_validation_and_test(
            scorer_name=scorer_name,
            train_manifest_path=split_manifest_paths["train"],
            validation_manifest_path=split_manifest_paths["validation"],
            test_manifest_path=split_manifest_paths["test"],
            split_records=split_records,
            outputs_dir=args.outputs_dir,
        )
        calibration_path = args.outputs_dir / f"{scorer_name}_calibration.json"
        calibration = calibrate_threshold(
            validation_scores_path,
            split_label_paths["validation"],
            calibration_path,
        )
        test_metrics_path = args.outputs_dir / f"{scorer_name}_test_metrics.json"
        test_metrics = evaluate_with_fixed_threshold(
            test_scores_path,
            split_label_paths["test"],
            calibration_path,
            test_metrics_path,
        )
        results.append(
            {
                "scorer": scorer_name,
                "validation_threshold": calibration["threshold"],
                "calibration_path": str(calibration_path),
                "test_metrics_path": str(test_metrics_path),
                "fit": fit_metadata,
                "test_metrics": test_metrics,
            }
        )

    split_counts = Counter(record.split for record in split_records)
    group_counts = Counter(
        (record.category, record.label, record.split) for record in split_records
    )
    summary = {
        "dataset_url": DATASET_PAGE_URL,
        "dataset_revision": samples[0].dataset_revision if samples else None,
        "categories": args.categories,
        "limit_per_group": args.limit_per_group,
        "video_count": len(samples),
        "clip_count": len(read_manifest(manifest_path)),
        "split_counts": dict(split_counts),
        "group_split_counts": {
            f"{category}/{label}/{split}": count
            for (category, label, split), count in sorted(group_counts.items())
        },
        "positive_clip_counts": positive_clip_counts(manifest_path, labels_path, split_records),
        "clip_length": args.clip_length,
        "stride": args.stride,
        "size": args.size,
        "seed": args.seed,
        "label_limitation": "binary per-video labels; no temporal span claims",
        "results": results,
    }
    args.outputs_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.outputs_dir / "phase3_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    comparison_path = write_comparison(results, args.outputs_dir / "phase3_comparison.md")

    print(f"Videos: {summary['video_count']}")
    print(f"Clips: {summary['clip_count']}")
    print(f"Split counts: {summary['split_counts']}")
    print(f"Group split counts: {summary['group_split_counts']}")
    print(f"Positive clips by split: {summary['positive_clip_counts']}")
    for result in results:
        metrics = result["test_metrics"]
        print(
            f"{result['scorer']}: validation threshold={result['validation_threshold']:.6g}, "
            f"test AUROC={metrics['auroc']:.3f}, F1={metrics['f1']:.3f}, "
            f"precision={metrics['precision']:.3f}, recall={metrics['recall']:.3f}"
        )
    print(f"Comparison: {comparison_path}")
    print(f"Summary: {summary_path}")
    print("Warning: binary per-video labels only; no temporal span claims.")


if __name__ == "__main__":
    main()
