from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .manifest import ClipRecord, read_manifest
from .video_autoencoder import load_clip_array as _load_clip_array
from .video_autoencoder import write_scores as _write_scores


class VideoTransformerUnavailableError(RuntimeError):
    """Raised when the optional VideoMAE-style baseline cannot train or score."""


@dataclass(frozen=True)
class VideoTransformerConfig:
    image_size: int = 64
    clip_length: int = 16
    batch_size: int = 4
    epochs: int = 1
    learning_rate: float = 1e-4
    seed: int = 42
    num_workers: int = 2
    model_name: str = "MCG-NJU/videomae-small"
    hidden_size: int = 384
    intermediate_size: int = 1536
    num_hidden_layers: int = 12
    num_attention_heads: int = 6
    patch_size: int = 16
    tubelet_size: int = 2
    use_pretrained: bool = False

    def __post_init__(self) -> None:
        if self.image_size < 16 or self.image_size % self.patch_size != 0:
            raise ValueError("image_size must be at least patch_size and divisible by patch_size.")
        if self.clip_length < 2 or self.clip_length % self.tubelet_size != 0:
            raise ValueError("clip_length must be at least 2 and divisible by tubelet_size.")
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive.")
        if self.epochs < 1:
            raise ValueError("epochs must be positive.")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if self.num_workers < 0:
            raise ValueError("num_workers cannot be negative.")
        if self.hidden_size < 32:
            raise ValueError("hidden_size must be at least 32.")
        if self.num_hidden_layers < 1:
            raise ValueError("num_hidden_layers must be positive.")
        if self.num_attention_heads < 1:
            raise ValueError("num_attention_heads must be positive.")


def require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise VideoTransformerUnavailableError(
            'Video transformer baseline requires PyTorch. Install it with: python -m pip install -e ".[gpu]"'
        ) from exc
    return torch


def require_transformers() -> tuple[Any, Any]:
    try:
        from transformers import VideoMAEConfig, VideoMAEModel
    except ImportError as exc:
        raise VideoTransformerUnavailableError(
            "Video transformer baseline requires transformers==4.57.6 in the Kaggle/runtime "
            "environment."
        ) from exc
    return VideoMAEConfig, VideoMAEModel


def resolve_checkpoint(checkpoint: Path | None) -> Path:
    candidate = checkpoint or (
        Path(os.environ["VIDEO_TRANSFORMER_CHECKPOINT"])
        if "VIDEO_TRANSFORMER_CHECKPOINT" in os.environ
        else None
    )
    if candidate is None:
        raise VideoTransformerUnavailableError(
            "Video transformer scoring requires a checkpoint. Pass --checkpoint PATH or set "
            "VIDEO_TRANSFORMER_CHECKPOINT."
        )
    if not candidate.is_file():
        raise VideoTransformerUnavailableError(
            f"Video transformer checkpoint does not exist: {candidate}"
        )
    return candidate


def load_clip_array(record: ClipRecord, config: VideoTransformerConfig) -> np.ndarray:
    array = _load_clip_array(
        record,
        config=type(
            "_VideoAutoencoderLikeConfig",
            (),
            {"image_size": config.image_size, "clip_length": config.clip_length},
        )(),
    )
    return np.transpose(array, (1, 0, 2, 3)).astype(np.float32)


class ClipTensorDataset:
    def __init__(self, records: list[ClipRecord], config: VideoTransformerConfig) -> None:
        if not records:
            raise ValueError("Video transformer dataset requires at least one clip.")
        self.records = records
        self.config = config

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[str, Any]:
        torch = require_torch()
        record = self.records[index]
        return record.clip_id, torch.from_numpy(load_clip_array(record, self.config))


def build_model(config: VideoTransformerConfig) -> Any:
    _torch = require_torch()
    VideoMAEConfig, VideoMAEModel = require_transformers()
    if config.use_pretrained:
        try:
            return VideoMAEModel.from_pretrained(config.model_name, local_files_only=True)
        except OSError as exc:
            raise VideoTransformerUnavailableError(
                f"VideoMAE weights for {config.model_name!r} are not available locally. Provide a "
                "cached Hugging Face snapshot or disable --use-pretrained."
            ) from exc
    return VideoMAEModel(
        VideoMAEConfig(
            image_size=config.image_size,
            num_frames=config.clip_length,
            hidden_size=config.hidden_size,
            intermediate_size=config.intermediate_size,
            num_hidden_layers=config.num_hidden_layers,
            num_attention_heads=config.num_attention_heads,
            patch_size=config.patch_size,
            tubelet_size=config.tubelet_size,
            qkv_bias=True,
        )
    )


def _resolve_device(torch: Any, device: str) -> Any:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise VideoTransformerUnavailableError("CUDA was requested but is not available.")
    return torch.device(device)


def _set_deterministic_seed(torch: Any, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def _data_loader(records: list[ClipRecord], config: VideoTransformerConfig, shuffle: bool) -> Any:
    torch = require_torch()
    generator = torch.Generator()
    generator.manual_seed(config.seed)
    return torch.utils.data.DataLoader(
        ClipTensorDataset(records, config),
        batch_size=config.batch_size,
        shuffle=shuffle,
        num_workers=config.num_workers,
        generator=generator,
    )


def _pooled_features(model: Any, clips: Any) -> Any:
    output = model(pixel_values=clips)
    last_hidden = getattr(output, "last_hidden_state", None)
    if last_hidden is None:
        raise VideoTransformerUnavailableError(
            "Video transformer output did not expose last_hidden_state."
        )
    return last_hidden.mean(dim=1)


def train_model(
    records: list[ClipRecord],
    checkpoint_path: Path,
    metadata_path: Path,
    config: VideoTransformerConfig,
    device: str = "auto",
) -> dict[str, Any]:
    torch = require_torch()
    _set_deterministic_seed(torch, config.seed)
    resolved_device = _resolve_device(torch, device)
    model = build_model(config).to(resolved_device)
    loader = _data_loader(records, config, shuffle=False)
    feature_sum = None
    clip_count = 0

    model.eval()
    with torch.no_grad():
        for _clip_ids, clips in loader:
            clips = clips.to(resolved_device)
            features = _pooled_features(model, clips)
            batch_sum = features.sum(dim=0)
            feature_sum = batch_sum if feature_sum is None else feature_sum + batch_sum
            clip_count += int(features.shape[0])
    if clip_count < 1 or feature_sum is None:
        raise ValueError("Video transformer fit requires at least one train-normal clip.")
    centroid = (feature_sum / clip_count).detach().cpu()

    metadata = {
        "model": "videomae_small_feature_distance",
        "fit_split": "train-normal",
        "fit_mode": "feature_centroid",
        "train_clip_count": len(records),
        "train_source_count": len({record.source for record in records}),
        "config": asdict(config),
        "device": str(resolved_device),
        "score_definition": "L2 distance from the train-normal pooled VideoMAE feature centroid",
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": metadata["model"],
            "config": asdict(config),
            "state_dict": model.state_dict(),
            "feature_centroid": centroid,
        },
        checkpoint_path,
    )
    metadata["checkpoint_path"] = str(checkpoint_path)
    metadata["feature_dim"] = int(centroid.numel())
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_model(
    checkpoint_path: Path,
    device: str = "auto",
) -> tuple[Any, VideoTransformerConfig, Any, Any]:
    torch = require_torch()
    resolved_device = _resolve_device(torch, device)
    try:
        payload = torch.load(checkpoint_path, map_location=resolved_device, weights_only=True)
    except TypeError:
        payload = torch.load(checkpoint_path, map_location=resolved_device)
    config = VideoTransformerConfig(**payload["config"])
    model = build_model(config).to(resolved_device)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    feature_centroid = payload["feature_centroid"].to(resolved_device)
    return model, config, feature_centroid, resolved_device


def score_records_with_checkpoint(
    records: list[ClipRecord],
    checkpoint_path: Path,
    device: str = "auto",
) -> dict[str, float]:
    torch = require_torch()
    model, config, feature_centroid, resolved_device = load_model(checkpoint_path, device=device)
    loader = _data_loader(records, config, shuffle=False)
    scores: dict[str, float] = {}
    with torch.no_grad():
        for clip_ids, clips in loader:
            clips = clips.to(resolved_device)
            features = _pooled_features(model, clips)
            distances = torch.linalg.norm(features - feature_centroid.reshape(1, -1), dim=1)
            for clip_id, distance in zip(clip_ids, distances.detach().cpu().tolist()):
                scores[str(clip_id)] = float(distance)
    return scores


def write_scores(records: list[ClipRecord], scores: dict[str, float], output_path: Path) -> Path:
    return _write_scores(records, scores, output_path)


def score_manifest(
    manifest_path: Path,
    labels_path: Path | None,
    output_path: Path,
    checkpoint: Path | None = None,
    device: str = "auto",
) -> Path:
    _ = labels_path
    checkpoint_path = resolve_checkpoint(checkpoint)
    records = read_manifest(manifest_path)
    scores = score_records_with_checkpoint(records, checkpoint_path, device=device)
    return write_scores(records, scores, output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fit or score the VideoMAE-small feature-distance baseline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Fit the train-normal feature centroid.")
    train_parser.add_argument("--manifest", required=True, type=Path)
    train_parser.add_argument("--checkpoint", required=True, type=Path)
    train_parser.add_argument("--metadata", required=True, type=Path)
    train_parser.add_argument("--image-size", type=int, default=64)
    train_parser.add_argument("--clip-length", type=int, default=16)
    train_parser.add_argument("--batch-size", type=int, default=4)
    train_parser.add_argument("--epochs", type=int, default=1)
    train_parser.add_argument("--learning-rate", type=float, default=1e-4)
    train_parser.add_argument("--seed", type=int, default=42)
    train_parser.add_argument("--num-workers", type=int, default=2)
    train_parser.add_argument("--hidden-size", type=int, default=384)
    train_parser.add_argument("--intermediate-size", type=int, default=1536)
    train_parser.add_argument("--num-hidden-layers", type=int, default=12)
    train_parser.add_argument("--num-attention-heads", type=int, default=6)
    train_parser.add_argument("--patch-size", type=int, default=16)
    train_parser.add_argument("--tubelet-size", type=int, default=2)
    train_parser.add_argument("--model-name", default="MCG-NJU/videomae-small")
    train_parser.add_argument("--use-pretrained", action="store_true")
    train_parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")

    score_parser = subparsers.add_parser("score", help="Score clips with a fitted checkpoint.")
    score_parser.add_argument("--manifest", required=True, type=Path)
    score_parser.add_argument("--output", required=True, type=Path)
    score_parser.add_argument("--checkpoint", type=Path, default=None)
    score_parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "train":
        config = VideoTransformerConfig(
            image_size=args.image_size,
            clip_length=args.clip_length,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            seed=args.seed,
            num_workers=args.num_workers,
            model_name=args.model_name,
            hidden_size=args.hidden_size,
            intermediate_size=args.intermediate_size,
            num_hidden_layers=args.num_hidden_layers,
            num_attention_heads=args.num_attention_heads,
            patch_size=args.patch_size,
            tubelet_size=args.tubelet_size,
            use_pretrained=args.use_pretrained,
        )
        metadata = train_model(
            read_manifest(args.manifest),
            args.checkpoint,
            args.metadata,
            config,
            device=args.device,
        )
        print(f"Training complete: {metadata['checkpoint_path']}")
        return
    output_path = score_manifest(
        args.manifest,
        None,
        args.output,
        checkpoint=args.checkpoint,
        device=args.device,
    )
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()
