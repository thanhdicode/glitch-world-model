import pytest

from glitch_detection.lewm_training import LeWMTrainConfig, build_model_config


def test_training_config_builds_official_lewm_model_contract():
    config = LeWMTrainConfig(image_size=28, predictor_depth=1, sigreg_projections=4)

    model = build_model_config(config, action_dim=3)

    assert model["_target_"] == "stable_worldmodel.wm.lewm.LeWM"
    assert model["encoder"]["image_size"] == 28
    assert model["predictor"]["num_frames"] == 3
    assert model["action_encoder"]["input_dim"] == 3


def test_training_config_rejects_non_patch_aligned_image_size():
    with pytest.raises(ValueError, match="divisible"):
        LeWMTrainConfig(image_size=30)


def test_identical_dataset_override_is_disabled_by_default():
    assert LeWMTrainConfig().allow_identical_datasets_for_smoke is False


def test_research_training_config_exposes_runtime_controls():
    config = LeWMTrainConfig(
        run_kind="research",
        num_workers=2,
        pin_memory=True,
        mixed_precision=True,
        early_stopping_patience=5,
        gradient_clip_norm=1.0,
    )

    assert config.run_kind == "research"
    assert config.early_stopping_patience == 5
    assert config.mixed_precision is True


def test_training_config_rejects_invalid_early_stopping():
    with pytest.raises(ValueError, match="patience"):
        LeWMTrainConfig(early_stopping_patience=0)
