from __future__ import annotations

import io
import json
import re
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
from PIL import Image

from .manifest import ClipRecord
from .preprocess import IMAGE_EXTENSIONS

WOB_STEP_PATTERN = re.compile(r"^(?P<index>\d{8})\.npz$")


class LeWMDataUnavailableError(RuntimeError):
    """Raised when the optional stable-worldmodel data runtime is unavailable."""


@dataclass(frozen=True)
class LeWMEpisode:
    dataset_id: str
    source: str
    episode_id: str
    pixels: list[np.ndarray]
    action: np.ndarray
    label: str
    category: str
    split: str
    pair_id: str
    action_mode: str

    def __post_init__(self) -> None:
        if len(self.pixels) != len(self.action):
            raise ValueError("LeWM episode pixels and actions must have identical lengths.")
        if len(self.pixels) < 2:
            raise ValueError("LeWM episode requires at least two steps.")
        if self.action.ndim != 2:
            raise ValueError("LeWM episode actions must have shape (steps, action_dim).")

    def writer_payload(self) -> dict[str, Any]:
        count = len(self.pixels)
        return {
            "pixels": self.pixels,
            "action": [row for row in self.action.astype(np.float32)],
            "dataset_id": [self.dataset_id] * count,
            "source": [self.source] * count,
            "source_episode_id": [self.episode_id] * count,
            "label": [self.label] * count,
            "category": [self.category] * count,
            "split": [self.split] * count,
            "pair_id": [self.pair_id] * count,
            "action_mode": [self.action_mode] * count,
        }


def _frame_paths(record: ClipRecord) -> list[Path]:
    root = Path(record.clip_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Missing clip directory: {root}")
    frames = sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if len(frames) < 2:
        raise ValueError(f"LeWM conversion requires at least two frames: {root}")
    return frames


def episode_from_clip(
    record: ClipRecord,
    *,
    dataset_id: str,
    category: str,
    label: str,
    split: str,
    pair_id: str,
    action_mode: str = "zero_action",
    actions: np.ndarray | None = None,
) -> LeWMEpisode:
    pixels: list[np.ndarray] = []
    for path in _frame_paths(record):
        with Image.open(path) as image:
            pixels.append(np.asarray(image.convert("RGB"), dtype=np.uint8))
    if action_mode == "real":
        if actions is None:
            raise ValueError("Real-action LeWM conversion requires synchronized actions.")
        action = np.asarray(actions, dtype=np.float32)
    elif action_mode == "zero_action":
        action = np.zeros((len(pixels), 1), dtype=np.float32)
    else:
        raise ValueError("Dataset conversion supports only real or zero_action modes.")
    return LeWMEpisode(
        dataset_id=dataset_id,
        source=record.source,
        episode_id=record.clip_id,
        pixels=pixels,
        action=action,
        label=label,
        category=category,
        split=split,
        pair_id=pair_id,
        action_mode=action_mode,
    )


def episode_from_wob_tar(
    path: Path,
    *,
    dataset_id: str,
    source: str,
    episode_id: str,
    category: str,
    label: str,
    split: str,
    pair_id: str,
    action_dim: int = 4,
    max_steps: int | None = None,
) -> LeWMEpisode:
    """Convert numeric WOB tar members without loading the optional pickled info field."""
    pixels: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    with tarfile.open(path, "r") as archive:
        indexed_members = []
        for member in archive.getmembers():
            match = WOB_STEP_PATTERN.match(Path(member.name).name)
            if member.isfile() and match:
                indexed_members.append((int(match.group("index")), member))
        indexed_members.sort(key=lambda item: item[0])
        if max_steps is not None:
            indexed_members = indexed_members[:max_steps]
        indices = [index for index, _ in indexed_members]
        expected_indices = list(range(indices[0], indices[0] + len(indices))) if indices else []
        if indices != expected_indices:
            raise ValueError(f"WOB episode {path} step indices are not contiguous.")
        for _, member in indexed_members:
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"Could not read WOB tar member {member.name}.")
            with np.load(io.BytesIO(extracted.read()), allow_pickle=False) as sample:
                state = sample["state"]
                action = int(sample["action"])
                if state.shape[0] != 3 or state.ndim != 3:
                    raise ValueError(f"WOB member {member.name} state must be CHW RGB.")
                if not 0 <= action < action_dim:
                    raise ValueError(
                        f"WOB member {member.name} action {action} exceeds action_dim={action_dim}."
                    )
                rgb = np.moveaxis(state, 0, -1)
                pixels.append(np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8))
                one_hot = np.zeros(action_dim, dtype=np.float32)
                one_hot[action] = 1.0
                actions.append(one_hot)
    return LeWMEpisode(
        dataset_id=dataset_id,
        source=source,
        episode_id=episode_id,
        pixels=pixels,
        action=np.stack(actions),
        label=label,
        category=category,
        split=split,
        pair_id=pair_id,
        action_mode="real",
    )


def episode_from_video(
    path: Path,
    *,
    dataset_id: str,
    source: str,
    episode_id: str,
    category: str,
    label: str,
    split: str,
    pair_id: str,
    frame_stride: int = 1,
    image_size: int | None = None,
    max_steps: int | None = None,
) -> LeWMEpisode:
    try:
        import cv2
    except ImportError as exc:
        raise LeWMDataUnavailableError("Video conversion requires opencv-python.") from exc
    if frame_stride < 1:
        raise ValueError("frame_stride must be positive.")
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {path}")
    pixels: list[np.ndarray] = []
    frame_index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_stride == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if image_size is not None:
                    rgb = cv2.resize(rgb, (image_size, image_size), interpolation=cv2.INTER_AREA)
                pixels.append(np.asarray(rgb, dtype=np.uint8))
                if max_steps is not None and len(pixels) >= max_steps:
                    break
            frame_index += 1
    finally:
        capture.release()
    return LeWMEpisode(
        dataset_id=dataset_id,
        source=source,
        episode_id=episode_id,
        pixels=pixels,
        action=np.zeros((len(pixels), 1), dtype=np.float32),
        label=label,
        category=category,
        split=split,
        pair_id=pair_id,
        action_mode="zero_action",
    )


def write_lance_dataset(
    episodes: Iterable[LeWMEpisode],
    output_path: Path,
    *,
    mode: str = "error",
    batch_size: int = 1,
    progress: Callable[[int], None] | None = None,
) -> Path:
    try:
        from stable_worldmodel.data import LanceWriter
    except ImportError as exc:
        raise LeWMDataUnavailableError(
            "Lance conversion requires the isolated LeWM runtime from requirements/lewm-runtime.txt."
        ) from exc
    if batch_size < 1:
        raise ValueError("batch_size must be positive.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written_episode_count = 0
    payload_batch: list[dict[str, Any]] = []
    with LanceWriter(output_path.resolve().as_posix(), mode=mode) as writer:
        for episode in episodes:
            payload_batch.append(episode.writer_payload())
            if len(payload_batch) < batch_size:
                continue
            writer.write_episodes(payload_batch)
            written_episode_count += len(payload_batch)
            if progress is not None:
                progress(written_episode_count)
            payload_batch = []
        if payload_batch:
            writer.write_episodes(payload_batch)
            written_episode_count += len(payload_batch)
            if progress is not None:
                progress(written_episode_count)
    if written_episode_count == 0:
        raise ValueError("Cannot write an empty LeWM dataset.")
    return output_path


def inspect_lance_dataset(
    path: Path,
    *,
    num_steps: int = 4,
    frameskip: int = 1,
) -> dict[str, Any]:
    try:
        import stable_worldmodel as swm
    except ImportError as exc:
        raise LeWMDataUnavailableError(
            "Dataset inspection requires the isolated LeWM runtime."
        ) from exc
    # LanceDataset's Windows path parser requires POSIX separators in stable-worldmodel 0.1.1.
    dataset = swm.data.LanceDataset(
        path=str(path.resolve().as_posix()),
        num_steps=num_steps,
        frameskip=frameskip,
        keys_to_load=["pixels", "action"],
    )
    if not len(dataset):
        raise ValueError("LeWM dataset contains no valid temporal windows.")
    sample = dataset[0]
    return {
        "path": str(path),
        "format": "lance",
        "window_count": len(dataset),
        "columns": dataset.column_names,
        "pixels_shape": list(sample["pixels"].shape),
        "pixels_dtype": str(sample["pixels"].dtype),
        "action_shape": list(sample["action"].shape),
        "action_dtype": str(sample["action"].dtype),
        "num_steps": num_steps,
        "frameskip": frameskip,
        "episode_boundary_policy": "writer-managed episode_idx; windows generated within episodes",
    }


def write_dataset_inspection(summary: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return output_path
