from __future__ import annotations

import csv
import gc
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .kaggle_automation import FingerprintBuilder
from .lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec, sha256_file
from .lewm_training import _preprocess_pixels

NORMAL_DATASET_NAME = "normal_validation"
BUGGY_DATASET_NAME = "buggy_probe"
MANIFEST_FIELDS = (
    "window_id",
    "dataset_name",
    "dataset_fingerprint",
    "dataset_window_index",
    "source",
    "source_episode_id",
    "pair_id",
    "category",
    "label",
    "split",
    "action_mode",
    "evaluation_role",
)
SCORE_FIELDS = (
    "window_id",
    "mse_t1",
    "mse_t2",
    "mse_t3",
    "l2_t1",
    "l2_t2",
    "l2_t3",
)
TRANSITION_SCORE_FIELDS = SCORE_FIELDS[1:]
METADATA_KEYS = (
    "source",
    "source_episode_id",
    "pair_id",
    "category",
    "label",
    "split",
    "action_mode",
)


def runtime_provenance(*, include_lewm: bool) -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    provenance = {
        "git_sha": completed.stdout.strip(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy_version": importlib.metadata.version("numpy"),
    }
    if include_lewm:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("LeWM provenance requires PyTorch.") from exc
        provenance["torch_version"] = torch.__version__
        for distribution, key in (
            ("stable-worldmodel", "stable_worldmodel_version"),
            ("pylance", "lance_version"),
        ):
            try:
                provenance[key] = importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:
                provenance[key] = "unknown"
    return provenance


def select_calibration_episodes(
    episodes: Iterable[str],
    *,
    count: int = 2,
    seed: int = 42,
) -> tuple[str, ...]:
    unique = sorted(set(episodes))
    if len(unique) < count:
        raise ValueError(f"Need at least {count} normal episodes for threshold calibration.")

    def key(episode: str) -> str:
        return hashlib.sha256(f"{seed}:{episode}".encode()).hexdigest()

    return tuple(sorted(unique, key=key)[:count])


def canonical_row_from_sample(
    *,
    dataset_name: str,
    dataset_fingerprint: str,
    index: int,
    sample: dict[str, Any],
    calibration_episodes: set[str],
) -> dict[str, str]:
    label = str(sample["label"])
    episode = str(sample["source_episode_id"])
    role = (
        "calibration_normal"
        if label.lower() == "normal" and episode in calibration_episodes
        else "evaluation"
    )
    return {
        "window_id": f"{dataset_name}:{index:08d}",
        "dataset_name": dataset_name,
        "dataset_fingerprint": dataset_fingerprint,
        "dataset_window_index": str(index),
        "source": str(sample["source"]),
        "source_episode_id": episode,
        "pair_id": str(sample["pair_id"]),
        "category": str(sample["category"]),
        "label": label,
        "split": str(sample["split"]),
        "action_mode": str(sample["action_mode"]),
        "evaluation_role": role,
    }


def canonical_rows_from_samples(
    *,
    dataset_name: str,
    dataset_fingerprint: str,
    samples: Sequence[dict[str, Any]],
    calibration_episodes: set[str],
) -> list[dict[str, str]]:
    return [
        canonical_row_from_sample(
            dataset_name=dataset_name,
            dataset_fingerprint=dataset_fingerprint,
            index=index,
            sample=sample,
            calibration_episodes=calibration_episodes,
        )
        for index, sample in enumerate(samples)
    ]


def validate_manifest_rows(
    rows: Sequence[dict[str, str]],
    *,
    expected_calibration_episode_count: int = 2,
) -> None:
    if not rows:
        raise ValueError("Canonical Gate 7 manifest is empty.")
    seen_window_ids: set[str] = set()
    calibration_episodes: set[str] = set()
    for row in rows:
        validate_manifest_row(row, seen_window_ids=seen_window_ids)
        if row["evaluation_role"] == "calibration_normal":
            calibration_episodes.add(row["source_episode_id"])
    validate_calibration_episode_count(
        calibration_episodes,
        expected_calibration_episode_count=expected_calibration_episode_count,
    )


def validate_manifest_row(row: dict[str, str], *, seen_window_ids: set[str]) -> None:
    """Validate a single manifest row and track duplicate window_ids in place.

    Mutates ``seen_window_ids`` so callers can stream rows one at a time while
    still enforcing the global uniqueness invariant.
    """
    window_id = row["window_id"]
    if window_id in seen_window_ids:
        raise ValueError("Canonical Gate 7 manifest contains duplicate window_id values.")
    seen_window_ids.add(window_id)
    split = row["split"].lower()
    if "locked" in split or split == "test":
        raise ValueError("Canonical Gate 7 manifest must not contain locked-test rows.")
    label = row["label"].lower()
    role = row["evaluation_role"]
    if label not in {"normal", "buggy"}:
        raise ValueError(f"Unsupported Gate 7 label: {row['label']}")
    if label == "buggy" and role != "evaluation":
        raise ValueError("Buggy rows must not be used for threshold calibration.")
    if role not in {"calibration_normal", "evaluation"}:
        raise ValueError(f"Unsupported Gate 7 evaluation role: {role}")


def validate_calibration_episode_count(
    calibration_episodes: set[str],
    *,
    expected_calibration_episode_count: int,
) -> None:
    if len(calibration_episodes) != expected_calibration_episode_count:
        raise ValueError(
            "Canonical Gate 7 manifest has an invalid calibration episode count: "
            f"{len(calibration_episodes)}."
        )


def validate_score_alignment(
    manifest_rows: Sequence[dict[str, str]],
    score_rows: Sequence[dict[str, str]],
) -> None:
    expected_ids = [row["window_id"] for row in manifest_rows]
    actual_ids = [row["window_id"] for row in score_rows]
    if expected_ids != actual_ids:
        raise ValueError("Score rows must match the canonical manifest in exact ordered form.")
    for row in score_rows:
        for field in TRANSITION_SCORE_FIELDS:
            if field not in row or not math.isfinite(float(row[field])):
                raise ValueError(f"Gate 7 score field {field} must be finite.")


def write_csv_rows(
    path: Path,
    rows: Sequence[dict[str, Any]],
    fieldnames: Sequence[str],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _lance_dataset(path: Path, *, include_metadata: bool, metadata_only: bool = False) -> Any:
    try:
        import stable_worldmodel as swm
    except ImportError as exc:
        raise RuntimeError("Gate 7 Lance evaluation requires the isolated LeWM runtime.") from exc
    if metadata_only:
        keys = list(METADATA_KEYS)
    else:
        keys = ["pixels", "action"]
        if include_metadata:
            keys.extend(METADATA_KEYS)
    return swm.data.LanceDataset(
        path=path.resolve().as_posix(),
        num_steps=4,
        frameskip=1,
        keys_to_load=keys,
    )


def open_metadata_dataset(path: Path) -> tuple[Any, bool]:
    """Open a LanceDataset that loads only metadata columns when supported.

    Returns ``(dataset, metadata_only)``. The primary path requests a
    metadata-only ``keys_to_load`` so the ``pixels``/``action`` image tensors
    are never decoded while a window manifest is built. If the isolated runtime
    rejects a metadata-only load, it falls back to the full ``keys_to_load``
    (pixels + action + metadata).

    Both paths go through ``swm.data.LanceDataset`` on purpose: ``window_id`` and
    ``dataset_window_index`` are defined by the ``num_steps``/``frameskip``
    windowing and must match ``_score_dataset``. A native ``lance`` column scan
    would iterate raw rows, which do not align with that windowing, so it is not
    used here.
    """
    try:
        dataset = _lance_dataset(path, include_metadata=True, metadata_only=True)
        if len(dataset) > 0:
            probe = dataset[0]
            for key in METADATA_KEYS:
                _ = probe[key]
        return dataset, True
    except RuntimeError:
        raise
    except Exception:
        return _lance_dataset(path, include_metadata=True), False


def iter_metadata_samples(dataset: Any) -> Iterable[dict[str, str]]:
    """Yield metadata-only samples, reading each window exactly once."""
    for index in range(len(dataset)):
        sample = dataset[index]
        yield {key: str(sample[key]) for key in METADATA_KEYS}


def _metadata_samples(dataset: Any) -> list[dict[str, str]]:
    return list(iter_metadata_samples(dataset))


def capture_resource_usage() -> dict[str, Any]:
    """Return a bounded RSS snapshot, degrading gracefully without psutil."""
    try:
        import psutil
    except ImportError:
        import resource

        max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {"source": "resource.getrusage", "max_rss_kib": int(max_rss)}
    return {"source": "psutil", "rss_bytes": int(psutil.Process().memory_info().rss)}


class ResourceTelemetry:
    """Collect bounded RSS snapshots at named checkpoints and persist them."""

    def __init__(self, phase: str) -> None:
        self.phase = phase
        self.checkpoints: list[dict[str, Any]] = []

    def record(self, checkpoint: str, **fields: Any) -> None:
        snapshot = capture_resource_usage()
        snapshot["checkpoint"] = checkpoint
        snapshot["timestamp"] = datetime.now(timezone.utc).isoformat()
        snapshot.update(fields)
        self.checkpoints.append(snapshot)

    def to_dict(self) -> dict[str, Any]:
        return {"phase": self.phase, "checkpoints": self.checkpoints}

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path


def build_canonical_manifest(
    normal_lance: Path,
    buggy_lance: Path,
    *,
    seed: int = 42,
    calibration_episode_count: int = 2,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    normal_dataset, _normal_metadata_only = open_metadata_dataset(normal_lance)
    try:
        normal_samples = _metadata_samples(normal_dataset)
    finally:
        del normal_dataset
        gc.collect()
    calibration = set(
        select_calibration_episodes(
            (sample["source_episode_id"] for sample in normal_samples),
            count=calibration_episode_count,
            seed=seed,
        )
    )
    fingerprints = {
        NORMAL_DATASET_NAME: FingerprintBuilder.inventory_sha256(normal_lance),
        BUGGY_DATASET_NAME: FingerprintBuilder.inventory_sha256(buggy_lance),
    }
    rows = canonical_rows_from_samples(
        dataset_name=NORMAL_DATASET_NAME,
        dataset_fingerprint=fingerprints[NORMAL_DATASET_NAME],
        samples=normal_samples,
        calibration_episodes=calibration,
    )
    del normal_samples
    gc.collect()
    buggy_dataset, _buggy_metadata_only = open_metadata_dataset(buggy_lance)
    try:
        buggy_samples = _metadata_samples(buggy_dataset)
    finally:
        del buggy_dataset
        gc.collect()
    rows.extend(
        canonical_rows_from_samples(
            dataset_name=BUGGY_DATASET_NAME,
            dataset_fingerprint=fingerprints[BUGGY_DATASET_NAME],
            samples=buggy_samples,
            calibration_episodes=calibration,
        )
    )
    del buggy_samples
    gc.collect()
    validate_manifest_rows(
        rows,
        expected_calibration_episode_count=calibration_episode_count,
    )
    return rows, fingerprints


def _score_dataset(
    dataset_path: Path,
    window_ids: Sequence[str],
    adapter: LeWMAdapter,
    *,
    batch_size: int,
    device: str,
) -> list[dict[str, str]]:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("Gate 7 scoring requires PyTorch in the isolated runtime.") from exc
    dataset = _lance_dataset(dataset_path, include_metadata=False)
    if len(dataset) != len(window_ids):
        raise ValueError("Lance window count does not match the canonical manifest.")
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    rows: list[dict[str, str]] = []
    offset = 0
    resolved_device = torch.device(device)
    for batch in loader:
        pixels = _preprocess_pixels(
            torch,
            batch["pixels"],
            adapter.image_size,
            resolved_device,
        )
        mse = adapter.surprise(pixels, batch.get("action"), distance="mse")
        l2 = adapter.surprise(pixels, batch.get("action"), distance="l2")
        mse_values = mse.detach().cpu().numpy()
        l2_values = l2.detach().cpu().numpy()
        for batch_index in range(len(mse_values)):
            values = [*mse_values[batch_index].tolist(), *l2_values[batch_index].tolist()]
            if len(values) != 6 or not all(math.isfinite(float(value)) for value in values):
                raise ValueError("LeWM produced non-finite or malformed transition scores.")
            rows.append(
                {
                    "window_id": window_ids[offset + batch_index],
                    **{
                        field: f"{float(value):.12g}"
                        for field, value in zip(TRANSITION_SCORE_FIELDS, values)
                    },
                }
            )
        offset += len(mse_values)
    return rows


def run_gate7_scoring(
    *,
    checkpoint: Path,
    config: Path,
    normal_lance: Path,
    buggy_lance: Path,
    output_dir: Path,
    expected_sha256: str,
    device: str = "cpu",
    batch_size: int = 16,
    seed: int = 42,
) -> dict[str, Any]:
    manifest_rows, fingerprints = build_canonical_manifest(
        normal_lance,
        buggy_lance,
        seed=seed,
    )
    adapter = LeWMAdapter(
        LeWMCheckpointSpec(
            weights_path=checkpoint,
            config_path=config,
            action_mode=ActionMode.ZERO_ACTION,
            expected_sha256=expected_sha256,
            device=device,
        )
    ).load()
    normal_ids = [
        row["window_id"] for row in manifest_rows if row["dataset_name"] == NORMAL_DATASET_NAME
    ]
    buggy_ids = [
        row["window_id"] for row in manifest_rows if row["dataset_name"] == BUGGY_DATASET_NAME
    ]
    score_rows = [
        *_score_dataset(
            normal_lance,
            normal_ids,
            adapter,
            batch_size=batch_size,
            device=device,
        ),
        *_score_dataset(
            buggy_lance,
            buggy_ids,
            adapter,
            batch_size=batch_size,
            device=device,
        ),
    ]
    validate_score_alignment(manifest_rows, score_rows)
    manifest_path = write_csv_rows(
        output_dir / "window_manifest.csv", manifest_rows, MANIFEST_FIELDS
    )
    scores_path = write_csv_rows(
        output_dir / "lewm_transition_scores.csv", score_rows, SCORE_FIELDS
    )
    calibration_episodes = sorted(
        {
            row["source_episode_id"]
            for row in manifest_rows
            if row["evaluation_role"] == "calibration_normal"
        }
    )
    metadata = {
        "status": "gate7_scored",
        "protocol": "nonlocked_window_level_pilot",
        "window_count": len(manifest_rows),
        "normal_window_count": len(normal_ids),
        "buggy_window_count": len(buggy_ids),
        "calibration_episode_ids": calibration_episodes,
        "dataset_fingerprints": fingerprints,
        "checkpoint_sha256": sha256_file(checkpoint),
        "config_sha256": sha256_file(config),
        "manifest_sha256": sha256_file(manifest_path),
        "scores_sha256": sha256_file(scores_path),
        "device": device,
        "batch_size": batch_size,
        "seed": seed,
        "environment": runtime_provenance(include_lewm=True),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    metadata_path = output_dir / "gate7_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadata_path"] = str(metadata_path)
    return metadata
