from scripts.run_phase6e_kaggle_automation import build_config, build_parser


def test_cli_defaults_to_dry_run():
    args = build_parser().parse_args([])

    config = build_config(args)

    assert config.dry_run is True
    assert config.dataset_slug == "thanhhuynhdieu/glitch-world-model-phase6e"
    assert config.kernel_slug == "thanhhuynhdieu/phase6e-video-autoencoder"
    assert config.recursive_mode == "zip"


def test_cli_requires_explicit_live_flag():
    args = build_parser().parse_args(["--live"])

    assert build_config(args).dry_run is False
