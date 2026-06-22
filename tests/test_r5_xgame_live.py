from __future__ import annotations

import pytest

from glitch_detection import r5_xgame_live
from glitch_detection.r5_xgame_live import partition_manifest_rows, training_roles


def test_partition_manifest_rows_rejects_test_rows():
    with pytest.raises(ValueError, match="test"):
        partition_manifest_rows([{"evaluation_role": "train_normal", "split": "test"}])


def test_training_roles_excludes_evaluation_rows():
    rows = [
        {"evaluation_role": "train_normal", "split": "train", "label": "Normal"},
        {"evaluation_role": "calibration_normal", "split": "validation", "label": "Normal"},
        {"evaluation_role": "evaluation_normal_negative", "split": "validation", "label": "Normal"},
        {"evaluation_role": "evaluation_buggy_positive", "split": "validation", "label": "Buggy"},
    ]
    train, calibration = training_roles(rows)
    assert len(train) == len(calibration) == 1


def test_train_fresh_seed_uses_role_specific_paths(tmp_path, monkeypatch):
    captured = {}

    def fake_train(train, calibration, output, config, *, device, resume):
        captured.update(
            train=train,
            calibration=calibration,
            output=output,
            config=config,
            device=device,
            resume=resume,
        )
        return {"status": "ok"}

    monkeypatch.setattr(r5_xgame_live, "train_lewm", fake_train)
    result = r5_xgame_live.train_fresh_seed(
        tmp_path / "train.lance",
        tmp_path / "calibration.lance",
        tmp_path / "seed42",
        seed=42,
        device="cuda",
        resume=True,
    )
    assert result["status"] == "ok"
    assert captured["config"].seed == 42
    assert captured["config"].target_optimizer_updates == 15000
    assert captured["calibration"].name == "calibration.lance"
    assert captured["resume"] is True
