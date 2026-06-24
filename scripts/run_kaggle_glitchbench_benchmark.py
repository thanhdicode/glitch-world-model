from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from glitch_detection import (
    cnn_lstm,
    feature_distance,
    frame_diff,
    video_autoencoder,
    video_transformer,
)
from glitch_detection.manifest import ClipRecord, read_manifest, write_manifest
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.r5_xgame_metrics import evaluate_r5_xgame_binary_scores
from glitch_detection.splits import read_grouped_split_csv
from glitch_detection.statistics import bootstrap_metric_ci

ROOT = Path(__file__).resolve().parents[1]


def _load_bundle_validator() -> Any:
    path = ROOT / "scripts" / "validate_glitchbench_bundle.py"
    spec = importlib.util.spec_from_file_location("validate_glitchbench_bundle", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load bundle validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_glitchbench_bundle


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_scores(path: Path, records: list[ClipRecord], scores: dict[str, float]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
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
    return path


def _p95_threshold(values: list[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot compute threshold from an empty score list.")
    position = (len(ordered) - 1) * 0.95
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _rows_for_bootstrap(
    records: list[ClipRecord], split_records: list[Any], scores: dict[str, float]
) -> list[dict[str, Any]]:
    label_by_source = {row.source: row.label for row in split_records}
    return [
        {
            "source": record.source,
            "label": 1 if label_by_source[record.source] == "Buggy" else 0,
            "score": scores[record.clip_id],
        }
        for record in records
    ]


def _evaluate_method(
    *,
    method: str,
    train_records: list[ClipRecord],
    validation_records: list[ClipRecord],
    split_records: list[Any],
    train_scores: dict[str, float],
    validation_scores: dict[str, float],
) -> dict[str, Any]:
    threshold = _p95_threshold([train_scores[record.clip_id] for record in train_records])
    rows = _rows_for_bootstrap(validation_records, split_records, validation_scores)
    metrics = evaluate_r5_xgame_binary_scores(
        [row["label"] for row in rows],
        [row["score"] for row in rows],
        threshold=threshold,
    )
    auroc_ci = bootstrap_metric_ci(rows, "auroc", group_key="source")
    f1_ci = bootstrap_metric_ci(rows, "f1", group_key="source", threshold=threshold)
    return {
        "method": method,
        "threshold": threshold,
        "threshold_source": "train_normal_p95",
        **metrics,
        "auroc_ci_lower": auroc_ci["lower"],
        "auroc_ci_upper": auroc_ci["upper"],
        "f1_ci_lower": f1_ci["lower"],
        "f1_ci_upper": f1_ci["upper"],
        "validation_count": len(validation_records),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def _score_simple_baselines(
    *,
    train_records: list[ClipRecord],
    validation_records: list[ClipRecord],
    split_records: list[Any],
    output_root: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    frame_train = {
        record.clip_id: frame_diff.score_clip(Path(record.clip_dir)) for record in train_records
    }
    frame_validation = {
        record.clip_id: frame_diff.score_clip(Path(record.clip_dir))
        for record in validation_records
    }
    _write_scores(output_root / "frame_diff_train_scores.csv", train_records, frame_train)
    _write_scores(
        output_root / "frame_diff_validation_scores.csv", validation_records, frame_validation
    )
    results.append(
        _evaluate_method(
            method="frame_diff",
            train_records=train_records,
            validation_records=validation_records,
            split_records=split_records,
            train_scores=frame_train,
            validation_scores=frame_validation,
        )
    )

    centroid = feature_distance.fit_centroid(train_records)
    feature_train = feature_distance.score_records_with_centroid(train_records, centroid)
    feature_validation = feature_distance.score_records_with_centroid(validation_records, centroid)
    _write_scores(output_root / "feature_distance_train_scores.csv", train_records, feature_train)
    _write_scores(
        output_root / "feature_distance_validation_scores.csv",
        validation_records,
        feature_validation,
    )
    results.append(
        _evaluate_method(
            method="feature_distance",
            train_records=train_records,
            validation_records=validation_records,
            split_records=split_records,
            train_scores=feature_train,
            validation_scores=feature_validation,
        )
    )
    return results


def _score_learned_baselines(
    *,
    train_records: list[ClipRecord],
    validation_records: list[ClipRecord],
    split_records: list[Any],
    output_root: Path,
    device: str,
) -> list[dict[str, Any]]:
    learned_specs = {
        "video_autoencoder": (
            video_autoencoder,
            video_autoencoder.VideoAutoencoderConfig(device=device if device != "auto" else "cpu"),
            output_root / "video_autoencoder.pt",
        ),
        "cnn_lstm": (
            cnn_lstm,
            cnn_lstm.CNNLSTMConfig(device=device if device != "auto" else "cpu"),
            output_root / "cnn_lstm.pt",
        ),
        "video_transformer": (
            video_transformer,
            video_transformer.VideoTransformerConfig(device=device if device != "auto" else "cpu"),
            output_root / "video_transformer.pt",
        ),
    }
    results: list[dict[str, Any]] = []
    for name, (module, config, checkpoint_path) in learned_specs.items():
        metadata_path = output_root / f"{name}_training_metadata.json"
        train_score_path = output_root / f"{name}_train_scores.csv"
        validation_score_path = output_root / f"{name}_validation_scores.csv"
        module.train_model(train_records, checkpoint_path, metadata_path, config, device=device)
        train_scores = module.score_records_with_checkpoint(
            train_records, checkpoint_path, device=device
        )
        validation_scores = module.score_records_with_checkpoint(
            validation_records, checkpoint_path, device=device
        )
        _write_scores(train_score_path, train_records, train_scores)
        module.write_scores(validation_records, validation_scores, validation_score_path)
        result = _evaluate_method(
            method=name,
            train_records=train_records,
            validation_records=validation_records,
            split_records=split_records,
            train_scores=train_scores,
            validation_scores=validation_scores,
        )
        result["training_config"] = asdict(config)
        results.append(result)
    return results


def run_kaggle_glitchbench_benchmark(
    *,
    manifest_path: Path,
    split_path: Path,
    clips_root: Path,
    output_root: Path,
    device: str,
    dry_run: bool,
    lewm_seed_artifact_root: Path | None = None,
) -> dict[str, Any]:
    validate_glitchbench_bundle = _load_bundle_validator()
    validate_glitchbench_bundle(manifest_path.parent)
    records = rebase_clip_records(read_manifest(manifest_path), clips_root)
    split_records = read_grouped_split_csv(split_path)
    partitions = prepare_neural_partitions(records, split_records)
    plan = {
        "status": "dry_run_ready" if dry_run else "planned",
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "clips_root": str(clips_root),
        "train_normal_clip_count": len(partitions.train_normal),
        "validation_clip_count": len(partitions.validation),
        "device": device,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "lewm_seed_artifact_root": str(lewm_seed_artifact_root)
        if lewm_seed_artifact_root
        else None,
        "claim_boundary": (
            "This K2 runner targets the bounded image-level GlitchBench subset package only. "
            "Synthetic normal clips are used and no temporal-localization claim is supported."
        ),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    write_manifest(output_root / "train_normal_manifest.csv", partitions.train_normal)
    write_manifest(output_root / "validation_manifest.csv", partitions.validation)
    if dry_run:
        _write_json(output_root / "glitchbench_benchmark_summary.json", plan)
        return plan
    if lewm_seed_artifact_root is None:
        raise ValueError(
            "LeWM scoring for K2 requires --lewm-seed-artifact-root with compatible seed42/43/44 "
            "artifacts or a separate K2-specific LeWM training step. The current script can still "
            "train simple and learned baselines, but the LeWM benchmark lane is intentionally "
            "fail-closed until that artifact root is attached."
        )
    simple_results = _score_simple_baselines(
        train_records=partitions.train_normal,
        validation_records=partitions.validation,
        split_records=split_records,
        output_root=output_root,
    )
    learned_results = _score_learned_baselines(
        train_records=partitions.train_normal,
        validation_records=partitions.validation,
        split_records=split_records,
        output_root=output_root,
        device=device,
    )
    summary = {
        **plan,
        "status": "partial_baselines_complete_pending_lewm",
        "simple_results": simple_results,
        "learned_results": learned_results,
    }
    _write_json(output_root / "glitchbench_benchmark_summary.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the bounded K2 GlitchBench benchmark package on Kaggle."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--clips-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--lewm-seed-artifact-root", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = run_kaggle_glitchbench_benchmark(
        manifest_path=args.manifest,
        split_path=args.split,
        clips_root=args.clips_root,
        output_root=args.output_root,
        device=args.device,
        dry_run=args.dry_run,
        lewm_seed_artifact_root=args.lewm_seed_artifact_root,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
