from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from glitch_detection import (
    cnn_lstm,
    feature_distance,
    frame_diff,
    video_autoencoder,
    video_transformer,
)
from glitch_detection.gate6_data import sha256_file
from glitch_detection.lewm_surprise import score_manifest
from glitch_detection.manifest import ClipRecord, read_manifest, write_manifest
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.r5_xgame_metrics import evaluate_r5_xgame_binary_scores
from glitch_detection.splits import read_grouped_split_csv
from glitch_detection.statistics import bootstrap_metric_ci

ROOT = Path(__file__).resolve().parents[1]
LEWM_SEEDS = (42, 43, 44)
LEWM_AGGREGATIONS = ("mean", "max")


@dataclass(frozen=True)
class LeWMSeedArtifact:
    seed: int
    seed_root: Path
    checkpoint_path: Path
    config_path: Path
    expected_sha256: str | None
    checkpoint_sha256_path: Path | None
    training_metadata_path: Path | None


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


def _read_scores_csv(path: Path) -> dict[str, float]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {row["clip_id"]: float(row["score"]) for row in csv.DictReader(handle)}


def _write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    fieldnames = [
        "method",
        "seed",
        "aggregation",
        "threshold",
        "threshold_source",
        "auroc",
        "auprc",
        "f1",
        "precision",
        "recall",
        "balanced_accuracy",
        "fpr_at_95_tpr",
        "auroc_ci_lower",
        "auroc_ci_upper",
        "f1_ci_lower",
        "f1_ci_upper",
        "validation_count",
        "locked_test_materialized",
        "locked_test_scored",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
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


def _read_sha256_sidecar(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Empty SHA256 sidecar: {path}")
    return text.split()[0]


def _validate_lewm_seed_artifact_root(root: Path) -> list[LeWMSeedArtifact]:
    if not root.is_dir():
        raise FileNotFoundError(f"LeWM seed artifact root does not exist: {root}")
    artifacts: list[LeWMSeedArtifact] = []
    for seed in LEWM_SEEDS:
        seed_root = root / f"seed{seed}"
        if not seed_root.is_dir():
            raise FileNotFoundError(
                f"LeWM seed artifact root must contain seed{seed}/ for K2: {root}"
            )
        checkpoint_path = seed_root / "best_weights.pt"
        config_path = seed_root / "config.json"
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"Missing K2 LeWM checkpoint for seed{seed}: {checkpoint_path}")
        if not config_path.is_file():
            raise FileNotFoundError(f"Missing K2 LeWM config for seed{seed}: {config_path}")
        checkpoint_sha256_path = seed_root / "checkpoint.sha256"
        expected_sha256 = None
        if checkpoint_sha256_path.is_file():
            expected_sha256 = _read_sha256_sidecar(checkpoint_sha256_path)
            actual_sha256 = sha256_file(checkpoint_path)
            if actual_sha256 != expected_sha256:
                raise ValueError(
                    f"K2 LeWM checkpoint SHA256 mismatch for seed{seed}: "
                    f"{checkpoint_path.name} != checkpoint.sha256"
                )
        training_metadata_path = seed_root / "training_metadata.json"
        artifacts.append(
            LeWMSeedArtifact(
                seed=seed,
                seed_root=seed_root,
                checkpoint_path=checkpoint_path,
                config_path=config_path,
                expected_sha256=expected_sha256,
                checkpoint_sha256_path=checkpoint_sha256_path
                if checkpoint_sha256_path.is_file()
                else None,
                training_metadata_path=training_metadata_path
                if training_metadata_path.is_file()
                else None,
            )
        )
    return artifacts


def _git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _score_lewm_manifest(
    *,
    manifest_path: Path,
    output_path: Path,
    artifact: LeWMSeedArtifact,
    aggregation: str,
    device: str,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    score_manifest(
        manifest_path,
        None,
        output_path,
        checkpoint=artifact.checkpoint_path,
        config=artifact.config_path,
        action_mode="zero_action",
        device=device,
        aggregation=aggregation,
        expected_sha256=artifact.expected_sha256,
    )
    records = read_manifest(manifest_path)
    metadata = {
        "scorer": "lewm_surprise",
        "seed": artifact.seed,
        "aggregation": aggregation,
        "checkpoint_path": str(artifact.checkpoint_path),
        "config_path": str(artifact.config_path),
        "checkpoint_sha256": sha256_file(artifact.checkpoint_path),
        "config_sha256": sha256_file(artifact.config_path),
        "manifest_sha256": sha256_file(manifest_path),
        "scores_sha256": sha256_file(output_path),
        "action_mode": "zero_action",
        "device": device,
        "clip_count": len(records),
        "finite_score_count": len(records),
        "locked_test_scored": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
    }
    if artifact.checkpoint_sha256_path is not None:
        metadata["checkpoint_sha256_sidecar_path"] = str(artifact.checkpoint_sha256_path)
    if artifact.training_metadata_path is not None:
        metadata["training_metadata_path"] = str(artifact.training_metadata_path)
    metadata_path = output_path.with_name(f"{output_path.stem}_metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata_path


def _score_lewm(
    *,
    train_manifest_path: Path,
    validation_manifest_path: Path,
    train_records: list[ClipRecord],
    validation_records: list[ClipRecord],
    split_records: list[Any],
    output_root: Path,
    device: str,
    lewm_seed_artifact_root: Path,
    lewm_aggregations: tuple[str, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    artifacts = _validate_lewm_seed_artifact_root(lewm_seed_artifact_root)
    results: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "artifact_root": str(lewm_seed_artifact_root),
        "seeds": [],
    }
    lewm_root = output_root / "lewm"
    for artifact in artifacts:
        seed_dir = lewm_root / f"seed{artifact.seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        actual_checkpoint_sha256 = sha256_file(artifact.checkpoint_path)
        seed_receipt = {
            "seed": artifact.seed,
            "seed_root": str(artifact.seed_root),
            "checkpoint_path": str(artifact.checkpoint_path),
            "config_path": str(artifact.config_path),
            "checkpoint_sha256": actual_checkpoint_sha256,
            "config_sha256": sha256_file(artifact.config_path),
            "aggregations": list(lewm_aggregations),
        }
        if artifact.expected_sha256 is not None:
            seed_receipt["checkpoint_sha256_sidecar"] = artifact.expected_sha256
        receipt["seeds"].append(seed_receipt)
        for aggregation in lewm_aggregations:
            train_score_path = seed_dir / f"lewm_seed{artifact.seed}_{aggregation}_train_scores.csv"
            validation_score_path = (
                seed_dir / f"lewm_seed{artifact.seed}_{aggregation}_validation_scores.csv"
            )
            _score_lewm_manifest(
                manifest_path=train_manifest_path,
                output_path=train_score_path,
                artifact=artifact,
                aggregation=aggregation,
                device=device,
            )
            _score_lewm_manifest(
                manifest_path=validation_manifest_path,
                output_path=validation_score_path,
                artifact=artifact,
                aggregation=aggregation,
                device=device,
            )
            result = _evaluate_method(
                method="lewm",
                train_records=train_records,
                validation_records=validation_records,
                split_records=split_records,
                train_scores=_read_scores_csv(train_score_path),
                validation_scores=_read_scores_csv(validation_score_path),
            )
            result["seed"] = artifact.seed
            result["aggregation"] = aggregation
            result["checkpoint_sha256"] = actual_checkpoint_sha256
            results.append(result)
    return results, receipt


def _claim_boundary_text() -> str:
    return (
        "This K2 runner targets the bounded image-level GlitchBench subset package only. "
        "Synthetic normal clips are used and no temporal-localization, cross-game generalization, "
        "broad superiority, or SOTA claim is supported."
    )


def run_kaggle_glitchbench_benchmark(
    *,
    manifest_path: Path,
    split_path: Path,
    clips_root: Path,
    output_root: Path,
    device: str,
    dry_run: bool,
    lewm_seed_artifact_root: Path | None = None,
    baseline_only: bool = False,
    lewm_aggregations: tuple[str, ...] = LEWM_AGGREGATIONS,
) -> dict[str, Any]:
    validate_glitchbench_bundle = _load_bundle_validator()
    bundle_validation = validate_glitchbench_bundle(manifest_path.parent)
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
        "baseline_only": baseline_only,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "lewm_seed_artifact_root": str(lewm_seed_artifact_root)
        if lewm_seed_artifact_root
        else None,
        "lewm_aggregations": list(lewm_aggregations),
        "bundle_validation": bundle_validation,
        "claim_boundary": _claim_boundary_text(),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    train_manifest_path = output_root / "train_normal_manifest.csv"
    validation_manifest_path = output_root / "validation_manifest.csv"
    write_manifest(train_manifest_path, partitions.train_normal)
    write_manifest(validation_manifest_path, partitions.validation)
    _write_json(output_root / "bundle_validation.json", bundle_validation)
    if dry_run:
        _write_json(output_root / "glitchbench_benchmark_summary.json", plan)
        return plan
    if lewm_seed_artifact_root is None and not baseline_only:
        raise ValueError(
            "Scientific K2 requires --lewm-seed-artifact-root with compatible seed42/43/44 "
            "artifacts. Use --baseline-only only for engineering smoke tests; it cannot support "
            "LeWM-vs-baseline claims."
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
        "simple_results": simple_results,
        "learned_results": learned_results,
    }
    metrics_rows = [*simple_results, *learned_results]
    if baseline_only:
        summary["status"] = "baseline_only_complete_no_lewm"
        summary["lewm_results"] = []
        summary["lewm_artifact_validation"] = None
    else:
        lewm_results, artifact_receipt = _score_lewm(
            train_manifest_path=train_manifest_path,
            validation_manifest_path=validation_manifest_path,
            train_records=partitions.train_normal,
            validation_records=partitions.validation,
            split_records=split_records,
            output_root=output_root,
            device=device,
            lewm_seed_artifact_root=lewm_seed_artifact_root,
            lewm_aggregations=lewm_aggregations,
        )
        summary["status"] = "k2_complete_lewm_and_baselines"
        summary["lewm_results"] = lewm_results
        summary["lewm_artifact_validation"] = artifact_receipt
        metrics_rows.extend(lewm_results)
        _write_json(output_root / "lewm_artifact_validation.json", artifact_receipt)
    _write_metrics_csv(output_root / "glitchbench_benchmark_metrics.csv", metrics_rows)
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
    parser.add_argument(
        "--lewm-aggregations",
        nargs="+",
        choices=list(LEWM_AGGREGATIONS),
        default=list(LEWM_AGGREGATIONS),
    )
    parser.add_argument("--baseline-only", action="store_true")
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
        baseline_only=args.baseline_only,
        lewm_aggregations=tuple(args.lewm_aggregations),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
