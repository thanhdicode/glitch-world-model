from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec, LeWMIntegrationError
from .lewm_latent import (
    LeWMUnavailableError,
    _load_pixels,
    _require_torch,
    resolve_checkpoint,
    resolve_config,
)
from .manifest import ClipRecord, read_manifest


def aggregate_scores(values: Iterable[float], aggregation: str) -> float:
    array = np.asarray(list(values), dtype=np.float64)
    if not len(array):
        raise ValueError("Cannot aggregate an empty LeWM surprise series.")
    if not np.isfinite(array).all():
        raise ValueError("LeWM surprise series contains non-finite values.")
    if aggregation == "mean":
        return float(array.mean())
    if aggregation == "max":
        return float(array.max())
    if aggregation == "topk_mean":
        count = min(3, len(array))
        return float(np.partition(array, len(array) - count)[-count:].mean())
    if aggregation == "top2_mean":
        count = min(2, len(array))
        return float(np.partition(array, len(array) - count)[-count:].mean())
    if aggregation == "percentile95":
        return float(np.percentile(array, 95))
    if aggregation == "max_plus_std":
        # Peak surprise plus dispersion: sensitive to both short spikes and
        # sustained variance in the per-window surprise series.
        return float(array.max() + 0.5 * array.std())
    raise ValueError(f"Unknown LeWM surprise aggregation: {aggregation}")


def score_direction_check(values: Iterable[float]) -> dict[str, Any]:
    array = np.asarray(list(values), dtype=np.float64)
    if not len(array) or not np.isfinite(array).all():
        raise ValueError("Score direction check requires finite non-empty scores.")
    return {
        "higher_is_more_anomalous": True,
        "finite": True,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "range": float(array.max() - array.min()),
    }


def score_record_series(adapter: LeWMAdapter, record: ClipRecord) -> list[float]:
    torch = _require_torch()
    pixels = _load_pixels(record, adapter.image_size)
    window_size = adapter.history_size + 1
    if len(pixels) < window_size:
        raise ValueError(f"LeWM scoring requires at least {window_size} frames: {record.clip_id}")
    windows = torch.stack(
        [pixels[start : start + window_size] for start in range(len(pixels) - window_size + 1)]
    )
    surprise = adapter.surprise(windows, distance="l2")
    values = surprise.mean(dim=-1).detach().cpu().numpy().astype(float).tolist()
    if not np.isfinite(values).all():
        raise ValueError(f"LeWM produced non-finite scores for {record.clip_id}.")
    return values


def score_record(adapter: LeWMAdapter, record: ClipRecord, aggregation: str = "mean") -> float:
    return aggregate_scores(score_record_series(adapter, record), aggregation)


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    torch = _require_torch()
    return "cuda" if torch.cuda.is_available() else "cpu"


def score_manifest(
    manifest_path: Path,
    labels_path: Path | None,
    output_path: Path,
    checkpoint: Path | None = None,
    config: Path | None = None,
    action_mode: str = "zero_action",
    device: str = "cpu",
    aggregation: str = "mean",
    expected_sha256: str | None = None,
) -> Path:
    _ = labels_path
    checkpoint_path = resolve_checkpoint(checkpoint)
    config_path = resolve_config(config, checkpoint_path)
    if action_mode == "real":
        raise LeWMUnavailableError(
            "real action mode requires a synchronized action source; manifest-only scoring "
            "supports zero_action."
        )
    try:
        adapter = LeWMAdapter(
            LeWMCheckpointSpec(
                weights_path=checkpoint_path,
                config_path=config_path,
                action_mode=ActionMode(action_mode),
                expected_sha256=expected_sha256,
                device=_resolve_device(device),
            )
        ).load()
    except (ValueError, LeWMIntegrationError) as exc:
        raise LeWMUnavailableError(str(exc)) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        for record in read_manifest(manifest_path):
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "score": f"{score_record(adapter, record, aggregation):.8f}",
                }
            )
    return output_path


def registered_score_manifest(
    manifest_path: Path, labels_path: Path | None, output_path: Path
) -> Path:
    return score_manifest(
        manifest_path,
        labels_path,
        output_path,
        checkpoint=Path(os.environ["LEWM_CHECKPOINT"]) if "LEWM_CHECKPOINT" in os.environ else None,
        config=Path(os.environ["LEWM_CONFIG"]) if "LEWM_CONFIG" in os.environ else None,
        action_mode=os.environ.get("LEWM_ACTION_MODE", "zero_action"),
        device=os.environ.get("LEWM_DEVICE", "cpu"),
        aggregation=os.environ.get("LEWM_AGGREGATION", "mean"),
        expected_sha256=os.environ.get("LEWM_EXPECTED_SHA256"),
    )
