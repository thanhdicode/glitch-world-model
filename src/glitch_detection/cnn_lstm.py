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


class CNNLSTMUnavailableError(RuntimeError):
    """Raised when the optional CNN-LSTM baseline cannot train or score."""


@dataclass(frozen=True)
class CNNLSTMConfig:
    image_size: int = 64
    clip_length: int = 16
    batch_size: int = 8
    epochs: int = 10
    learning_rate: float = 1e-3
    seed: int = 42
    num_workers: int = 2
    hidden_size: int = 128

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
        if self.hidden_size < 8:
            raise ValueError("hidden_size must be at least 8.")


def require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise CNNLSTMUnavailableError(
            'CNN-LSTM baseline requires PyTorch. Install it with: python -m pip install -e ".[gpu]"'
        ) from exc
    return torch


def resolve_checkpoint(checkpoint: Path | None) -> Path:
    candidate = checkpoint or (
        Path(os.environ["CNN_LSTM_CHECKPOINT"]) if "CNN_LSTM_CHECKPOINT" in os.environ else None
    )
    if candidate is None:
        raise CNNLSTMUnavailableError(
            "CNN-LSTM scoring requires a checkpoint. Pass --checkpoint PATH or set "
            "CNN_LSTM_CHECKPOINT."
        )
    if not candidate.is_file():
        raise CNNLSTMUnavailableError(f"CNN-LSTM checkpoint does not exist: {candidate}")
    return candidate


def load_clip_array(record: ClipRecord, config: CNNLSTMConfig) -> np.ndarray:
    return _load_clip_array(
        record,
        config=type(
            "_VideoAutoencoderLikeConfig",
            (),
            {"image_size": config.image_size, "clip_length": config.clip_length},
        )(),
    )


class ClipTensorDataset:
    def __init__(self, records: list[ClipRecord], config: CNNLSTMConfig) -> None:
        if not records:
            raise ValueError("CNN-LSTM dataset requires at least one clip.")
        self.records = records
        self.config = config

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[str, Any]:
        torch = require_torch()
        record = self.records[index]
        return record.clip_id, torch.from_numpy(load_clip_array(record, self.config))


def build_model(config: CNNLSTMConfig) -> Any:
    torch = require_torch()
    nn = torch.nn
    flattened_frame_dim = 3 * config.image_size * config.image_size

    class CNNLSTMNextFramePredictor(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((4, 4)),
                nn.Flatten(),
            )
            self.lstm = nn.LSTM(
                input_size=32 * 4 * 4, hidden_size=config.hidden_size, batch_first=True
            )
            self.decoder = nn.Sequential(
                nn.Linear(config.hidden_size, flattened_frame_dim),
                nn.Sigmoid(),
            )

        def forward(self, inputs: Any) -> Any:
            batch_size, _channels, steps, height, width = inputs.shape
            frames = inputs.permute(0, 2, 1, 3, 4).reshape(batch_size * steps, 3, height, width)
            encoded = self.encoder(frames).reshape(batch_size, steps, -1)
            recurrent_output, _ = self.lstm(encoded[:, :-1, :])
            decoded = self.decoder(recurrent_output.reshape(batch_size * (steps - 1), -1))
            return decoded.reshape(batch_size, steps - 1, 3, height, width).permute(0, 2, 1, 3, 4)

    return CNNLSTMNextFramePredictor()


def _resolve_device(torch: Any, device: str) -> Any:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise CNNLSTMUnavailableError("CUDA was requested but is not available.")
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


def _data_loader(records: list[ClipRecord], config: CNNLSTMConfig, shuffle: bool) -> Any:
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
    config: CNNLSTMConfig,
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
            targets = clips[:, :, 1:, :, :]
            optimizer.zero_grad(set_to_none=True)
            predictions = model(clips)
            loss = criterion(predictions, targets)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
        epoch_losses.append(float(np.mean(losses)))

    metadata = {
        "model": "cnn_lstm_next_frame",
        "fit_split": "train-normal",
        "train_clip_count": len(records),
        "train_source_count": len({record.source for record in records}),
        "config": asdict(config),
        "device": str(resolved_device),
        "epoch_losses": epoch_losses,
        "score_definition": "mean next-frame prediction MSE across the clip",
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


def load_model(checkpoint_path: Path, device: str = "auto") -> tuple[Any, CNNLSTMConfig, Any]:
    torch = require_torch()
    resolved_device = _resolve_device(torch, device)
    try:
        payload = torch.load(checkpoint_path, map_location=resolved_device, weights_only=True)
    except TypeError:
        payload = torch.load(checkpoint_path, map_location=resolved_device)
    config = CNNLSTMConfig(**payload["config"])
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
            targets = clips[:, :, 1:, :, :]
            predictions = model(clips)
            errors = torch.mean((predictions - targets) ** 2, dim=(1, 2, 3, 4))
            for clip_id, error in zip(clip_ids, errors.detach().cpu().tolist()):
                scores[str(clip_id)] = float(error)
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
    parser = argparse.ArgumentParser(description="Train or score the CNN-LSTM video baseline.")
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
    train_parser.add_argument("--hidden-size", type=int, default=128)
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
        config = CNNLSTMConfig(
            image_size=args.image_size,
            clip_length=args.clip_length,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            seed=args.seed,
            num_workers=args.num_workers,
            hidden_size=args.hidden_size,
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
