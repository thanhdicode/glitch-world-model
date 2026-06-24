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


def test_update_based_training_requires_intervals():
    with pytest.raises(ValueError, match="requires evaluation and checkpoint intervals"):
        LeWMTrainConfig(target_optimizer_updates=15000)


def test_research_training_config_exposes_update_controls():
    config = LeWMTrainConfig(
        run_kind="research",
        target_optimizer_updates=15000,
        evaluation_interval_updates=500,
        checkpoint_interval_updates=500,
    )

    assert config.target_optimizer_updates == 15000
    assert config.evaluation_interval_updates == 500
    assert config.checkpoint_interval_updates == 500


def test_training_config_accepts_zero_action_and_sigreg_toggle():
    config = LeWMTrainConfig(action_mode="zero_action", sigreg_enabled=False)

    assert config.action_mode == "zero_action"
    assert config.sigreg_enabled is False


def test_training_config_rejects_action_free_training_mode():
    with pytest.raises(ValueError, match="action_free"):
        LeWMTrainConfig(action_mode="action_free")
