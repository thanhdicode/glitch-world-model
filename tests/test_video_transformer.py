import importlib.util
from pathlib import Path

import pytest

from glitch_detection.video_transformer import (
    VideoTransformerConfig,
    VideoTransformerUnavailableError,
    require_transformers,
    resolve_checkpoint,
    score_manifest,
)


def test_video_transformer_config_rejects_non_divisible_patch_geometry():
    with pytest.raises(ValueError, match="patch_size"):
        VideoTransformerConfig(image_size=62)


def test_video_transformer_config_rejects_non_divisible_tubelet_geometry():
    with pytest.raises(ValueError, match="tubelet_size"):
        VideoTransformerConfig(clip_length=15)


def test_resolve_checkpoint_requires_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("VIDEO_TRANSFORMER_CHECKPOINT", raising=False)

    with pytest.raises(VideoTransformerUnavailableError, match="checkpoint"):
        resolve_checkpoint(None)
    with pytest.raises(VideoTransformerUnavailableError, match="does not exist"):
        resolve_checkpoint(tmp_path / "missing.pt")


def test_score_manifest_requires_checkpoint_before_loading_transformers(tmp_path: Path):
    with pytest.raises(VideoTransformerUnavailableError, match="checkpoint"):
        score_manifest(
            manifest_path=tmp_path / "manifest.csv",
            labels_path=None,
            output_path=tmp_path / "scores.csv",
        )


@pytest.mark.skipif(
    importlib.util.find_spec("transformers") is not None,
    reason="requires no local transformers",
)
def test_require_transformers_reports_optional_dependency():
    with pytest.raises(VideoTransformerUnavailableError, match="transformers==4.57.6"):
        require_transformers()
