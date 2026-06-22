from __future__ import annotations

import pytest

from glitch_detection.r5_xgame_protocol import validate_r5_xgame_manifest


def _rows() -> list[dict[str, str]]:
    return [
        {
            "dataset_id": "a",
            "source": "train",
            "episode_id": "train-1",
            "pair_id": "p1",
            "label": "Normal",
            "split": "train",
            "evaluation_role": "train_normal",
        },
        {
            "dataset_id": "a",
            "source": "cal",
            "episode_id": "cal-1",
            "pair_id": "p2",
            "label": "Normal",
            "split": "validation",
            "evaluation_role": "calibration_normal",
        },
        {
            "dataset_id": "b",
            "source": "normal",
            "episode_id": "normal-1",
            "pair_id": "p3",
            "label": "Normal",
            "split": "validation",
            "evaluation_role": "evaluation_normal_negative",
        },
        {
            "dataset_id": "c",
            "source": "buggy",
            "episode_id": "buggy-1",
            "pair_id": "p4",
            "label": "Buggy",
            "split": "validation",
            "evaluation_role": "evaluation_buggy_positive",
        },
    ]


def test_r5_xgame_protocol_accepts_disjoint_binary_split():
    assert validate_r5_xgame_manifest(_rows())["evaluation_normal_negative"] == 1


@pytest.mark.parametrize("role", ["evaluation_normal_negative", "evaluation_buggy_positive"])
def test_r5_xgame_protocol_rejects_missing_evaluation_class(role: str):
    rows = [row for row in _rows() if row["evaluation_role"] != role]
    with pytest.raises(ValueError, match=role):
        validate_r5_xgame_manifest(rows)


def test_r5_xgame_protocol_rejects_calibration_evaluation_overlap():
    rows = _rows()
    rows[2]["episode_id"] = "cal-1"
    with pytest.raises(ValueError, match="leakage"):
        validate_r5_xgame_manifest(rows)


def test_r5_xgame_protocol_rejects_source_overlap():
    rows = _rows()
    rows[2]["source"] = "cal"
    with pytest.raises(ValueError, match="leakage"):
        validate_r5_xgame_manifest(rows)


def test_r5_xgame_protocol_rejects_pair_overlap():
    rows = _rows()
    rows[2]["pair_id"] = "p2"
    with pytest.raises(ValueError, match="leakage"):
        validate_r5_xgame_manifest(rows)


@pytest.mark.parametrize("role", ["train_normal", "calibration_normal"])
def test_r5_xgame_protocol_rejects_buggy_fit_rows(role: str):
    rows = _rows()
    next(row for row in rows if row["evaluation_role"] == role)["label"] = "Buggy"
    with pytest.raises(ValueError, match="must contain only Normal"):
        validate_r5_xgame_manifest(rows)


def test_r5_xgame_protocol_rejects_locked_test_row():
    rows = _rows()
    rows[3]["split"] = "test"
    with pytest.raises(ValueError, match="Locked/test"):
        validate_r5_xgame_manifest(rows)
