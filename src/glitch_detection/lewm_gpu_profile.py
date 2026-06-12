from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .kaggle_automation import FingerprintBuilder

PROFILE_REQUIRED_REMOTE_ARTIFACTS = (
    "PROFILE_REPORT.md",
    "profile_metadata.json",
    "environment_snapshot.json",
    "checkpoint_hashes.json",
    "retry_history.json",
    "checkpoint.pt",
    "profile.log",
)
FORBIDDEN_PROFILE_TERMS = (
    "auroc",
    "auprc",
    "validation_buggy",
    "validation-buggy",
    "locked_test",
    "locked-test",
    "detection_performance",
    "paper_claim",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class LeWMGPUProfileConfig:
    batch_size: int
    optimizer_updates: int = 500
    validation_batches: int = 8
    seed: int = 42
    image_size: int = 112
    amp: bool = False
    num_workers: int = 2
    pin_memory: bool = True
    gradient_clip_norm: float | None = None
    validation_only: bool = True
    locked_test_materialized: bool = False
    locked_test_scored: bool = False
    evidence_class: str = "engineering-profile-only"

    def __post_init__(self) -> None:
        if self.batch_size not in {8, 6, 4, 2}:
            raise ValueError("Profile batch_size must follow the approved 8, 6, 4, 2 ladder.")
        if self.optimizer_updates != 500 or self.validation_batches != 8:
            raise ValueError("Profile requires exactly 500 updates and eight validation batches.")
        if not self.validation_only or self.locked_test_materialized or self.locked_test_scored:
            raise ValueError("Profile must remain validation-only with locked test disabled.")
        if self.image_size < 28 or self.image_size % 14:
            raise ValueError("Profile image_size must be divisible by 14.")

    @property
    def config_hash(self) -> str:
        return canonical_sha256(asdict(self))


def build_dataset_manifest(train_path: Path, validation_path: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for split, root in (
        ("train_normal", train_path),
        ("validation_normal", validation_path),
    ):
        if not root.is_dir():
            raise FileNotFoundError(f"Missing profile dataset: {root}")
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            files.append(
                {
                    "split": split,
                    "path": path.relative_to(root).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": FingerprintBuilder.sha256_file(path),
                }
            )
    return {
        "files": files,
        "dataset_manifest_hash": canonical_sha256(files),
        "train_dataset_hash": FingerprintBuilder.inventory_sha256(train_path),
        "validation_dataset_hash": FingerprintBuilder.inventory_sha256(validation_path),
    }


def build_profile_fingerprint(payload: dict[str, Any]) -> str:
    required = {
        "git_sha",
        "dataset_manifest_hash",
        "train_dataset_hash",
        "validation_dataset_hash",
        "config_hash",
        "batch_size",
        "amp",
    }
    if set(payload) != required:
        raise ValueError(f"Profile fingerprint payload must contain exactly {sorted(required)}.")
    return canonical_sha256(payload)


def run_exact_updates(
    *,
    target_updates: int,
    train_step: Callable[[int], dict[str, float]],
    on_update: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    started = time.perf_counter()
    for update in range(1, target_updates + 1):
        metrics = {"update": update, **train_step(update)}
        values = [float(value) for key, value in metrics.items() if key != "update"]
        if not values or not all(math.isfinite(value) for value in values):
            raise ValueError(f"Profile update {update} produced non-finite metrics.")
        history.append(metrics)
        if on_update is not None:
            on_update(update)
    elapsed = max(time.perf_counter() - started, 1e-12)
    return {
        "updates_completed": len(history),
        "history": history,
        "training_runtime_seconds": elapsed,
        "updates_per_second": len(history) / elapsed,
    }


def build_checkpoint_payload(
    *,
    model_state: Any,
    optimizer_state: Any,
    scheduler_state: Any | None,
    global_step: int,
    config_hash: str,
    dataset_hashes: dict[str, str],
) -> dict[str, Any]:
    return {
        "model": model_state,
        "optimizer": optimizer_state,
        "scheduler": scheduler_state,
        "scheduler_present": scheduler_state is not None,
        "global_step": global_step,
        "config_hash": config_hash,
        "dataset_hashes": dataset_hashes,
    }


def verify_reloaded_checkpoint(
    checkpoint: dict[str, Any],
    *,
    expected_step: int,
    expected_config_hash: str,
    expected_dataset_hashes: dict[str, str],
) -> dict[str, Any]:
    if int(checkpoint.get("global_step", -1)) != expected_step:
        raise ValueError("Reloaded checkpoint global step does not match expected value.")
    if checkpoint.get("config_hash") != expected_config_hash:
        raise ValueError("Reloaded checkpoint config hash mismatch.")
    if checkpoint.get("dataset_hashes") != expected_dataset_hashes:
        raise ValueError("Reloaded checkpoint dataset hashes mismatch.")
    for name in ("model", "optimizer"):
        if name not in checkpoint:
            raise ValueError(f"Reloaded checkpoint is missing {name} state.")
    return {
        "weights_reload_verified": True,
        "optimizer_reload_verified": True,
        "scheduler": {
            "present": bool(checkpoint.get("scheduler_present")),
            "reload_verified": True,
        },
        "reloaded_global_step": expected_step,
    }


def environment_snapshot(torch: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.version,
        "platform": platform.platform(),
        "kaggle_runtime": {
            "is_kaggle": Path("/kaggle").exists(),
            "input_root": "/kaggle/input",
            "working_root": "/kaggle/working",
        },
    }
    if torch is not None:
        payload.update(
            {
                "pytorch": torch.__version__,
                "cuda_version": torch.version.cuda,
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device": (
                    torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
                ),
            }
        )
    return payload


def _contains_forbidden(payload: Any) -> str | None:
    text = json.dumps(payload, sort_keys=True).lower()
    return next((term for term in FORBIDDEN_PROFILE_TERMS if term in text), None)


def write_artifact_manifest(root: Path) -> dict[str, Any]:
    files = {}
    for name in PROFILE_REQUIRED_REMOTE_ARTIFACTS:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing profile artifact before manifest: {name}")
        files[name] = {
            "size": path.stat().st_size,
            "sha256": FingerprintBuilder.sha256_file(path),
        }
    payload = {"created_at": _utc_now(), "files": files}
    _write_json(root / "artifact_manifest.json", payload)
    return payload


def write_profile_artifacts(
    root: Path,
    *,
    metadata: dict[str, Any],
    environment: dict[str, Any],
    retry_history: dict[str, Any],
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _write_json(root / "profile_metadata.json", metadata)
    _write_json(root / "environment_snapshot.json", environment)
    _write_json(root / "checkpoint_hashes.json", metadata["checkpoint"])
    _write_json(root / "retry_history.json", retry_history)
    report = (
        "# LeWM 500-Update GPU Profile\n\n"
        "Evidence class: engineering-profile-only\n\n"
        "This profile reports engineering runtime, VRAM, throughput, and checkpoint integrity "
        "only. No model-performance or scientific conclusion is permitted.\n"
    )
    (root / "PROFILE_REPORT.md").write_text(report, encoding="utf-8")
    (root / "profile.log").touch(exist_ok=True)
    write_artifact_manifest(root)


def run_lewm_gpu_profile(
    train_path: Path,
    validation_path: Path,
    output_root: Path,
    config: LeWMGPUProfileConfig,
    *,
    preflight_metadata: dict[str, Any],
) -> dict[str, Any]:
    from .lewm_training import (
        LeWMTrainConfig,
        _dataset,
        _preprocess_pixels,
        _require_runtime,
        _sigreg,
        build_model_config,
    )

    torch, instantiate = _require_runtime()
    if not torch.cuda.is_available():
        raise RuntimeError("LeWM GPU profile requires CUDA.")
    device = torch.device("cuda")
    train_config = LeWMTrainConfig(
        image_size=config.image_size,
        batch_size=config.batch_size,
        epochs=1,
        seed=config.seed,
        run_kind="research",
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
        mixed_precision=config.amp,
        gradient_clip_norm=config.gradient_clip_norm,
    )
    manifest = build_dataset_manifest(train_path, validation_path)
    dataset_hashes = {
        "train": manifest["train_dataset_hash"],
        "validation": manifest["validation_dataset_hash"],
    }
    train_dataset = _dataset(train_path, train_config)
    validation_dataset = _dataset(validation_path, train_config)
    action_dim = int(train_dataset.get_dim("action"))
    if int(validation_dataset.get_dim("action")) != action_dim:
        raise RuntimeError("Profile train and validation action dimensions differ.")
    model_config = build_model_config(train_config, action_dim)
    model = instantiate(model_config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=train_config.learning_rate, weight_decay=train_config.weight_decay
    )
    scaler = torch.amp.GradScaler("cuda", enabled=config.amp)
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
    output_root.mkdir(parents=True, exist_ok=True)
    log_path = output_root / "profile.log"
    log_path.write_text("", encoding="utf-8")
    memory_samples: list[int] = []
    train_batches = iter(train_loader)
    torch.cuda.reset_peak_memory_stats()
    wall_started = time.perf_counter()
    training_started_at = _utc_now()

    def train_step(_update: int) -> dict[str, float]:
        nonlocal train_batches
        try:
            batch = next(train_batches)
        except StopIteration:
            train_batches = iter(train_loader)
            batch = next(train_batches)
        model.train(True)
        pixels = _preprocess_pixels(torch, batch["pixels"], config.image_size, device)
        actions = torch.nan_to_num(batch["action"].to(device), 0.0)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(device_type="cuda", enabled=config.amp):
            output = model.encode({"pixels": pixels, "action": actions})
            embeddings = output["emb"]
            predicted = model.predict(
                embeddings[:, : train_config.history_size],
                output["act_emb"][:, : train_config.history_size],
            )
            target = embeddings[:, 1 : train_config.history_size + 1]
            prediction_loss = (predicted - target).pow(2).mean()
            sigreg_loss = _sigreg(torch, embeddings, train_config.sigreg_projections)
            loss = prediction_loss + train_config.sigreg_weight * sigreg_loss
        if scaler.is_enabled():
            scaler.scale(loss).backward()
            if config.gradient_clip_norm is not None:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip_norm)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            if config.gradient_clip_norm is not None:
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip_norm)
            optimizer.step()
        memory_samples.append(int(torch.cuda.memory_allocated()))
        return {
            "loss": float(loss.detach().cpu()),
            "prediction_loss": float(prediction_loss.detach().cpu()),
            "sigreg_loss": float(sigreg_loss.detach().cpu()),
        }

    training = run_exact_updates(target_updates=500, train_step=train_step)
    training_ended_at = _utc_now()
    checkpoint_path = output_root / "checkpoint.pt"
    checkpoint_saved_at = _utc_now()
    checkpoint = build_checkpoint_payload(
        model_state=model.state_dict(),
        optimizer_state=optimizer.state_dict(),
        scheduler_state=None,
        global_step=training["updates_completed"],
        config_hash=config.config_hash,
        dataset_hashes=dataset_hashes,
    )
    torch.save(checkpoint, checkpoint_path)
    reloaded = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    fresh_model = instantiate(model_config)
    fresh_optimizer = torch.optim.AdamW(
        fresh_model.parameters(),
        lr=train_config.learning_rate,
        weight_decay=train_config.weight_decay,
    )
    fresh_model.load_state_dict(reloaded["model"], strict=True)
    fresh_optimizer.load_state_dict(reloaded["optimizer"])
    checkpoint_reload = verify_reloaded_checkpoint(
        reloaded,
        expected_step=500,
        expected_config_hash=config.config_hash,
        expected_dataset_hashes=dataset_hashes,
    )
    checkpoint_reloaded_at = _utc_now()
    fresh_model = fresh_model.to(device)
    fresh_model.eval()
    validation_history = []
    with torch.no_grad():
        for index, batch in enumerate(validation_loader):
            if index >= 8:
                break
            pixels = _preprocess_pixels(torch, batch["pixels"], config.image_size, device)
            actions = torch.nan_to_num(batch["action"].to(device), 0.0)
            with torch.autocast(device_type="cuda", enabled=config.amp):
                output = fresh_model.encode({"pixels": pixels, "action": actions})
                embeddings = output["emb"]
                predicted = fresh_model.predict(
                    embeddings[:, : train_config.history_size],
                    output["act_emb"][:, : train_config.history_size],
                )
                target = embeddings[:, 1 : train_config.history_size + 1]
                loss = (predicted - target).pow(2).mean()
            value = float(loss.detach().cpu())
            if not math.isfinite(value):
                raise RuntimeError("Profile validation verification produced non-finite loss.")
            validation_history.append({"batch": index + 1, "loss": value})
    if len(validation_history) != 8:
        raise RuntimeError("Profile validation dataset yielded fewer than eight batches.")
    wall_elapsed = max(time.perf_counter() - wall_started, 1e-12)
    metadata = {
        "evidence_class": "engineering-profile-only",
        "fingerprint": preflight_metadata["fingerprint"],
        "git_sha": preflight_metadata["git_sha"],
        "branch": preflight_metadata["branch"],
        "dataset_manifest_hash": manifest["dataset_manifest_hash"],
        "dataset_hashes": dataset_hashes,
        "config_hash": config.config_hash,
        "device": "cuda",
        "batch_size": config.batch_size,
        "amp": config.amp,
        "updates_completed": training["updates_completed"],
        "validation_batches_completed": len(validation_history),
        "training_started_at": training_started_at,
        "training_ended_at": training_ended_at,
        "checkpoint_saved_at": checkpoint_saved_at,
        "checkpoint_reloaded_at": checkpoint_reloaded_at,
        "wall_clock_runtime_seconds": wall_elapsed,
        "training_runtime_seconds": training["training_runtime_seconds"],
        "updates_per_second": training["updates_per_second"],
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "average_vram_bytes": sum(memory_samples) / len(memory_samples),
        "finite_loss": True,
        "checkpoint_reload": checkpoint_reload,
        "checkpoint": {
            "checkpoint_sha256": FingerprintBuilder.sha256_file(checkpoint_path),
            "save_verified": True,
        },
        "validation_verification": validation_history,
    }
    _write_json(output_root / "loss_history.json", training["history"])
    write_profile_artifacts(
        output_root,
        metadata=metadata,
        environment=environment_snapshot(torch),
        retry_history={"attempts": preflight_metadata.get("attempts", [])},
    )
    return metadata


def validate_lewm_gpu_profile_artifacts(root: Path) -> dict[str, Any]:
    required = (*PROFILE_REQUIRED_REMOTE_ARTIFACTS, "artifact_manifest.json")
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing LeWM GPU profile artifacts: {', '.join(missing)}")
    metadata = json.loads((root / "profile_metadata.json").read_text(encoding="utf-8-sig"))
    environment = json.loads((root / "environment_snapshot.json").read_text(encoding="utf-8-sig"))
    hashes = json.loads((root / "checkpoint_hashes.json").read_text(encoding="utf-8-sig"))
    retries = json.loads((root / "retry_history.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((root / "artifact_manifest.json").read_text(encoding="utf-8-sig"))
    forbidden = _contains_forbidden(
        {
            "metadata": metadata,
            "environment": environment,
            "hashes": hashes,
            "retries": retries,
        }
    )
    if forbidden:
        raise ValueError(f"Profile artifacts contain forbidden performance/test term: {forbidden}")
    if metadata.get("evidence_class") != "engineering-profile-only":
        raise ValueError("Profile evidence class is not engineering-profile-only.")
    if (
        metadata.get("updates_completed") != 500
        or metadata.get("validation_batches_completed") != 8
    ):
        raise ValueError(
            "Profile did not complete exactly 500 updates and eight validation batches."
        )
    if environment.get("cuda_available") is not True or metadata.get("device") != "cuda":
        raise ValueError("Profile artifacts do not prove CUDA execution.")
    for key in ("wall_clock_runtime_seconds", "updates_per_second", "peak_vram_bytes"):
        value = metadata.get(key)
        if not isinstance(value, int | float) or not math.isfinite(float(value)) or value <= 0:
            raise ValueError(f"Profile metadata has invalid {key}.")
    reload_proof = metadata.get("checkpoint_reload", {})
    required_reload = (
        "weights_reload_verified",
        "optimizer_reload_verified",
    )
    if not all(reload_proof.get(key) is True for key in required_reload):
        raise ValueError("Profile checkpoint state reload was not verified.")
    if reload_proof.get("reloaded_global_step") != 500:
        raise ValueError("Profile checkpoint reload step is not 500.")
    if reload_proof.get("scheduler", {}).get("reload_verified") is not True:
        raise ValueError("Profile scheduler presence/absence was not verified.")
    checkpoint_hash = FingerprintBuilder.sha256_file(root / "checkpoint.pt")
    if hashes.get("checkpoint_sha256") != checkpoint_hash:
        raise ValueError("Profile checkpoint hash mismatch.")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file() or FingerprintBuilder.sha256_file(path) != expected.get("sha256"):
            raise ValueError(f"Profile artifact hash mismatch: {name}")
    return {
        "status": "lewm_gpu_profile_validated",
        "fingerprint": metadata["fingerprint"],
        "updates_completed": 500,
        "validation_batches_completed": 8,
        "checkpoint_sha256": checkpoint_hash,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
