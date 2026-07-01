from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class LeWMIntegrationError(RuntimeError):
    """Raised when a LeWM runtime, checkpoint, or tensor contract is invalid."""


class ActionMode(str, Enum):
    REAL = "real"
    ZERO_ACTION = "zero_action"
    ACTION_FREE = "action_free"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class LeWMCheckpointSpec:
    weights_path: Path
    config_path: Path
    action_mode: ActionMode
    expected_sha256: str | None = None
    device: str = "cpu"


class LeWMAdapter:
    def __init__(self, spec: LeWMCheckpointSpec) -> None:
        self.spec = spec
        self.model: Any | None = None
        self.config: dict[str, Any] | None = None

    def _require_runtime(self) -> tuple[Any, Any]:
        try:
            import torch
            from hydra.utils import instantiate
        except ImportError as exc:
            raise LeWMIntegrationError(
                "LeWM requires the isolated Python 3.10 runtime from requirements/lewm-runtime.txt."
            ) from exc
        return torch, instantiate

    def load(self) -> LeWMAdapter:
        if not self.spec.weights_path.is_file() or not self.spec.config_path.is_file():
            raise LeWMIntegrationError(
                "LeWM checkpoint requires existing weights and config files."
            )
        actual_hash = sha256_file(self.spec.weights_path)
        if self.spec.expected_sha256 and actual_hash != self.spec.expected_sha256:
            raise LeWMIntegrationError(
                "LeWM checkpoint SHA-256 does not match expected provenance."
            )
        torch, instantiate = self._require_runtime()
        config = json.loads(self.spec.config_path.read_text(encoding="utf-8"))
        self._validate_config(config)
        model = instantiate(config)
        state_dict = torch.load(self.spec.weights_path, map_location="cpu", weights_only=True)
        try:
            model.load_state_dict(state_dict, strict=True)
        except RuntimeError as exc:
            raise LeWMIntegrationError(
                "Strict LeWM checkpoint loading failed; runtime/model versions are incompatible."
            ) from exc
        model = model.to(self.spec.device).eval()
        model.requires_grad_(False)
        self.model = model
        self.config = config
        return self

    def _validate_config(self, config: dict[str, Any]) -> None:
        required = {"encoder", "predictor", "action_encoder"}
        missing = sorted(required - set(config))
        if missing:
            raise LeWMIntegrationError(f"LeWM config missing required sections: {missing}")
        if self.spec.action_mode == ActionMode.ACTION_FREE:
            raise LeWMIntegrationError(
                "action_free is a declared method variant but is not implemented by official LeWM."
            )

    @property
    def history_size(self) -> int:
        if self.config is None:
            raise LeWMIntegrationError("Load LeWM before reading its contract.")
        return int(self.config["predictor"]["num_frames"])

    @property
    def image_size(self) -> int:
        if self.config is None:
            raise LeWMIntegrationError("Load LeWM before reading its contract.")
        return int(self.config["encoder"]["image_size"])

    @property
    def action_dim(self) -> int:
        if self.config is None:
            raise LeWMIntegrationError("Load LeWM before reading its contract.")
        return int(self.config["action_encoder"]["input_dim"])

    def prepare_actions(self, pixels: Any, actions: Any | None) -> Any:
        torch, _ = self._require_runtime()
        batch, steps = int(pixels.shape[0]), int(pixels.shape[1])
        if self.spec.action_mode == ActionMode.REAL:
            if actions is None:
                raise LeWMIntegrationError("Action-conditioned LeWM requires real actions.")
            if (
                tuple(actions.shape[:2]) != (batch, steps)
                or int(actions.shape[-1]) != self.action_dim
            ):
                raise LeWMIntegrationError(
                    "Real actions do not match LeWM batch/time/action dimensions."
                )
            return actions.to(self.spec.device)
        return torch.zeros((batch, steps, self.action_dim), device=self.spec.device)

    def surprise(
        self,
        pixels: Any,
        actions: Any | None = None,
        *,
        distance: str = "mse",
    ) -> Any:
        torch, _ = self._require_runtime()
        if self.model is None:
            raise LeWMIntegrationError("Load LeWM before inference.")
        expected_steps = self.history_size + 1
        if pixels.ndim != 5 or int(pixels.shape[1]) != expected_steps:
            raise LeWMIntegrationError(f"LeWM pixels must have shape (B,{expected_steps},C,H,W).")
        if tuple(pixels.shape[-2:]) != (self.image_size, self.image_size):
            raise LeWMIntegrationError("LeWM pixels do not match checkpoint image size.")
        prepared_actions = self.prepare_actions(pixels, actions)
        with torch.inference_mode():
            output = self.model.encode(
                {"pixels": pixels.to(self.spec.device), "action": prepared_actions}
            )
            context = output["emb"][:, : self.history_size]
            context_actions = output["act_emb"][:, : self.history_size]
            target = output["emb"][:, 1 : self.history_size + 1]
            predicted = self.model.predict(context, context_actions)
            error = predicted - target
            if distance == "mse":
                return error.pow(2).mean(dim=-1)
            if distance == "l2":
                return error.pow(2).sum(dim=-1).sqrt()
            if distance == "cosine_gap":
                # 1 - cosine_similarity(predicted, target).
                # Direction-sensitive: detects representational drift that
                # magnitude-only metrics (L2/MSE) miss when zero_action
                # inflates prediction error uniformly across normal and buggy
                # frames. Range: [0, 2], higher = more anomalous.
                pred_norm = predicted / predicted.norm(dim=-1, keepdim=True).clamp_min(1e-8)
                tgt_norm = target / target.norm(dim=-1, keepdim=True).clamp_min(1e-8)
                cosine_sim = (pred_norm * tgt_norm).sum(dim=-1)
                return 1.0 - cosine_sim
            raise LeWMIntegrationError(f"Unsupported LeWM surprise distance: {distance}")

    def audit(self) -> dict[str, Any]:
        if self.model is None or self.config is None:
            raise LeWMIntegrationError("Load LeWM before writing an audit.")
        torch, _ = self._require_runtime()
        return {
            "status": "checkpoint_load_verified",
            "weights_path": str(self.spec.weights_path),
            "config_path": str(self.spec.config_path),
            "checkpoint_sha256": sha256_file(self.spec.weights_path),
            "action_mode": self.spec.action_mode.value,
            "action_dim": self.action_dim,
            "history_size": self.history_size,
            "image_size": self.image_size,
            "device": self.spec.device,
            "torch_version": torch.__version__,
            "model_class": f"{type(self.model).__module__}.{type(self.model).__name__}",
            "parameter_count": sum(parameter.numel() for parameter in self.model.parameters()),
            "inference_verified": False,
            "training_verified": False,
            "locked_test_scored": False,
        }

    def inference_smoke(self) -> dict[str, Any]:
        torch, _ = self._require_runtime()
        pixels = torch.zeros(
            (1, self.history_size + 1, 3, self.image_size, self.image_size),
            dtype=torch.float32,
        )
        actions = (
            torch.zeros((1, self.history_size + 1, self.action_dim), dtype=torch.float32)
            if self.spec.action_mode == ActionMode.REAL
            else None
        )
        surprise = self.surprise(pixels, actions)
        return {
            "inference_verified": True,
            "pixels_shape": list(pixels.shape),
            "actions_shape": list(actions.shape) if actions is not None else None,
            "surprise_shape": list(surprise.shape),
            "surprise_finite": bool(torch.isfinite(surprise).all().item()),
            "surprise_mean": float(surprise.mean().item()),
        }
