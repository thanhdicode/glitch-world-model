from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from glitch_detection.manifest import ClipRecord, write_manifest
from glitch_detection.splits import GroupedSplitRecord, write_grouped_split_csv
from scripts.run_kaggle_learned_baselines import run_kaggle_learned_baselines
from scripts.validate_learned_baselines import validate_learned_baselines


def _record(tmp_path: Path, source: str) -> ClipRecord:
    clip_id = f"{source}_000000"
    clip_dir = tmp_path / source / "clips" / clip_id
    clip_dir.mkdir(parents=True)
    return ClipRecord(clip_id, source, str(clip_dir), 0, 15, 16, 30.0)


def _split(source: str, label: str, split: str, pair_id: str) -> GroupedSplitRecord:
    return GroupedSplitRecord(source, "Blinking", label, split, pair_id)


def _write_scores_csv(
    records: list[ClipRecord], scores: dict[str, float], output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
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


def _fake_train_model(
    records: list[ClipRecord],
    checkpoint_path: Path,
    metadata_path: Path,
    config: object,
    device: str = "auto",
) -> dict[str, object]:
    checkpoint_path.write_text("fake-checkpoint\n", encoding="utf-8")
    metadata = {
        "model": "fake",
        "fit_split": "train-normal",
        "train_clip_count": len(records),
        "device": device,
        "config": getattr(config, "__dict__", {}),
        "checkpoint_path": str(checkpoint_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def _fake_score_records_with_checkpoint(
    records: list[ClipRecord], checkpoint_path: Path, device: str = "auto"
) -> dict[str, float]:
    _ = checkpoint_path, device
    return {record.clip_id: float(index + 1) / 10.0 for index, record in enumerate(records)}


def test_dry_run_writes_protocol_audit_without_checkpoints(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    split_path = tmp_path / "split.csv"
    output_root = tmp_path / "outputs"
    records = [
        _record(tmp_path, "train_normal_a"),
        _record(tmp_path, "train_normal_b"),
        _record(tmp_path, "validation_normal"),
        _record(tmp_path, "validation_buggy"),
        _record(tmp_path, "test_normal"),
    ]
    write_manifest(manifest_path, records)
    write_grouped_split_csv(
        split_path,
        [
            _split("train_normal_a", "Normal", "train", "Blinking/1"),
            _split("train_normal_b", "Normal", "train", "Blinking/2"),
            _split("validation_normal", "Normal", "validation", "Blinking/3"),
            _split("validation_buggy", "Buggy", "validation", "Blinking/4"),
            _split("test_normal", "Normal", "test", "Blinking/5"),
        ],
        seed=42,
    )

    summary = run_kaggle_learned_baselines(
        manifest_path=manifest_path,
        split_path=split_path,
        output_root=output_root,
        dry_run=True,
    )

    assert summary["status"] == "dry-run only"
    assert summary["train_normal_clip_count"] == 2
    assert summary["validation_clip_count"] == 2
    assert summary["test_clip_count"] == 1
    assert summary["test_materialized"] is False
    assert summary["locked_test_scored"] is False
    assert not (output_root / "video_autoencoder.pt").exists()
    assert not (output_root / "cnn_lstm.pt").exists()
    assert not (output_root / "video_transformer.pt").exists()
    assert json.loads((output_root / "protocol_audit.json").read_text(encoding="utf-8")) == summary
    assert (
        json.loads((output_root / "learned_baselines_summary.json").read_text(encoding="utf-8"))
        == summary
    )


def test_runner_and_validator_complete_with_stubbed_baselines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest_path = tmp_path / "manifest.csv"
    split_path = tmp_path / "split.csv"
    output_root = tmp_path / "outputs"
    records = [
        _record(tmp_path, "train_normal_a"),
        _record(tmp_path, "train_normal_b"),
        _record(tmp_path, "validation_normal"),
        _record(tmp_path, "validation_buggy"),
    ]
    write_manifest(manifest_path, records)
    write_grouped_split_csv(
        split_path,
        [
            _split("train_normal_a", "Normal", "train", "Blinking/1"),
            _split("train_normal_b", "Normal", "train", "Blinking/2"),
            _split("validation_normal", "Normal", "validation", "Blinking/3"),
            _split("validation_buggy", "Buggy", "validation", "Blinking/4"),
        ],
        seed=42,
    )

    for module_name in ("video_autoencoder", "cnn_lstm", "video_transformer"):
        monkeypatch.setattr(
            f"scripts.run_kaggle_learned_baselines.{module_name}.train_model",
            _fake_train_model,
        )
        monkeypatch.setattr(
            f"scripts.run_kaggle_learned_baselines.{module_name}.score_records_with_checkpoint",
            _fake_score_records_with_checkpoint,
        )
        monkeypatch.setattr(
            f"scripts.run_kaggle_learned_baselines.{module_name}.write_scores",
            _write_scores_csv,
        )

    summary = run_kaggle_learned_baselines(
        manifest_path=manifest_path,
        split_path=split_path,
        output_root=output_root,
        dry_run=False,
    )

    assert summary["status"] == "training and validation scoring complete"
    assert set(summary["baseline_outputs"]) == {
        "video_autoencoder",
        "cnn_lstm",
        "video_transformer",
    }
    for name in summary["baseline_outputs"]:
        assert (output_root / f"{name}.pt").is_file()
        assert (output_root / f"{name}_training_metadata.json").is_file()
        assert (output_root / f"{name}_validation_scores.csv").is_file()
        assert (output_root / f"{name}.pt.sha256").is_file()

    receipt = validate_learned_baselines(output_root)

    assert receipt["status"] == "validated"
    assert receipt["train_normal_clip_count"] == 2
    assert receipt["validation_clip_count"] == 2


def test_dry_run_rejects_cross_split_pair_groups(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    split_path = tmp_path / "split.csv"
    write_manifest(
        manifest_path, [_record(tmp_path, "train_normal"), _record(tmp_path, "test_buggy")]
    )
    write_grouped_split_csv(
        split_path,
        [
            _split("train_normal", "Normal", "train", "Blinking/1"),
            _split("test_buggy", "Buggy", "test", "Blinking/1"),
        ],
        seed=42,
    )

    with pytest.raises(ValueError, match="cross split"):
        run_kaggle_learned_baselines(
            manifest_path=manifest_path,
            split_path=split_path,
            output_root=tmp_path / "outputs",
            dry_run=True,
        )
