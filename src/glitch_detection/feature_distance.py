from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image

from .manifest import ClipRecord, clip_has_glitch, read_labels, read_manifest
from .preprocess import IMAGE_EXTENSIONS


def list_clip_frames(clip_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in clip_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def clip_feature(clip_dir: Path) -> np.ndarray:
    frames = list_clip_frames(clip_dir)
    if not frames:
        return np.zeros(6, dtype=np.float32)

    per_frame_features: list[np.ndarray] = []
    for frame_path in frames:
        with Image.open(frame_path) as image:
            array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
        means = array.mean(axis=(0, 1))
        stds = array.std(axis=(0, 1))
        per_frame_features.append(np.concatenate([means, stds]))
    return np.mean(np.stack(per_frame_features), axis=0)


def fit_centroid(records: list[ClipRecord]) -> np.ndarray:
    if not records:
        raise ValueError("Need at least one training record to fit feature centroid.")
    return np.mean(np.stack([clip_feature(Path(record.clip_dir)) for record in records]), axis=0)


def score_records_with_centroid(
    records: list[ClipRecord],
    centroid: np.ndarray,
) -> dict[str, float]:
    return {
        record.clip_id: float(np.linalg.norm(clip_feature(Path(record.clip_dir)) - centroid))
        for record in records
    }


def score_records(records: list[ClipRecord], labels: list[int]) -> dict[str, float]:
    normal_records = [record for record, label in zip(records, labels) if label == 0]
    centroid = fit_centroid(normal_records or records)
    return score_records_with_centroid(records, centroid)


def score_manifest(manifest_path: Path, labels_path: Path | None, output_path: Path) -> Path:
    records = read_manifest(manifest_path)
    intervals = read_labels(labels_path)
    labels = [
        int(clip_has_glitch(record.source, record.start_frame, record.end_frame, intervals))
        for record in records
    ]
    scores = score_records(records, labels)

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score clips by distance from normal visual features."
    )
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument(
        "--labels", type=Path, default=None, help="Optional labels CSV for normal centroid fitting."
    )
    parser.add_argument("--output", required=True, type=Path, help="Output scores.csv path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_path = score_manifest(args.manifest, args.labels, args.output)
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()
