from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import make_dataclass
from pathlib import Path

import pytest
from PIL import Image

from glitch_detection.manifest import read_manifest
from glitch_detection.splits import read_grouped_split_csv
from scripts.run_kaggle_glitchbench_benchmark import (
    _score_learned_baselines,
    _validate_lewm_seed_artifact_root,
    run_kaggle_glitchbench_benchmark,
)


def _png(path: Path, color: tuple[int, int, int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 4), color).save(path)
    return path


def _write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _package_root(tmp_path: Path) -> Path:
    package_root = tmp_path / "package"
    clips_root = package_root / "clips_root"
    clip_specs = {
        "train_normal_a_clip": ("train_normal_a", (0, 255, 0)),
        "train_normal_b_clip": ("train_normal_b", (0, 200, 0)),
        "validation_normal_clip": ("validation_normal", (0, 150, 0)),
        "validation_buggy_clip": ("validation_buggy", (255, 0, 0)),
    }
    for clip_id, (source, color) in clip_specs.items():
        _png(clips_root / source / "clips" / clip_id / "frame_000000.png", color)
    _write_csv(
        package_root / "combined_manifest.csv",
        [
            {
                "clip_id": clip_id,
                "source": source,
                "clip_dir": f"clips_root/{source}/clips/{clip_id}",
                "start_frame": "0",
                "end_frame": "0",
                "frame_count": "1",
                "fps": "1.0",
            }
            for clip_id, (source, _color) in clip_specs.items()
        ],
    )
    _write_csv(
        package_root / "grouped_split.csv",
        [
            {
                "source": "train_normal_a",
                "category": "Physics",
                "label": "Normal",
                "split": "train",
                "pair_id_heuristic": "reddit-1",
            },
            {
                "source": "train_normal_b",
                "category": "Physics",
                "label": "Normal",
                "split": "train",
                "pair_id_heuristic": "reddit-2",
            },
            {
                "source": "validation_normal",
                "category": "Physics",
                "label": "Normal",
                "split": "validation",
                "pair_id_heuristic": "reddit-3",
            },
            {
                "source": "validation_buggy",
                "category": "Physics",
                "label": "Buggy",
                "split": "validation",
                "pair_id_heuristic": "reddit-4",
            },
        ],
    )
    (package_root / "glitchbench_protocol_audit.json").write_text(
        json.dumps({"claim_boundary": "bounded", "limitations": {"claim_boundary": "bounded"}}),
        encoding="utf-8",
    )
    (package_root / "k2_input_audit.json").write_text(
        json.dumps({"locked_test_materialized": False, "locked_test_scored": False}, indent=2),
        encoding="utf-8",
    )
    (package_root / "README_KAGGLE.md").write_text("readme\n", encoding="utf-8")
    (package_root / "RUN_K2_COMMAND.txt").write_text("python run\n", encoding="utf-8")
    return package_root


def _artifact_root(tmp_path: Path) -> Path:
    root = tmp_path / "artifacts"
    for seed in (42, 43, 44):
        seed_root = root / f"seed{seed}"
        seed_root.mkdir(parents=True, exist_ok=True)
        checkpoint_path = seed_root / "best_weights.pt"
        checkpoint_path.write_bytes(f"weights-{seed}".encode("utf-8"))
        (seed_root / "config.json").write_text(
            json.dumps({"seed": seed, "image_size": 4}),
            encoding="utf-8",
        )
        (seed_root / "checkpoint.sha256").write_text(
            f"{hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()}\n",
            encoding="utf-8",
        )
    return root


def test_k2_dry_run_accepts_direct_package_inputs(tmp_path: Path):
    package_root = _package_root(tmp_path)

    summary = run_kaggle_glitchbench_benchmark(
        manifest_path=package_root / "combined_manifest.csv",
        split_path=package_root / "grouped_split.csv",
        clips_root=package_root / "clips_root",
        output_root=tmp_path / "out",
        device="cpu",
        dry_run=True,
    )

    assert summary["status"] == "dry_run_ready"
    assert summary["train_normal_clip_count"] == 2
    assert summary["validation_clip_count"] == 2
    assert not (package_root / "_validator_glitchbench_records.csv").exists()


def test_k2_full_run_fails_closed_without_lewm_artifacts(tmp_path: Path):
    package_root = _package_root(tmp_path)

    with pytest.raises(ValueError, match="Scientific K2 requires --lewm-seed-artifact-root"):
        run_kaggle_glitchbench_benchmark(
            manifest_path=package_root / "combined_manifest.csv",
            split_path=package_root / "grouped_split.csv",
            clips_root=package_root / "clips_root",
            output_root=tmp_path / "out",
            device="cpu",
            dry_run=False,
        )


def test_k2_baseline_only_mode_requires_explicit_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    package_root = _package_root(tmp_path)
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_simple_baselines",
        lambda **kwargs: [{"method": "frame_diff"}],
    )
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_learned_baselines",
        lambda **kwargs: [{"method": "video_autoencoder"}],
    )

    summary = run_kaggle_glitchbench_benchmark(
        manifest_path=package_root / "combined_manifest.csv",
        split_path=package_root / "grouped_split.csv",
        clips_root=package_root / "clips_root",
        output_root=tmp_path / "out",
        device="cpu",
        dry_run=False,
        baseline_only=True,
    )

    assert summary["status"] == "baseline_only_complete_no_lewm"
    assert summary["lewm_results"] == []
    assert summary["lewm_artifact_validation"] is None


def test_validate_lewm_seed_artifact_root_accepts_expected_layout(tmp_path: Path):
    artifact_root = _artifact_root(tmp_path)

    artifacts = _validate_lewm_seed_artifact_root(artifact_root)

    assert [artifact.seed for artifact in artifacts] == [42, 43, 44]


def test_k2_summary_status_is_complete_when_lewm_lane_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    package_root = _package_root(tmp_path)
    artifact_root = _artifact_root(tmp_path)
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_simple_baselines",
        lambda **kwargs: [{"method": "frame_diff"}],
    )
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_learned_baselines",
        lambda **kwargs: [{"method": "video_autoencoder"}],
    )
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_lewm",
        lambda **kwargs: ([{"method": "lewm", "seed": 42, "aggregation": "mean"}], {"ok": True}),
    )

    summary = run_kaggle_glitchbench_benchmark(
        manifest_path=package_root / "combined_manifest.csv",
        split_path=package_root / "grouped_split.csv",
        clips_root=package_root / "clips_root",
        output_root=tmp_path / "out",
        device="cpu",
        dry_run=False,
        lewm_seed_artifact_root=artifact_root,
    )

    assert summary["status"] == "k2_complete_lewm_and_baselines"
    assert summary["lewm_artifact_validation"] == {"ok": True}


def test_score_learned_baselines_does_not_pass_device_to_config_constructors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    package_root = _package_root(tmp_path)
    train_records = read_manifest(package_root / "combined_manifest.csv")[:2]
    validation_records = read_manifest(package_root / "combined_manifest.csv")[2:]
    split_records = read_grouped_split_csv(package_root / "grouped_split.csv")
    constructor_calls: list[str] = []

    def _constructor(name: str):
        def _build(**kwargs):
            assert "device" not in kwargs
            constructor_calls.append(name)
            config_type = make_dataclass("Config", [("model_name", str)])
            return config_type(kwargs.get("model_name", name))

        return _build

    def _fake_train_model(records, checkpoint_path, metadata_path, config, device="auto"):
        checkpoint_path.write_text("checkpoint\n", encoding="utf-8")
        metadata_path.write_text(json.dumps({"device": device}), encoding="utf-8")
        return {
            "device": device,
            "clip_count": len(records),
            "config": getattr(config, "__dict__", {}),
        }

    def _fake_score_records(records, checkpoint_path, device="auto"):
        _ = checkpoint_path, device
        return {record.clip_id: float(index + 1) for index, record in enumerate(records)}

    def _fake_write_scores(records, scores, output_path):
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
            )
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "clip_id": record.clip_id,
                        "source": record.source,
                        "clip_dir": record.clip_dir,
                        "start_frame": record.start_frame,
                        "end_frame": record.end_frame,
                        "score": f"{scores[record.clip_id]:.8f}",
                    }
                )
        return output_path

    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark.video_autoencoder.VideoAutoencoderConfig",
        _constructor("video_autoencoder"),
    )
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark.cnn_lstm.CNNLSTMConfig",
        _constructor("cnn_lstm"),
    )
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark.video_transformer.VideoTransformerConfig",
        _constructor("video_transformer"),
    )
    output_root = tmp_path / "out"
    output_root.mkdir(parents=True, exist_ok=True)
    for module_name in ("video_autoencoder", "cnn_lstm", "video_transformer"):
        monkeypatch.setattr(
            f"scripts.run_kaggle_glitchbench_benchmark.{module_name}.train_model",
            _fake_train_model,
        )
        monkeypatch.setattr(
            f"scripts.run_kaggle_glitchbench_benchmark.{module_name}.score_records_with_checkpoint",
            _fake_score_records,
        )
        monkeypatch.setattr(
            f"scripts.run_kaggle_glitchbench_benchmark.{module_name}.write_scores",
            _fake_write_scores,
        )

    results = _score_learned_baselines(
        train_records=train_records,
        validation_records=validation_records,
        split_records=split_records,
        output_root=output_root,
        device="cuda",
    )

    assert [row["method"] for row in results] == [
        "video_autoencoder",
        "cnn_lstm",
        "video_transformer",
    ]
    assert constructor_calls == ["video_autoencoder", "cnn_lstm", "video_transformer"]


def test_k2_full_run_reaches_learned_baseline_setup_without_constructor_typeerror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    package_root = _package_root(tmp_path)
    artifact_root = _artifact_root(tmp_path)
    learned_setup_called = {"value": False}

    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_simple_baselines",
        lambda **kwargs: [{"method": "frame_diff"}],
    )

    def _fake_learned(**kwargs):
        learned_setup_called["value"] = True
        return [{"method": "video_autoencoder"}]

    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_learned_baselines",
        _fake_learned,
    )
    monkeypatch.setattr(
        "scripts.run_kaggle_glitchbench_benchmark._score_lewm",
        lambda **kwargs: ([{"method": "lewm", "seed": 42, "aggregation": "mean"}], {"ok": True}),
    )

    summary = run_kaggle_glitchbench_benchmark(
        manifest_path=package_root / "combined_manifest.csv",
        split_path=package_root / "grouped_split.csv",
        clips_root=package_root / "clips_root",
        output_root=tmp_path / "out",
        device="cuda",
        dry_run=False,
        lewm_seed_artifact_root=artifact_root,
    )

    assert learned_setup_called["value"] is True
    assert summary["status"] == "k2_complete_lewm_and_baselines"
