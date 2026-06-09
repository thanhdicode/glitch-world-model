from __future__ import annotations

import argparse
import csv
import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .manifest import ClipRecord, read_manifest
from .preprocess import IMAGE_EXTENSIONS


class VideoAutoencoderUnavailableError(RuntimeError):
    """Raised when the optional neural baseline cannot train or score."""


@dataclass(frozen=True)
class VideoAutoencoderConfig:
    image_size: int = 64
    clip_length: int = 16
    batch_size: int = 8
    epochs: int = 10
    learning_rate: float = 1e-3
    seed: int = 42
    num_workers: int = 2

    def __post_init__(self) -> None:
        if self.image_size < 8 or self.image_size % 4 != 0:
            raise ValueError("image_size must be at least 8 and divisible by 4.")
        if self.clip_length < 2:
            raise ValueError("clip_length must be at least 2.")
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive.")
        if self.epochs < 1:
            raise ValueError("epochs must be positive.")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if self.num_workers < 0:
            raise ValueError("num_workers cannot be negative.")


def require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise VideoAutoencoderUnavailableError(
            'Video autoencoder requires PyTorch. Install it with: python -m pip install -e ".[gpu]"'
        ) from exc
    return torch


def resolve_checkpoint(checkpoint: Path | None) -> Path:
    candidate = checkpoint or (
        Path(os.environ["VIDEO_AUTOENCODER_CHECKPOINT"])
        if "VIDEO_AUTOENCODER_CHECKPOINT" in os.environ
        else None
    )
    if candidate is None:
        raise VideoAutoencoderUnavailableError(
            "Video autoencoder scoring requires a checkpoint. Pass --checkpoint PATH or set "
            "VIDEO_AUTOENCODER_CHECKPOINT."
        )
    if not candidate.is_file():
        raise VideoAutoencoderUnavailableError(
            f"Video autoencoder checkpoint does not exist: {candidate}"
        )
    return candidate


def list_clip_frames(clip_dir: Path) -> list[Path]:
    if not clip_dir.is_dir():
        raise FileNotFoundError(f"Clip directory does not exist: {clip_dir}")
    frames = sorted(
        path
        for path in clip_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not frames:
        raise ValueError(f"Clip directory contains no supported frames: {clip_dir}")
    return frames


def select_frame_paths(frames: list[Path], clip_length: int) -> list[Path]:
    if not frames:
        raise ValueError("Cannot sample an empty frame list.")
    if clip_length < 1:
        raise ValueError("clip_length must be positive.")
    if len(frames) < clip_length:
        return [*frames, *([frames[-1]] * (clip_length - len(frames)))]
    indices = np.linspace(0, len(frames) - 1, clip_length, dtype=int)
    return [frames[int(index)] for index in indices]


def load_clip_array(record: ClipRecord, config: VideoAutoencoderConfig) -> np.ndarray:
    frame_paths = select_frame_paths(list_clip_frames(Path(record.clip_dir)), config.clip_length)
    frames: list[np.ndarray] = []
    for path in frame_paths:
        with Image.open(path) as image:
            rgb = image.convert("RGB").resize(
                (config.image_size, config.image_size), Image.Resampling.BILINEAR
            )
            frames.append(np.asarray(rgb, dtype=np.float32) / 255.0)
    return np.transpose(np.stack(frames), (3, 0, 1, 2)).astype(np.float32)


class ClipTensorDataset:
    def __init__(self, records: list[ClipRecord], config: VideoAutoencoderConfig) -> None:
        if not records:
            raise ValueError("Video autoencoder dataset requires at least one clip.")
        self.records = records
        self.config = config

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[str, Any]:
        torch = require_torch()
        record = self.records[index]
        return record.clip_id, torch.from_numpy(load_clip_array(record, self.config))


def build_model(config: VideoAutoencoderConfig) -> Any:
    _ = config
    torch = require_torch()
    nn = torch.nn

    class Conv3dAutoencoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Conv3d(3, 16, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv3d(16, 32, kernel_size=3, stride=(1, 2, 2), padding=1),
                nn.ReLU(inplace=True),
                nn.Conv3d(32, 64, kernel_size=3, stride=(1, 2, 2), padding=1),
                nn.ReLU(inplace=True),
            )
            self.decoder = nn.Sequential(
                nn.ConvTranspose3d(
                    64, 32, kernel_size=(3, 4, 4), stride=(1, 2, 2), padding=(1, 1, 1)
                ),
                nn.ReLU(inplace=True),
                nn.ConvTranspose3d(
                    32, 16, kernel_size=(3, 4, 4), stride=(1, 2, 2), padding=(1, 1, 1)
                ),
                nn.ReLU(inplace=True),
                nn.Conv3d(16, 3, kernel_size=3, padding=1),
                nn.Sigmoid(),
            )

        def forward(self, inputs: Any) -> Any:
            return self.decoder(self.encoder(inputs))

    return Conv3dAutoencoder()


def _resolve_device(torch: Any, device: str) -> Any:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise VideoAutoencoderUnavailableError("CUDA was requested but is not available.")
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


def _data_loader(
    records: list[ClipRecord],
    config: VideoAutoencoderConfig,
    shuffle: bool,
) -> Any:
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


def train_model(
    records: list[ClipRecord],
    checkpoint_path: Path,
    metadata_path: Path,
    config: VideoAutoencoderConfig,
    device: str = "auto",
) -> dict[str, Any]:
    torch = require_torch()
    _set_deterministic_seed(torch, config.seed)
    resolved_device = _resolve_device(torch, device)
    model = build_model(config).to(resolved_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = torch.nn.MSELoss()
    loader = _data_loader(records, config, shuffle=True)
    epoch_losses: list[float] = []

    model.train()
    for _epoch in range(config.epochs):
        losses: list[float] = []
        for _clip_ids, clips in loader:
            clips = clips.to(resolved_device)
            optimizer.zero_grad(set_to_none=True)
            reconstructed = model(clips)
            loss = criterion(reconstructed, clips)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
        epoch_losses.append(float(np.mean(losses)))

    metadata = {
        "model": "conv3d_autoencoder",
        "fit_split": "train-normal",
        "train_clip_count": len(records),
        "train_source_count": len({record.source for record in records}),
        "config": asdict(config),
        "device": str(resolved_device),
        "epoch_losses": epoch_losses,
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": metadata["model"],
            "config": asdict(config),
            "state_dict": model.state_dict(),
        },
        checkpoint_path,
    )
    metadata["checkpoint_path"] = str(checkpoint_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_model(
    checkpoint_path: Path, device: str = "auto"
) -> tuple[Any, VideoAutoencoderConfig, Any]:
    torch = require_torch()
    resolved_device = _resolve_device(torch, device)
    try:
        payload = torch.load(checkpoint_path, map_location=resolved_device, weights_only=True)
    except TypeError:
        payload = torch.load(checkpoint_path, map_location=resolved_device)
    config = VideoAutoencoderConfig(**payload["config"])
    model = build_model(config).to(resolved_device)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, config, resolved_device


def score_records_with_checkpoint(
    records: list[ClipRecord],
    checkpoint_path: Path,
    device: str = "auto",
) -> dict[str, float]:
    torch = require_torch()
    model, config, resolved_device = load_model(checkpoint_path, device=device)
    loader = _data_loader(records, config, shuffle=False)
    scores: dict[str, float] = {}
    with torch.no_grad():
        for clip_ids, clips in loader:
            clips = clips.to(resolved_device)
            reconstructed = model(clips)
            errors = torch.mean((reconstructed - clips) ** 2, dim=(1, 2, 3, 4))
            for clip_id, error in zip(clip_ids, errors.detach().cpu().tolist()):
                scores[str(clip_id)] = float(error)
    return scores


def write_scores(
    records: list[ClipRecord],
    scores: dict[str, float],
    output_path: Path,
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
    parser = argparse.ArgumentParser(description="Train or score a Conv3D video autoencoder.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser(
        "train", help="Train on a caller-supplied normal manifest."
    )
    train_parser.add_argument("--manifest", required=True, type=Path)
    train_parser.add_argument("--checkpoint", required=True, type=Path)
    train_parser.add_argument("--metadata", required=True, type=Path)
    train_parser.add_argument("--image-size", type=int, default=64)
    train_parser.add_argument("--clip-length", type=int, default=16)
    train_parser.add_argument("--batch-size", type=int, default=8)
    train_parser.add_argument("--epochs", type=int, default=10)
    train_parser.add_argument("--learning-rate", type=float, default=1e-3)
    train_parser.add_argument("--seed", type=int, default=42)
    train_parser.add_argument("--num-workers", type=int, default=2)
    train_parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")

    score_parser = subparsers.add_parser("score", help="Score clips with a trained checkpoint.")
    score_parser.add_argument("--manifest", required=True, type=Path)
    score_parser.add_argument("--output", required=True, type=Path)
    score_parser.add_argument("--checkpoint", type=Path, default=None)
    score_parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "train":
        config = VideoAutoencoderConfig(
            image_size=args.image_size,
            clip_length=args.clip_length,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            seed=args.seed,
            num_workers=args.num_workers,
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
