from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

from glitch_detection.manifest import ClipRecord, write_manifest
from scripts.build_k1_kaggle_input_dataset import build_k1_kaggle_input_dataset


def _make_clip(tmp_path: Path, source: str, index: int) -> ClipRecord:
    clip_id = f"{source}_{index:06d}"
    clip_dir = tmp_path / "processed" / source / "clips" / clip_id
    clip_dir.mkdir(parents=True, exist_ok=True)
    for frame_index in range(3):
        (clip_dir / f"{frame_index:06d}.png").write_bytes(b"png")
    return ClipRecord(
        clip_id=clip_id,
        source=source,
        clip_dir=str(clip_dir),
        start_frame=0,
        end_frame=2,
        frame_count=3,
        fps=30.0,
    )


def test_build_k1_kaggle_input_dataset_creates_portable_package(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    split_path = tmp_path / "split.csv"
    output_root = tmp_path / "outputs"
    records = [
        _make_clip(tmp_path, "train_normal_a", 0),
        _make_clip(tmp_path, "train_normal_b", 0),
        _make_clip(tmp_path, "validation_normal", 0),
        _make_clip(tmp_path, "validation_buggy", 0),
    ]
    write_manifest(manifest_path, records)
    with split_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset_id",
                "source",
                "episode_id",
                "pair_id",
                "category",
                "label",
                "split",
                "action_mode",
                "use_for_training",
                "materialize",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "dataset_id": "tempglitch",
                    "source": "train_normal_a",
                    "episode_id": "train_normal_a",
                    "pair_id": "Blinking/1",
                    "category": "Blinking",
                    "label": "Normal",
                    "split": "train",
                    "action_mode": "zero_action",
                    "use_for_training": "True",
                    "materialize": "True",
                },
                {
                    "dataset_id": "tempglitch",
                    "source": "train_normal_b",
                    "episode_id": "train_normal_b",
                    "pair_id": "Blinking/2",
                    "category": "Blinking",
                    "label": "Normal",
                    "split": "train",
                    "action_mode": "zero_action",
                    "use_for_training": "True",
                    "materialize": "True",
                },
                {
                    "dataset_id": "tempglitch",
                    "source": "validation_normal",
                    "episode_id": "validation_normal",
                    "pair_id": "Blinking/3",
                    "category": "Blinking",
                    "label": "Normal",
                    "split": "validation",
                    "action_mode": "zero_action",
                    "use_for_training": "False",
                    "materialize": "True",
                },
                {
                    "dataset_id": "tempglitch",
                    "source": "validation_buggy",
                    "episode_id": "validation_buggy",
                    "pair_id": "Blinking/4",
                    "category": "Blinking",
                    "label": "Buggy",
                    "split": "validation",
                    "action_mode": "zero_action",
                    "use_for_training": "False",
                    "materialize": "True",
                },
            ]
        )

    audit = build_k1_kaggle_input_dataset(
        manifest_path=manifest_path,
        split_source_path=split_path,
        source_roots=[tmp_path / "processed"],
        output_root=output_root,
        required_train_normal=2,
        required_validation_normal=1,
        required_validation_buggy=1,
    )

    package_root = output_root / "lewm-k1-tempglitch-inputs"
    assert audit["split_source_count"] == 4
    assert audit["train_normal_source_count"] == 2
    assert audit["validation_normal_source_count"] == 1
    assert audit["validation_buggy_source_count"] == 1
    assert audit["selected_clip_record_count"] == 4
    assert audit["copied_clip_folders"] == 4
    assert audit["total_frame_count"] == 12
    assert audit["missing_clip_count"] == 0
    assert (package_root / "combined_manifest.csv").is_file()
    assert (package_root / "grouped_split.csv").is_file()
    assert (package_root / "k1_input_audit.json").is_file()
    assert (package_root / "README_KAGGLE.md").is_file()
    assert (package_root / "RUN_K1_COMMAND.txt").is_file()
    assert (output_root / "lewm-k1-tempglitch-inputs.zip").is_file()
    assert (output_root / "lewm-k1-tempglitch-inputs.zip.sha256").is_file()

    manifest_rows = list(
        csv.DictReader((package_root / "combined_manifest.csv").open(encoding="utf-8-sig"))
    )
    assert all(row["clip_dir"].startswith("clips_root/") for row in manifest_rows)
    readme = (package_root / "README_KAGGLE.md").read_text(encoding="utf-8")
    assert "/kaggle/input/lewm-k1-tempglitch-inputs/combined_manifest.csv" in readme
    audit_payload = json.loads((package_root / "k1_input_audit.json").read_text(encoding="utf-8"))
    assert audit_payload["zip_sha256"] == audit["zip_sha256"]
    with zipfile.ZipFile(output_root / "lewm-k1-tempglitch-inputs.zip") as archive:
        names = set(archive.namelist())
    assert "lewm-k1-tempglitch-inputs/combined_manifest.csv" in names
    assert "lewm-k1-tempglitch-inputs/grouped_split.csv" in names
    assert (
        "lewm-k1-tempglitch-inputs/clips_root/train_normal_a/clips/train_normal_a_000000/000000.png"
        in names
    )
