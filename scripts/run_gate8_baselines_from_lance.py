from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from glitch_detection.kaggle_automation import FingerprintBuilder
from glitch_detection.lewm_adapter import sha256_file
from glitch_detection.lewm_lance_eval import (
    BUGGY_DATASET_NAME,
    METADATA_KEYS,
    NORMAL_DATASET_NAME,
    _lance_dataset,
    read_csv_rows,
    runtime_provenance,
    validate_manifest_rows,
    write_csv_rows,
)

BASELINE_SCORE_FIELDS = ("window_id", "frame_diff", "feature_distance")


def baseline_values(pixels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(pixels, dtype=np.float32) / 255.0
    if array.ndim != 5 or array.shape[2] != 3:
        raise ValueError("Baseline pixels must have shape (B,T,3,H,W).")
    grayscale = 0.299 * array[:, :, 0] + 0.587 * array[:, :, 1] + 0.114 * array[:, :, 2]
    frame_diff = np.abs(np.diff(grayscale, axis=1)).mean(axis=(1, 2, 3))
    channel_means = array.mean(axis=(-1, -2))
    channel_stds = array.std(axis=(-1, -2))
    features = np.concatenate([channel_means, channel_stds], axis=2).mean(axis=1)
    return frame_diff, features


def fit_feature_centroid(feature_batches: Iterable[np.ndarray]) -> np.ndarray:
    total: np.ndarray | None = None
    count = 0
    for batch in feature_batches:
        values = np.asarray(batch, dtype=np.float64)
        if values.ndim != 2 or not len(values):
            continue
        total = values.sum(axis=0) if total is None else total + values.sum(axis=0)
        count += len(values)
    if total is None or count == 0:
        raise ValueError("Feature-distance centroid requires train-normal windows.")
    return (total / count).astype(np.float32)


def validate_baseline_alignment(
    manifest_rows: Sequence[dict[str, str]],
    score_rows: Sequence[dict[str, str]],
) -> None:
    if [row["window_id"] for row in manifest_rows] != [row["window_id"] for row in score_rows]:
        raise ValueError("Baseline rows must match the canonical manifest in exact ordered form.")
    for row in score_rows:
        for field in ("frame_diff", "feature_distance"):
            if not math.isfinite(float(row[field])):
                raise ValueError(f"Baseline score field {field} must be finite.")


def _git_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _loader(dataset: Any, *, batch_size: int) -> Any:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("Gate 8 Lance baselines require the isolated LeWM runtime.") from exc
    return torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)


def _fit_train_centroid(train_lance: Path, *, batch_size: int) -> np.ndarray:
    dataset = _lance_dataset(train_lance, include_metadata=False)

    def batches() -> Iterable[np.ndarray]:
        for batch in _loader(dataset, batch_size=batch_size):
            _, features = baseline_values(batch["pixels"].numpy())
            yield features

    return fit_feature_centroid(batches())


def _batch_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _validate_batch_metadata(
    batch: dict[str, Any],
    expected_rows: Sequence[dict[str, str]],
) -> None:
    for key in METADATA_KEYS:
        actual = _batch_strings(batch[key])
        expected = [row[key] for row in expected_rows]
        if actual != expected:
            raise ValueError(f"Lance metadata mismatch for canonical field {key}.")


def _score_target(
    dataset_path: Path,
    manifest_rows: Sequence[dict[str, str]],
    centroid: np.ndarray,
    *,
    batch_size: int,
) -> list[dict[str, str]]:
    dataset = _lance_dataset(dataset_path, include_metadata=True)
    if len(dataset) != len(manifest_rows):
        raise ValueError("Baseline Lance window count does not match canonical manifest.")
    output: list[dict[str, str]] = []
    offset = 0
    for batch in _loader(dataset, batch_size=batch_size):
        batch_count = len(batch["pixels"])
        expected = manifest_rows[offset : offset + batch_count]
        _validate_batch_metadata(batch, expected)
        frame_diff, features = baseline_values(batch["pixels"].numpy())
        feature_distance = np.linalg.norm(features - centroid.reshape(1, -1), axis=1)
        for index in range(batch_count):
            output.append(
                {
                    "window_id": expected[index]["window_id"],
                    "frame_diff": f"{float(frame_diff[index]):.12g}",
                    "feature_distance": f"{float(feature_distance[index]):.12g}",
                }
            )
        offset += batch_count
    return output


def _validate_fingerprints(
    manifest_rows: Sequence[dict[str, str]],
    normal_lance: Path,
    buggy_lance: Path,
) -> dict[str, str]:
    actual = {
        NORMAL_DATASET_NAME: FingerprintBuilder.inventory_sha256(normal_lance),
        BUGGY_DATASET_NAME: FingerprintBuilder.inventory_sha256(buggy_lance),
    }
    for dataset_name, fingerprint in actual.items():
        expected = {
            row["dataset_fingerprint"]
            for row in manifest_rows
            if row["dataset_name"] == dataset_name
        }
        if expected != {fingerprint}:
            raise ValueError(f"Canonical manifest fingerprint mismatch for {dataset_name}.")
    return actual


def run_gate8_baselines(
    *,
    manifest_path: Path,
    train_lance: Path,
    normal_lance: Path,
    buggy_lance: Path,
    output_dir: Path,
    batch_size: int = 64,
) -> dict[str, Any]:
    manifest_rows = read_csv_rows(manifest_path)
    validate_manifest_rows(manifest_rows)
    fingerprints = _validate_fingerprints(manifest_rows, normal_lance, buggy_lance)
    centroid = _fit_train_centroid(train_lance, batch_size=batch_size)
    normal_rows = [row for row in manifest_rows if row["dataset_name"] == NORMAL_DATASET_NAME]
    buggy_rows = [row for row in manifest_rows if row["dataset_name"] == BUGGY_DATASET_NAME]
    score_rows = [
        *_score_target(normal_lance, normal_rows, centroid, batch_size=batch_size),
        *_score_target(buggy_lance, buggy_rows, centroid, batch_size=batch_size),
    ]
    validate_baseline_alignment(manifest_rows, score_rows)
    scores_path = write_csv_rows(
        output_dir / "baseline_scores.csv",
        score_rows,
        BASELINE_SCORE_FIELDS,
    )
    metadata = {
        "status": "gate8_scored",
        "protocol": "same_canonical_nonlocked_window_manifest",
        "window_count": len(score_rows),
        "manifest_sha256": sha256_file(manifest_path),
        "scores_sha256": sha256_file(scores_path),
        "train_dataset_fingerprint": FingerprintBuilder.inventory_sha256(train_lance),
        "evaluation_dataset_fingerprints": fingerprints,
        "feature_centroid": centroid.astype(float).tolist(),
        "feature_definition": "mean over four frames of RGB channel means and population stds",
        "frame_diff_definition": "mean adjacent-frame absolute grayscale difference",
        "batch_size": batch_size,
        "git_sha": _git_sha(),
        "environment": runtime_provenance(include_lewm=True),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    metadata_path = output_dir / "gate8_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadata_path"] = str(metadata_path)
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score Gate 8 baselines on the exact Gate 7 Lance window manifest."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--train-lance", required=True, type=Path)
    parser.add_argument("--normal-lance", required=True, type=Path)
    parser.add_argument("--buggy-lance", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    for path in (args.manifest, args.train_lance, args.normal_lance, args.buggy_lance):
        if not path.exists():
            raise FileNotFoundError(f"Missing Gate 8 input: {path}")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "manifest": str(args.manifest),
                    "output_dir": str(args.output_dir),
                    "batch_size": args.batch_size,
                    "locked_test_materialized": False,
                    "locked_test_scored": False,
                },
                indent=2,
            )
        )
        return
    print(
        json.dumps(
            run_gate8_baselines(
                manifest_path=args.manifest,
                train_lance=args.train_lance,
                normal_lance=args.normal_lance,
                buggy_lance=args.buggy_lance,
                output_dir=args.output_dir,
                batch_size=args.batch_size,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
