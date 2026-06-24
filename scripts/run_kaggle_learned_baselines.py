from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from glitch_detection import cnn_lstm, video_autoencoder, video_transformer
from glitch_detection.gate6_data import sha256_file
from glitch_detection.manifest import read_manifest, write_manifest
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.splits import read_grouped_split_csv

ROOT = Path(__file__).resolve().parents[1]


def _require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")
    return path


def _validate_clip_dirs(records: list[Any]) -> None:
    missing = [record.clip_dir for record in records if not Path(record.clip_dir).is_dir()]
    if missing:
        preview = ", ".join(missing[:3])
        raise FileNotFoundError(
            f"{len(missing)} selected clip directories do not exist. First missing: {preview}"
        )


def _write_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_sha256_sidecar(path: Path) -> dict[str, str]:
    digest = sha256_file(path)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return {"sha256": digest, "sha256_path": str(sidecar)}


BASELINE_SPECS: dict[str, dict[str, Any]] = {
    "video_autoencoder": {
        "module": video_autoencoder,
        "config": video_autoencoder.VideoAutoencoderConfig,
        "checkpoint_name": "video_autoencoder.pt",
    },
    "cnn_lstm": {
        "module": cnn_lstm,
        "config": cnn_lstm.CNNLSTMConfig,
        "checkpoint_name": "cnn_lstm.pt",
    },
    "video_transformer": {
        "module": video_transformer,
        "config": video_transformer.VideoTransformerConfig,
        "checkpoint_name": "video_transformer.pt",
    },
}


def run_kaggle_learned_baselines(
    manifest_path: Path,
    split_path: Path,
    output_root: Path,
    dry_run: bool,
    clips_root: Path | None = None,
    video_autoencoder_config: video_autoencoder.VideoAutoencoderConfig | None = None,
    cnn_lstm_config: cnn_lstm.CNNLSTMConfig | None = None,
    video_transformer_config: video_transformer.VideoTransformerConfig | None = None,
    device: str = "auto",
) -> dict[str, Any]:
    _require_file(manifest_path, "combined manifest")
    _require_file(split_path, "grouped split")
    records = read_manifest(manifest_path)
    if clips_root is not None:
        records = rebase_clip_records(records, clips_root)
    split_records = read_grouped_split_csv(split_path)
    partitions = prepare_neural_partitions(records, split_records)
    _validate_clip_dirs([*partitions.train_normal, *partitions.validation])

    resolved_configs = {
        "video_autoencoder": video_autoencoder_config or video_autoencoder.VideoAutoencoderConfig(),
        "cnn_lstm": cnn_lstm_config or cnn_lstm.CNNLSTMConfig(),
        "video_transformer": video_transformer_config or video_transformer.VideoTransformerConfig(),
    }

    output_root.mkdir(parents=True, exist_ok=True)
    train_manifest_path = output_root / "train_normal_manifest.csv"
    validation_manifest_path = output_root / "validation_manifest.csv"
    write_manifest(train_manifest_path, partitions.train_normal)
    write_manifest(validation_manifest_path, partitions.validation)
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "training pending",
        "protocol": "pair-suspect grouped; train-normal fit; frozen follow-up validation scoring only",
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "clips_root": str(clips_root) if clips_root is not None else None,
        "device": device,
        "baseline_order": list(BASELINE_SPECS),
        "baseline_configs": {name: asdict(config) for name, config in resolved_configs.items()},
        "train_normal_clip_count": len(partitions.train_normal),
        "train_normal_source_count": len({row.source for row in partitions.train_normal}),
        "validation_clip_count": len(partitions.validation),
        "validation_source_count": len({row.source for row in partitions.validation}),
        "test_clip_count": len(partitions.test),
        "test_source_count": len({row.source for row in partitions.test}),
        "test_materialized": False,
        "test_scored": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "leakage_audit": partitions.audit,
        "train_normal_manifest_path": str(train_manifest_path),
        "validation_manifest_path": str(validation_manifest_path),
    }
    audit_path = output_root / "protocol_audit.json"
    summary_path = output_root / "learned_baselines_summary.json"
    if dry_run:
        _write_json(summary, audit_path)
        _write_json(summary, summary_path)
        return summary

    baseline_outputs: dict[str, Any] = {}
    for name, spec in BASELINE_SPECS.items():
        module = spec["module"]
        config = resolved_configs[name]
        checkpoint_path = output_root / spec["checkpoint_name"]
        metadata_path = output_root / f"{name}_training_metadata.json"
        validation_scores_path = output_root / f"{name}_validation_scores.csv"
        training_metadata = module.train_model(
            partitions.train_normal,
            checkpoint_path,
            metadata_path,
            config,
            device=device,
        )
        validation_scores = module.score_records_with_checkpoint(
            partitions.validation,
            checkpoint_path,
            device=device,
        )
        module.write_scores(partitions.validation, validation_scores, validation_scores_path)
        baseline_outputs[name] = {
            "checkpoint_path": str(checkpoint_path),
            "training_metadata_path": str(metadata_path),
            "validation_scores_path": str(validation_scores_path),
            "training_metadata": training_metadata,
            **{
                f"checkpoint_{key}": value
                for key, value in _write_sha256_sidecar(checkpoint_path).items()
            },
            **{
                f"training_metadata_{key}": value
                for key, value in _write_sha256_sidecar(metadata_path).items()
            },
            **{
                f"validation_scores_{key}": value
                for key, value in _write_sha256_sidecar(validation_scores_path).items()
            },
        }
    summary.update(
        {
            "status": "training and validation scoring complete",
            "baseline_outputs": baseline_outputs,
        }
    )
    _write_json(summary, audit_path)
    _write_json(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train and score the learned video baselines on the frozen follow-up split."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Combined manifest containing train-normal and frozen validation clips.",
    )
    parser.add_argument(
        "--split",
        type=Path,
        required=True,
        help="Grouped split CSV for the frozen follow-up support.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
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
    parser.add_argument("--cnn-lstm-hidden-size", type=int, default=128)
    parser.add_argument("--video-transformer-batch-size", type=int, default=4)
    parser.add_argument("--video-transformer-learning-rate", type=float, default=1e-4)
    parser.add_argument("--video-transformer-epochs", type=int, default=1)
    parser.add_argument("--video-transformer-model-name", default="MCG-NJU/videomae-small")
    parser.add_argument("--video-transformer-hidden-size", type=int, default=384)
    parser.add_argument("--video-transformer-intermediate-size", type=int, default=1536)
    parser.add_argument("--video-transformer-num-hidden-layers", type=int, default=12)
    parser.add_argument("--video-transformer-num-attention-heads", type=int, default=6)
    parser.add_argument("--video-transformer-patch-size", type=int, default=16)
    parser.add_argument("--video-transformer-tubelet-size", type=int, default=2)
    parser.add_argument("--video-transformer-use-pretrained", action="store_true")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = run_kaggle_learned_baselines(
        manifest_path=args.manifest,
        split_path=args.split,
        output_root=args.output_root,
        dry_run=args.dry_run,
        clips_root=args.clips_root,
        video_autoencoder_config=video_autoencoder.VideoAutoencoderConfig(
            image_size=args.image_size,
            clip_length=args.clip_length,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            seed=args.seed,
            num_workers=args.num_workers,
        ),
        cnn_lstm_config=cnn_lstm.CNNLSTMConfig(
            image_size=args.image_size,
            clip_length=args.clip_length,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            seed=args.seed,
            num_workers=args.num_workers,
            hidden_size=args.cnn_lstm_hidden_size,
        ),
        video_transformer_config=video_transformer.VideoTransformerConfig(
            image_size=args.image_size,
            clip_length=args.clip_length,
            batch_size=args.video_transformer_batch_size,
            epochs=args.video_transformer_epochs,
            learning_rate=args.video_transformer_learning_rate,
            seed=args.seed,
            num_workers=args.num_workers,
            model_name=args.video_transformer_model_name,
            hidden_size=args.video_transformer_hidden_size,
            intermediate_size=args.video_transformer_intermediate_size,
            num_hidden_layers=args.video_transformer_num_hidden_layers,
            num_attention_heads=args.video_transformer_num_attention_heads,
            patch_size=args.video_transformer_patch_size,
            tubelet_size=args.video_transformer_tubelet_size,
            use_pretrained=args.video_transformer_use_pretrained,
        ),
        device=args.device,
    )
    print(f"Learned baseline status: {summary['status']}")
    print(f"Train-normal clips: {summary['train_normal_clip_count']}")
    print(f"Validation clips: {summary['validation_clip_count']}")
    print(f"Test clips scored: {summary['test_scored']}")
    print(f"Protocol audit: {args.output_root / 'protocol_audit.json'}")


if __name__ == "__main__":
    main()
