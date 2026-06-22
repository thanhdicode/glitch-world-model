from __future__ import annotations

import pytest

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
