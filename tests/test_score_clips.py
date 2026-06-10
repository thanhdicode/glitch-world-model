from pathlib import Path

import pytest

from glitch_detection.score_clips import available_scorers, run_scorer


def test_available_scorers_contains_existing_baselines():
    assert "frame_diff" in available_scorers()
    assert "feature_distance" in available_scorers()
    assert "video_autoencoder" in available_scorers()


def test_unknown_scorer_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="Unknown scorer"):
        run_scorer(
            scorer_name="missing",
            manifest_path=tmp_path / "manifest.csv",
            labels_path=None,
            output_path=tmp_path / "scores.csv",
        )


def test_train_dependent_generic_scorer_requires_explicit_unsafe_opt_in(tmp_path: Path):
    with pytest.raises(ValueError, match="split-aware"):
        run_scorer(
            scorer_name="feature_distance",
            manifest_path=tmp_path / "manifest.csv",
            labels_path=tmp_path / "labels.csv",
            output_path=tmp_path / "scores.csv",
        )
