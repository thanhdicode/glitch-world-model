from __future__ import annotations

import numpy as np
import pytest

from scripts.run_gate8_baselines_from_lance import (
    baseline_values,
    fit_feature_centroid,
    validate_baseline_alignment,
)


def test_baseline_values_match_frame_diff_and_six_dimensional_feature_contract():
    pixels = np.zeros((2, 4, 3, 2, 2), dtype=np.uint8)
    pixels[0, 1:] = 255
    pixels[1, :, 0] = 255

    frame_diff, features = baseline_values(pixels)

    assert frame_diff[0] == pytest.approx(1.0 / 3.0)
    assert frame_diff[1] == pytest.approx(0.0)
    assert features.shape == (2, 6)
    assert features[1, :3].tolist() == pytest.approx([1.0, 0.0, 0.0])
    assert features[1, 3:].tolist() == pytest.approx([0.0, 0.0, 0.0])


def test_fit_feature_centroid_uses_only_supplied_train_features():
    centroid = fit_feature_centroid(
        [
            np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32),
            np.asarray([[4.0, 5.0]], dtype=np.float32),
        ]
    )

    assert centroid.tolist() == pytest.approx([2.0, 3.0])


def test_baseline_alignment_rejects_reordered_or_extra_rows():
    manifest = [{"window_id": "a"}, {"window_id": "b"}]
    scores = [
        {"window_id": "a", "frame_diff": "0.1", "feature_distance": "0.2"},
        {"window_id": "b", "frame_diff": "0.3", "feature_distance": "0.4"},
    ]

    validate_baseline_alignment(manifest, scores)
    with pytest.raises(ValueError, match="ordered"):
        validate_baseline_alignment(manifest, list(reversed(scores)))
    with pytest.raises(ValueError, match="ordered"):
        validate_baseline_alignment(manifest, [*scores, dict(scores[0])])


def test_baseline_alignment_rejects_non_finite_values():
    manifest = [{"window_id": "a"}]
    with pytest.raises(ValueError, match="finite"):
        validate_baseline_alignment(
            manifest,
            [{"window_id": "a", "frame_diff": "nan", "feature_distance": "0.2"}],
        )
