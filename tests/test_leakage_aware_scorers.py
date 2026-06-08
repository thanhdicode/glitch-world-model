from pathlib import Path

import numpy as np
from PIL import Image

from glitch_detection.feature_distance import fit_centroid, score_records_with_centroid
from glitch_detection.manifest import ClipRecord
from glitch_detection.mini_latent import fit_model, score_records_with_model


def _clip(tmp_path: Path, name: str, values: list[int]) -> ClipRecord:
    clip_dir = tmp_path / name
    clip_dir.mkdir()
    for index, value in enumerate(values):
        Image.new("RGB", (8, 8), color=(value, value, value)).save(clip_dir / f"{index:06d}.png")
    return ClipRecord(name, name, str(clip_dir), 0, len(values) - 1, len(values), 30.0)


def test_feature_distance_centroid_is_fit_from_supplied_train_records_only(tmp_path: Path):
    train_normal = _clip(tmp_path, "train_normal", [10, 10, 10, 10])
    test_normal = _clip(tmp_path, "test_normal", [240, 240, 240, 240])

    centroid = fit_centroid([train_normal])
    scores = score_records_with_centroid([train_normal, test_normal], centroid)

    assert scores["train_normal"] < scores["test_normal"]
    assert np.allclose(centroid[:3], np.full(3, 10 / 255.0), atol=1e-5)


def test_mini_latent_model_is_fit_once_and_reused_for_test_records(tmp_path: Path):
    train_normal = _clip(tmp_path, "train_normal", [10, 20, 30, 40])
    test_record = _clip(tmp_path, "test_record", [40, 30, 20, 10])

    model = fit_model([train_normal], latent_dim=2, image_size=4)
    scores = score_records_with_model([test_record], model)

    assert model.image_size == 4
    assert model.mean.shape == (16,)
    assert set(scores) == {"test_record"}
    assert scores["test_record"] >= 0.0
