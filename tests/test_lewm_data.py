import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image

from glitch_detection.lewm_data import LeWMEpisode, episode_from_clip, write_lance_dataset
from glitch_detection.manifest import ClipRecord


def test_zero_action_episode_from_clip_preserves_steps(tmp_path: Path):
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir()
    for index in range(4):
        Image.new("RGB", (8, 8), (index, index, index)).save(clip_dir / f"{index:06d}.png")
    record = ClipRecord("clip-1", "source-1", str(clip_dir), 0, 3, 4, 30.0)

    episode = episode_from_clip(
        record,
        dataset_id="tempglitch",
        category="Velocity",
        label="Normal",
        split="train",
        pair_id="pair-1",
    )

    assert isinstance(episode, LeWMEpisode)
    assert len(episode.pixels) == 4
    assert episode.action.shape == (4, 1)
    assert np.all(episode.action == 0)
    assert episode.writer_payload()["action_mode"] == ["zero_action"] * 4


def test_real_action_episode_rejects_length_mismatch(tmp_path: Path):
    pixels = [np.zeros((8, 8, 3), dtype=np.uint8)] * 4
    try:
        LeWMEpisode(
            "wob",
            "source",
            "episode",
            pixels,
            np.zeros((3, 2), dtype=np.float32),
            "Buggy",
            "bug",
            "validation",
            "episode",
            "real",
        )
    except ValueError as exc:
        assert "identical lengths" in str(exc)
    else:
        raise AssertionError("Expected action length mismatch to fail.")


def test_write_lance_dataset_streams_small_batches(tmp_path: Path, monkeypatch):
    calls: list[list[dict[str, object]]] = []
    writer_paths: list[str] = []

    class FakeLanceWriter:
        def __init__(self, path: str, *, mode: str):
            writer_paths.append(path)
            assert mode == "error"

        def __enter__(self) -> "FakeLanceWriter":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def write_episodes(self, payloads: list[dict[str, object]]) -> None:
            calls.append(payloads)

    data_module = types.ModuleType("stable_worldmodel.data")
    data_module.LanceWriter = FakeLanceWriter
    stable_worldmodel_module = types.ModuleType("stable_worldmodel")
    stable_worldmodel_module.data = data_module
    monkeypatch.setitem(sys.modules, "stable_worldmodel", stable_worldmodel_module)
    monkeypatch.setitem(sys.modules, "stable_worldmodel.data", data_module)

    def make_episode(index: int) -> LeWMEpisode:
        pixels = [
            np.full((4, 4, 3), index, dtype=np.uint8),
            np.full((4, 4, 3), index + 1, dtype=np.uint8),
        ]
        action = np.zeros((2, 1), dtype=np.float32)
        return LeWMEpisode(
            dataset_id="wob",
            source=f"source-{index}",
            episode_id=f"episode-{index}",
            pixels=pixels,
            action=action,
            label="Normal",
            category="Normal",
            split="train",
            pair_id=f"pair-{index}",
            action_mode="zero_action",
        )

    progress_calls: list[int] = []
    output = write_lance_dataset(
        (make_episode(index) for index in range(5)),
        tmp_path / "dataset.lance",
        batch_size=2,
        progress=progress_calls.append,
    )

    assert output == tmp_path / "dataset.lance"
    assert writer_paths == [output.resolve().as_posix()]
    assert [len(batch) for batch in calls] == [2, 2, 1]
    assert progress_calls == [2, 4, 5]
