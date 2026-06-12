from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .kaggle_automation import FingerprintBuilder
from .lewm_adapter import sha256_file


class LeWMTrainingError(RuntimeError):
    """Raised when the optional real-LeWM training runtime is unavailable or invalid."""


@dataclass(frozen=True)
class LeWMTrainConfig:
    image_size: int = 112
    history_size: int = 3
    embed_dim: int = 192
    predictor_depth: int = 6
    predictor_heads: int = 16
    predictor_mlp_dim: int = 2048
    predictor_dim_head: int = 64
    batch_size: int = 4
    epochs: int = 1
    learning_rate: float = 5e-5
    weight_decay: float = 1e-3
    sigreg_weight: float = 0.09
    sigreg_projections: int = 128
    seed: int = 42
    max_train_steps: int | None = None
    max_validation_steps: int | None = None
    allow_identical_datasets_for_smoke: bool = False
    run_kind: str = "engineering_smoke"
    num_workers: int = 0
    pin_memory: bool = False
    mixed_precision: bool = False
    early_stopping_patience: int | None = None
    early_stopping_min_delta: float = 0.0
    gradient_clip_norm: float | None = None

    def __post_init__(self) -> None:
        if self.image_size < 28 or self.image_size % 14:
            raise ValueError("LeWM image_size must be at least 28 and divisible by patch size 14.")
        if self.history_size < 1 or self.batch_size < 1 or self.epochs < 1:
            raise ValueError("LeWM history_size, batch_size, and epochs must be positive.")
        if self.sigreg_projections < 1:
            raise ValueError("LeWM sigreg_projections must be positive.")
        if self.run_kind not in {"engineering_smoke", "research"}:
            raise ValueError("LeWM run_kind must be engineering_smoke or research.")
        if self.num_workers < 0:
            raise ValueError("LeWM num_workers cannot be negative.")
        if self.early_stopping_patience is not None and self.early_stopping_patience < 1:
            raise ValueError("LeWM early_stopping_patience must be positive when set.")
        if self.early_stopping_min_delta < 0:
            raise ValueError("LeWM early_stopping_min_delta cannot be negative.")
        if self.gradient_clip_norm is not None and self.gradient_clip_norm <= 0:
            raise ValueError("LeWM gradient_clip_norm must be positive when set.")


def _require_runtime() -> tuple[Any, Any]:
    try:
        import torch
        from hydra.utils import instantiate
    except ImportError as exc:
        raise LeWMTrainingError("LeWM training requires the isolated Python 3.10 runtime.") from exc
    return torch, instantiate


def _config_hash(config: LeWMTrainConfig) -> str:
    return hashlib.sha256(
        json.dumps(asdict(config), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_model_config(config: LeWMTrainConfig, action_dim: int) -> dict[str, Any]:
    return {
        "_target_": "stable_worldmodel.wm.lewm.LeWM",
        "encoder": {
            "_target_": "stable_pretraining.backbone.utils.vit_hf",
            "size": "tiny",
            "patch_size": 14,
            "image_size": config.image_size,
            "pretrained": False,
            "use_mask_token": False,
        },
        "predictor": {
            "_target_": "stable_worldmodel.wm.lewm.module.Predictor",
            "num_frames": config.history_size,
            "input_dim": config.embed_dim,
            "hidden_dim": config.embed_dim,
            "output_dim": config.embed_dim,
            "depth": config.predictor_depth,
            "heads": config.predictor_heads,
            "mlp_dim": config.predictor_mlp_dim,
            "dim_head": config.predictor_dim_head,
            "dropout": 0.1,
            "emb_dropout": 0.0,
        },
        "action_encoder": {
            "_target_": "stable_worldmodel.wm.lewm.module.Embedder",
            "input_dim": action_dim,
            "emb_dim": config.embed_dim,
        },
        "projector": {
            "_target_": "stable_worldmodel.wm.lewm.module.MLP",
            "input_dim": config.embed_dim,
            "output_dim": config.embed_dim,
            "hidden_dim": 2048,
            "norm_fn": {"_target_": "torch.nn.BatchNorm1d", "_partial_": True},
        },
        "pred_proj": {
            "_target_": "stable_worldmodel.wm.lewm.module.MLP",
            "input_dim": config.embed_dim,
            "output_dim": config.embed_dim,
            "hidden_dim": 2048,
            "norm_fn": {"_target_": "torch.nn.BatchNorm1d", "_partial_": True},
        },
    }


def _preprocess_pixels(torch: Any, pixels: Any, image_size: int, device: Any) -> Any:
    functional = torch.nn.functional
    pixels = pixels.to(device=device, dtype=torch.float32).div_(255.0)
    batch, steps, channels, height, width = pixels.shape
    pixels = functional.interpolate(
        pixels.reshape(batch * steps, channels, height, width),
        size=(image_size, image_size),
        mode="bilinear",
        align_corners=False,
    ).reshape(batch, steps, channels, image_size, image_size)
    mean = torch.tensor([0.485, 0.456, 0.406], device=device).view(1, 1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device=device).view(1, 1, 3, 1, 1)
    return (pixels - mean) / std


def _sigreg(torch: Any, embeddings: Any, projections: int) -> Any:
    values = embeddings.transpose(0, 1)
    knots = 17
    t = torch.linspace(0, 3, knots, device=values.device)
    delta = 3 / (knots - 1)
    weights = torch.full((knots,), 2 * delta, device=values.device)
    weights[[0, -1]] = delta
    phi = torch.exp(-t.square() / 2.0)
    weights = weights * phi
    directions = torch.randn(values.size(-1), projections, device=values.device)
    directions = directions / directions.norm(p=2, dim=0).clamp_min(1e-8)
    projected = (values @ directions).unsqueeze(-1) * t
    error = (projected.cos().mean(-3) - phi).square() + projected.sin().mean(-3).square()
    return ((error @ weights) * values.size(-2)).mean()


def _dataset(path: Path, config: LeWMTrainConfig) -> Any:
    try:
        import stable_worldmodel as swm
    except ImportError as exc:
        raise LeWMTrainingError("stable-worldmodel is unavailable.") from exc
    return swm.data.LanceDataset(
        path=str(path.resolve().as_posix()),
        num_steps=config.history_size + 1,
        frameskip=1,
        keys_to_load=["pixels", "action"],
    )


def _run_epoch(
    model: Any,
    loader: Any,
    config: LeWMTrainConfig,
    device: Any,
    *,
    optimizer: Any | None,
    max_steps: int | None,
    scaler: Any | None = None,
) -> tuple[list[dict[str, float]], Any]:
    torch, _ = _require_runtime()
    training = optimizer is not None
    model.train(training)
    history: list[dict[str, float]] = []
    last_embeddings = None
    for step, batch in enumerate(loader):
        if max_steps is not None and step >= max_steps:
            break
        pixels = _preprocess_pixels(torch, batch["pixels"], config.image_size, device)
        actions = torch.nan_to_num(batch["action"].to(device), 0.0)
        use_amp = config.mixed_precision and device.type == "cuda"
        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, enabled=use_amp):
                output = model.encode({"pixels": pixels, "action": actions})
                embeddings = output["emb"]
                predicted = model.predict(
                    embeddings[:, : config.history_size],
                    output["act_emb"][:, : config.history_size],
                )
                target = embeddings[:, 1 : config.history_size + 1]
                prediction_loss = (predicted - target).pow(2).mean()
                sigreg_loss = _sigreg(torch, embeddings, config.sigreg_projections)
                loss = prediction_loss + config.sigreg_weight * sigreg_loss
            if training:
                optimizer.zero_grad(set_to_none=True)
                if scaler is not None and scaler.is_enabled():
                    scaler.scale(loss).backward()
                    if config.gradient_clip_norm is not None:
                        scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(
                            model.parameters(), config.gradient_clip_norm
                        )
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    if config.gradient_clip_norm is not None:
                        torch.nn.utils.clip_grad_norm_(
                            model.parameters(), config.gradient_clip_norm
                        )
                    optimizer.step()
        last_embeddings = embeddings.detach()
        history.append(
            {
                "loss": float(loss.detach().cpu()),
                "prediction_loss": float(prediction_loss.detach().cpu()),
                "sigreg_loss": float(sigreg_loss.detach().cpu()),
            }
        )
    if not history:
        raise LeWMTrainingError("LeWM dataset yielded no training/validation batches.")
    return history, last_embeddings


def train_lewm(
    train_path: Path,
    validation_path: Path,
    output_root: Path,
    config: LeWMTrainConfig,
    *,
    device: str = "auto",
    resume: bool = False,
) -> dict[str, Any]:
    torch, instantiate = _require_runtime()
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    resolved_device = torch.device(
        "cuda"
        if device == "auto" and torch.cuda.is_available()
        else ("cpu" if device == "auto" else device)
    )
    if resolved_device.type == "cuda" and not torch.cuda.is_available():
        raise LeWMTrainingError("CUDA was requested but is unavailable.")

    train_dataset = _dataset(train_path, config)
    validation_dataset = _dataset(validation_path, config)
    action_dim = int(train_dataset.get_dim("action"))
    if int(validation_dataset.get_dim("action")) != action_dim:
        raise LeWMTrainingError("Train and validation action dimensions differ.")
    model_config = build_model_config(config, action_dim)
    model = instantiate(model_config).to(resolved_device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    output_root.mkdir(parents=True, exist_ok=True)
    config_hash = _config_hash(config)
    dataset_hashes = {
        "train": FingerprintBuilder.inventory_sha256(train_path),
        "validation": FingerprintBuilder.inventory_sha256(validation_path),
    }
    if (
        dataset_hashes["train"] == dataset_hashes["validation"]
        and not config.allow_identical_datasets_for_smoke
    ):
        raise LeWMTrainingError(
            "Train and validation datasets are identical; permit this only for an explicit smoke."
        )
    checkpoint_path = output_root / "checkpoint_weights.pt"
    start_epoch = 0
    loss_history_path = output_root / "loss_history.json"
    loss_history: list[dict[str, Any]] = []
    best_weights_path = output_root / "best_weights.pt"
    best_metadata_path = output_root / "best_checkpoint_metadata.json"
    best_validation_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    if best_metadata_path.is_file():
        best_metadata = json.loads(best_metadata_path.read_text(encoding="utf-8"))
        best_validation_loss = float(best_metadata["validation_loss"])
        best_epoch = int(best_metadata["epoch"])
    if resume:
        if not checkpoint_path.is_file():
            raise LeWMTrainingError("Resume requested but checkpoint_weights.pt is missing.")
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if (
            checkpoint["config_hash"] != config_hash
            or checkpoint["dataset_hashes"] != dataset_hashes
        ):
            raise LeWMTrainingError("Resume checkpoint config/dataset hashes do not match.")
        model.load_state_dict(checkpoint["model"], strict=True)
        optimizer.load_state_dict(checkpoint["optimizer"])
        start_epoch = int(checkpoint["epoch"])
        epochs_without_improvement = int(checkpoint.get("epochs_without_improvement", 0))
        if loss_history_path.is_file():
            loss_history = json.loads(loss_history_path.read_text(encoding="utf-8"))

    generator = torch.Generator().manual_seed(config.seed)
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
    )
    validation_loader = torch.utils.data.DataLoader(
        validation_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
    )
    scaler = torch.amp.GradScaler(
        "cuda", enabled=config.mixed_precision and resolved_device.type == "cuda"
    )
    final_embeddings = None
    completed_epoch = start_epoch
    stopped_early = False
    for epoch in range(start_epoch, start_epoch + config.epochs):
        train_losses, _ = _run_epoch(
            model,
            train_loader,
            config,
            resolved_device,
            optimizer=optimizer,
            max_steps=config.max_train_steps,
            scaler=scaler,
        )
        validation_losses, final_embeddings = _run_epoch(
            model,
            validation_loader,
            config,
            resolved_device,
            optimizer=None,
            max_steps=config.max_validation_steps,
        )
        completed_epoch = epoch + 1
        loss_history.append(
            {"epoch": epoch + 1, "train": train_losses, "validation": validation_losses}
        )
        mean_validation_loss = float(
            np.mean([row["loss"] for row in validation_losses], dtype=np.float64)
        )
        improved = mean_validation_loss < (best_validation_loss - config.early_stopping_min_delta)
        if improved:
            best_validation_loss = mean_validation_loss
            best_epoch = epoch + 1
            epochs_without_improvement = 0
            torch.save(model.state_dict(), best_weights_path)
            best_metadata_path.write_text(
                json.dumps(
                    {
                        "epoch": best_epoch,
                        "validation_loss": best_validation_loss,
                        "selection_split": "validation_normal",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            epochs_without_improvement += 1
        torch.save(
            {
                "epoch": epoch + 1,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "config_hash": config_hash,
                "dataset_hashes": dataset_hashes,
                "epochs_without_improvement": epochs_without_improvement,
            },
            checkpoint_path,
        )
        if (
            config.early_stopping_patience is not None
            and epochs_without_improvement >= config.early_stopping_patience
        ):
            stopped_early = True
            break

    weights_path = output_root / "weights.pt"
    torch.save(model.state_dict(), weights_path)
    (output_root / "config.json").write_text(
        json.dumps(model_config, indent=2) + "\n", encoding="utf-8"
    )
    loss_history_path.write_text(json.dumps(loss_history, indent=2) + "\n", encoding="utf-8")
    flat = final_embeddings.reshape(-1, final_embeddings.shape[-1]).float()
    diagnostics = {
        "latent_variance_mean": float(flat.var(dim=0).mean().cpu()),
        "latent_variance_min": float(flat.var(dim=0).min().cpu()),
        "finite": bool(torch.isfinite(flat).all().item()),
    }
    (output_root / "collapse_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    metadata = {
        "status": (
            "research_run_complete_unvalidated"
            if config.run_kind == "research"
            else "training_smoke_complete"
        ),
        "device": str(resolved_device),
        "config": asdict(config),
        "config_hash": config_hash,
        "dataset_hashes": dataset_hashes,
        "action_dim": action_dim,
        "start_epoch": start_epoch,
        "completed_epoch": completed_epoch,
        "stopped_early": stopped_early,
        "epochs_without_improvement": epochs_without_improvement,
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "weights_sha256": sha256_file(weights_path),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    (output_root / "training_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (output_root / "checkpoint.sha256").write_text(
        metadata["checkpoint_sha256"] + "\n", encoding="utf-8"
    )
    reloaded_model = instantiate(model_config)
    reloaded_model.load_state_dict(
        torch.load(best_weights_path, map_location="cpu", weights_only=True),
        strict=True,
    )
    reload_metadata = {
        "checkpoint_reload_verified": True,
        "best_epoch": best_epoch,
        "best_validation_loss": best_validation_loss,
        "best_weights_sha256": sha256_file(best_weights_path),
        "strict": True,
    }
    (output_root / "checkpoint_reload.json").write_text(
        json.dumps(reload_metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def score_lance_probe(
    dataset_path: Path,
    weights_path: Path,
    config_path: Path,
    *,
    action_mode: str = "zero_action",
    device: str = "cpu",
) -> dict[str, Any]:
    from .lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec

    torch, _ = _require_runtime()
    adapter = LeWMAdapter(
        LeWMCheckpointSpec(
            weights_path=weights_path,
            config_path=config_path,
            action_mode=ActionMode(action_mode),
            device=device,
        )
    ).load()
    config = LeWMTrainConfig(
        image_size=adapter.image_size,
        history_size=adapter.history_size,
        batch_size=1,
    )
    dataset = _dataset(dataset_path, config)
    loader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=False)
    batch = next(iter(loader))
    pixels = _preprocess_pixels(torch, batch["pixels"], adapter.image_size, torch.device(device))
    surprise = adapter.surprise(pixels)
    if not torch.isfinite(surprise).all():
        raise LeWMTrainingError(f"Non-finite LeWM probe score for {dataset_path}.")
    return {
        "dataset_path": str(dataset_path),
        "window_count": len(dataset),
        "pixels_shape": list(pixels.shape),
        "surprise_shape": list(surprise.shape),
        "surprise_mean": float(surprise.mean().item()),
        "finite": True,
        "action_mode": action_mode,
    }
