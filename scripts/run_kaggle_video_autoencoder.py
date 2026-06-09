from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from glitch_detection.manifest import read_manifest, write_manifest
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.splits import GroupedSplitRecord
from glitch_detection.video_autoencoder import (
    VideoAutoencoderConfig,
    score_records_with_checkpoint,
    train_model,
    write_scores,
)

ROOT = Path(__file__).resolve().parents[1]


def _require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")
    return path


def _read_grouped_split(path: Path) -> list[GroupedSplitRecord]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {"source", "category", "label", "split", "pair_id_heuristic"}
    fields = set(rows[0]) if rows else set()
    missing = sorted(required - fields)
    if missing:
        raise ValueError(f"Grouped split is missing fields: {', '.join(missing)}")
    return [
        GroupedSplitRecord(
            source=row["source"],
            category=row["category"],
            label=row["label"],
            split=row["split"],
            pair_id_heuristic=row["pair_id_heuristic"],
        )
        for row in rows
    ]


def _validate_clip_dirs(records: list[Any]) -> None:
    missing = [record.clip_dir for record in records if not Path(record.clip_dir).is_dir()]
    if missing:
        preview = ", ".join(missing[:3])
        raise FileNotFoundError(
            f"{len(missing)} selected clip directories do not exist. First missing: {preview}"
        )


def _write_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def run_kaggle_video_autoencoder(
    manifest_path: Path,
    split_path: Path,
    output_root: Path,
    dry_run: bool,
    clips_root: Path | None = None,
    config: VideoAutoencoderConfig | None = None,
    device: str = "auto",
) -> dict[str, Any]:
    _require_file(manifest_path, "combined manifest")
    _require_file(split_path, "grouped split")
    records = read_manifest(manifest_path)
    if clips_root is not None:
        records = rebase_clip_records(records, clips_root)
    split_records = _read_grouped_split(split_path)
    partitions = prepare_neural_partitions(records, split_records)
    _validate_clip_dirs([*partitions.train_normal, *partitions.validation])
    config = config or VideoAutoencoderConfig()

    output_root.mkdir(parents=True, exist_ok=True)
    train_manifest_path = output_root / "train_normal_manifest.csv"
    validation_manifest_path = output_root / "validation_manifest.csv"
    write_manifest(train_manifest_path, partitions.train_normal)
    write_manifest(validation_manifest_path, partitions.validation)
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "training pending",
        "protocol": "pair-suspect grouped; train-normal fit; validation scoring only",
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "clips_root": str(clips_root) if clips_root is not None else None,
        "config": asdict(config),
        "train_normal_clip_count": len(partitions.train_normal),
        "train_normal_source_count": len({row.source for row in partitions.train_normal}),
        "validation_clip_count": len(partitions.validation),
        "validation_source_count": len({row.source for row in partitions.validation}),
        "test_clip_count": len(partitions.test),
        "test_source_count": len({row.source for row in partitions.test}),
        "test_materialized": False,
        "test_scored": False,
        "leakage_audit": partitions.audit,
        "train_normal_manifest_path": str(train_manifest_path),
        "validation_manifest_path": str(validation_manifest_path),
    }
    audit_path = output_root / "protocol_audit.json"
    if dry_run:
        _write_json(summary, audit_path)
        return summary

    checkpoint_path = output_root / "video_autoencoder.pt"
    training_metadata_path = output_root / "training_metadata.json"
    validation_scores_path = output_root / "validation_scores.csv"
    training_metadata = train_model(
        partitions.train_normal,
        checkpoint_path,
        training_metadata_path,
        config,
        device=device,
    )
    validation_scores = score_records_with_checkpoint(
        partitions.validation,
        checkpoint_path,
        device=device,
    )
    write_scores(partitions.validation, validation_scores, validation_scores_path)
    summary.update(
        {
            "status": "training and validation scoring complete",
            "checkpoint_path": str(checkpoint_path),
            "training_metadata_path": str(training_metadata_path),
            "validation_scores_path": str(validation_scores_path),
            "training_metadata": training_metadata,
        }
    )
    _write_json(summary, audit_path)
    _write_json(summary, output_root / "phase6e_summary.json")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train a Conv3D autoencoder on train-normal clips and score validation."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_phase3b" / "manifest.csv",
    )
    parser.add_argument(
        "--split",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6d" / "seed_42" / "split.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6e" / "seed_42",
    )
    parser.add_argument(
        "--clips-root",
        type=Path,
        default=None,
        help="Rebase clip_dir values to <clips-root>/<source>/clips/<clip_id> for Kaggle.",
    )
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--clip-length", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = VideoAutoencoderConfig(
        image_size=args.image_size,
        clip_length=args.clip_length,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        seed=args.seed,
        num_workers=args.num_workers,
    )
    summary = run_kaggle_video_autoencoder(
        manifest_path=args.manifest,
        split_path=args.split,
        output_root=args.output_root,
        dry_run=args.dry_run,
        clips_root=args.clips_root,
        config=config,
        device=args.device,
    )
    print(f"Phase 6E status: {summary['status']}")
    print(f"Train-normal clips: {summary['train_normal_clip_count']}")
    print(f"Validation clips: {summary['validation_clip_count']}")
    print(f"Test clips scored: {summary['test_scored']}")
    print(f"Protocol audit: {args.output_root / 'protocol_audit.json'}")


if __name__ == "__main__":
    main()
