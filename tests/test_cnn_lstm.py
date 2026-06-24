import importlib.util
from pathlib import Path

import pytest

from glitch_detection.cnn_lstm import (
    CNNLSTMConfig,
    CNNLSTMUnavailableError,
    require_torch,
    resolve_checkpoint,
    score_manifest,
)


def test_cnn_lstm_config_rejects_too_small_hidden_size():
    with pytest.raises(ValueError, match="hidden_size"):
        CNNLSTMConfig(hidden_size=4)


def test_resolve_checkpoint_requires_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CNN_LSTM_CHECKPOINT", raising=False)

    with pytest.raises(CNNLSTMUnavailableError, match="checkpoint"):
        resolve_checkpoint(None)
    with pytest.raises(CNNLSTMUnavailableError, match="does not exist"):
        resolve_checkpoint(tmp_path / "missing.pt")


def test_score_manifest_requires_checkpoint_before_loading_torch(tmp_path: Path):
    with pytest.raises(CNNLSTMUnavailableError, match="checkpoint"):
        score_manifest(
            manifest_path=tmp_path / "manifest.csv",
            labels_path=None,
            output_path=tmp_path / "scores.csv",
        )


@pytest.mark.skipif(importlib.util.find_spec("torch") is not None, reason="requires no local torch")
def test_require_torch_reports_optional_dependency():
    with pytest.raises(CNNLSTMUnavailableError, match=r"\.\[gpu\]"):
        require_torch()
