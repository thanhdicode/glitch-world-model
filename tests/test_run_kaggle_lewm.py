from __future__ import annotations

import sys
from dataclasses import asdict, replace
from importlib import util
from pathlib import Path

import pytest

from glitch_detection.lewm_training import LeWMTrainConfig


def _load_runner():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_kaggle_lewm.py"
    spec = util.spec_from_file_location("run_kaggle_lewm", path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _required_args(tmp_path: Path) -> list[str]:
    return [
        "--train-dataset",
        str(tmp_path / "train.lance"),
        "--validation-dataset",
        str(tmp_path / "validation.lance"),
        "--output-root",
        str(tmp_path / "run"),
    ]


def test_kaggle_lewm_runner_defaults_to_seed_42(tmp_path, monkeypatch):
    runner = _load_runner()
    captured = {}

    def fake_train_lewm(train_path, validation_path, output_root, config, *, device, resume):
        captured["config"] = config
        return {"status": "stubbed"}

    monkeypatch.setattr(runner, "train_lewm", fake_train_lewm)

    runner.main(_required_args(tmp_path))

    assert asdict(captured["config"]) == asdict(LeWMTrainConfig())


@pytest.mark.parametrize("seed", [43, 44])
def test_kaggle_lewm_runner_passes_cli_seed_without_changing_other_fields(
    tmp_path, monkeypatch, seed
):
    runner = _load_runner()
    captured = {}

    def fake_train_lewm(train_path, validation_path, output_root, config, *, device, resume):
        captured["config"] = config
        return {"status": "stubbed"}

    monkeypatch.setattr(runner, "train_lewm", fake_train_lewm)

    runner.main([*_required_args(tmp_path), "--seed", str(seed)])

    assert asdict(captured["config"]) == asdict(replace(LeWMTrainConfig(), seed=seed))


def test_kaggle_lewm_runner_passes_update_based_training_controls(tmp_path, monkeypatch):
    runner = _load_runner()
    captured = {}

    def fake_train_lewm(train_path, validation_path, output_root, config, *, device, resume):
        captured["config"] = config
        return {"status": "stubbed"}

    monkeypatch.setattr(runner, "train_lewm", fake_train_lewm)

    runner.main(
        [
            *_required_args(tmp_path),
            "--run-kind",
            "research",
            "--batch-size",
            "8",
            "--mixed-precision",
            "--target-optimizer-updates",
            "15000",
            "--evaluation-interval-updates",
            "500",
            "--checkpoint-interval-updates",
            "500",
        ]
    )

    assert asdict(captured["config"]) == asdict(
        replace(
            LeWMTrainConfig(),
            run_kind="research",
            batch_size=8,
            mixed_precision=True,
            target_optimizer_updates=15000,
            evaluation_interval_updates=500,
            checkpoint_interval_updates=500,
        )
    )


def test_kaggle_lewm_runner_rejects_incompatible_sm60_before_training(tmp_path, monkeypatch):
    runner = _load_runner()

    class _FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def get_device_capability(index=0):
            return (6, 0)

        @staticmethod
        def get_device_name(index=0):
            return "Tesla P100-PCIE-16GB"

    class _FakeTorch:
        cuda = _FakeCuda()

    monkeypatch.setitem(sys.modules, "torch", _FakeTorch())

    def fail_train(*args, **kwargs):
        raise AssertionError("train_lewm should not run for incompatible GPUs")

    monkeypatch.setattr(runner, "train_lewm", fail_train)

    with pytest.raises(RuntimeError, match="Incompatible GPU sm_60; need sm_70\\+"):
        runner.main([*_required_args(tmp_path), "--device", "cuda"])
