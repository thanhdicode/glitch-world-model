from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from scripts.build_k2_glitchbench_kaggle_dataset import build_k2_glitchbench_kaggle_dataset
from scripts.validate_glitchbench_bundle import validate_glitchbench_bundle


def _png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 4), (0, 0, 255)).save(path)
    return path


def _write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_build_k2_glitchbench_kaggle_dataset_packages_bundle(tmp_path: Path):
    source_root = tmp_path / "source"
    normal_clip = source_root / "normal_source" / "clips" / "normal_clip"
    validation_normal_clip = (
        source_root / "validation_normal_source" / "clips" / "validation_normal_clip"
    )
    buggy_clip = source_root / "buggy_source" / "clips" / "buggy_clip"
    _png(normal_clip / "frame_000000.png")
    _png(validation_normal_clip / "frame_000000.png")
    _png(buggy_clip / "frame_000000.png")
    manifest_path = _write_csv(
        tmp_path / "combined_manifest.csv",
        [
            {
                "clip_id": "normal_clip",
                "source": "normal_source",
                "clip_dir": str(normal_clip),
                "start_frame": "0",
                "end_frame": "0",
                "frame_count": "1",
                "fps": "1.0",
            },
            {
                "clip_id": "buggy_clip",
                "source": "buggy_source",
                "clip_dir": str(buggy_clip),
                "start_frame": "0",
                "end_frame": "0",
                "frame_count": "1",
                "fps": "1.0",
            },
            {
                "clip_id": "validation_normal_clip",
                "source": "validation_normal_source",
                "clip_dir": str(validation_normal_clip),
                "start_frame": "0",
                "end_frame": "0",
                "frame_count": "1",
                "fps": "1.0",
            },
        ],
    )
    split_path = _write_csv(
        tmp_path / "grouped_split.csv",
        [
            {
                "source": "normal_source",
                "category": "Physics",
                "label": "Normal",
                "split": "train",
                "pair_id_heuristic": "reddit-1",
            },
            {
                "source": "buggy_source",
                "category": "Physics",
                "label": "Buggy",
                "split": "validation",
                "pair_id_heuristic": "reddit-2",
            },
            {
                "source": "validation_normal_source",
                "category": "Physics",
                "label": "Normal",
                "split": "validation",
                "pair_id_heuristic": "reddit-3",
            },
        ],
    )
    protocol_audit_path = tmp_path / "glitchbench_protocol_audit.json"
    protocol_audit_path.write_text(json.dumps({"claim_boundary": "bounded"}), encoding="utf-8")

    audit = build_k2_glitchbench_kaggle_dataset(
        manifest_path=manifest_path,
        split_path=split_path,
        protocol_audit_path=protocol_audit_path,
        output_root=tmp_path / "outputs",
    )

    package_root = tmp_path / "outputs" / "lewm-k2-glitchbench-inputs"
    assert audit["status"] == "k2_input_ready"
    assert (tmp_path / "outputs" / "lewm-k2-glitchbench-inputs.zip").is_file()
    assert (tmp_path / "outputs" / "lewm-k2-glitchbench-inputs.zip.sha256").is_file()
    assert validate_glitchbench_bundle(package_root)["status"] == "validated"
