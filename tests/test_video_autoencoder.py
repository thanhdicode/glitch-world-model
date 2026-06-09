import importlib.util
from pathlib import Path

import pytest

from glitch_detection.video_autoencoder import (
    VideoAutoencoderConfig,
    VideoAutoencoderUnavailableError,
    require_torch,
    resolve_checkpoint,
    score_manifest,
    select_frame_paths,
)


def test_video_autoencoder_config_rejects_incompatible_image_size():
    with pytest.raises(ValueError, match="divisible by 4"):
        VideoAutoencoderConfig(image_size=30)


def test_select_frame_paths_pads_short_clips_with_last_frame(tmp_path: Path):
    frames = [tmp_path / f"{index:06d}.png" for index in range(3)]

    selected = select_frame_paths(frames, clip_length=5)

    assert selected == [frames[0], frames[1], frames[2], frames[2], frames[2]]


def test_resolve_checkpoint_requires_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("VIDEO_AUTOENCODER_CHECKPOINT", raising=False)

    with pytest.raises(VideoAutoencoderUnavailableError, match="checkpoint"):
        resolve_checkpoint(None)
    with pytest.raises(VideoAutoencoderUnavailableError, match="does not exist"):
        resolve_checkpoint(tmp_path / "missing.pt")


def test_score_manifest_requires_checkpoint_before_loading_torch(tmp_path: Path):
    with pytest.raises(VideoAutoencoderUnavailableError, match="checkpoint"):
        score_manifest(
            manifest_path=tmp_path / "manifest.csv",
            labels_path=None,
            output_path=tmp_path / "scores.csv",
        )


@pytest.mark.skipif(importlib.util.find_spec("torch") is not None, reason="requires no local torch")
def test_require_torch_reports_optional_dependency():
    with pytest.raises(VideoAutoencoderUnavailableError, match=r"\.\[gpu\]"):
        require_torch()
