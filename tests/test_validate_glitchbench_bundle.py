from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from scripts import validate_glitchbench_bundle as validator_module
from scripts.validate_glitchbench_bundle import validate_glitchbench_bundle


def _png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 4), (0, 255, 0)).save(path)
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
    normal_clip = clips_root / "normal_source" / "clips" / "normal_clip"
    buggy_clip = clips_root / "buggy_source" / "clips" / "buggy_clip"
    _png(normal_clip / "frame_000000.png")
    _png(buggy_clip / "frame_000000.png")
    _write_csv(
        package_root / "combined_manifest.csv",
        [
            {
                "clip_id": "normal_clip",
                "source": "normal_source",
                "clip_dir": "clips_root/normal_source/clips/normal_clip",
                "start_frame": "0",
                "end_frame": "0",
                "frame_count": "1",
                "fps": "1.0",
            },
            {
                "clip_id": "buggy_clip",
                "source": "buggy_source",
                "clip_dir": "clips_root/buggy_source/clips/buggy_clip",
                "start_frame": "0",
                "end_frame": "0",
                "frame_count": "1",
                "fps": "1.0",
            },
        ],
    )
    _write_csv(
        package_root / "grouped_split.csv",
        [
            {
                "source": "normal_source",
                "category": "Physics",
                "label": "Normal",
                "split": "validation",
                "pair_id_heuristic": "reddit-1",
            },
            {
                "source": "buggy_source",
                "category": "Physics",
                "label": "Buggy",
                "split": "validation",
                "pair_id_heuristic": "reddit-1",
            },
        ],
    )
    (package_root / "glitchbench_protocol_audit.json").write_text(
        json.dumps({"claim_boundary": "bounded", "limitations": {"claim_boundary": "bounded"}}),
        encoding="utf-8",
    )
    (package_root / "k2_input_audit.json").write_text(
        json.dumps(
            {"locked_test_materialized": False, "locked_test_scored": False},
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_root / "README_KAGGLE.md").write_text("readme\n", encoding="utf-8")
    (package_root / "RUN_K2_COMMAND.txt").write_text("python run\n", encoding="utf-8")
    return package_root


def test_validate_glitchbench_bundle_accepts_synthetic_package(tmp_path: Path):
    package_root = _package_root(tmp_path)

    receipt = validate_glitchbench_bundle(package_root)

    assert receipt["status"] == "validated"


def test_validate_glitchbench_bundle_remaps_kaggle_style_paths(tmp_path: Path):
    package_root = _package_root(tmp_path)
    manifest_path = package_root / "combined_manifest.csv"
    rows = list(csv.DictReader(manifest_path.open("r", newline="", encoding="utf-8")))
    rows[0]["clip_dir"] = (
        "/kaggle/input/lewm-k2-glitchbench-inputs/clips_root/normal_source/clips/normal_clip"
    )
    rows[1]["clip_dir"] = (
        "/kaggle/input/lewm-k2-glitchbench-inputs/clips_root/buggy_source/clips/buggy_clip"
    )
    _write_csv(manifest_path, rows)

    receipt = validate_glitchbench_bundle(package_root)

    assert receipt["status"] == "validated"


def test_validate_glitchbench_bundle_rejects_missing_clip_folder(tmp_path: Path):
    package_root = _package_root(tmp_path)
    missing_dir = package_root / "clips_root" / "buggy_source"
    for path in sorted(missing_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    missing_dir.rmdir()

    with pytest.raises(FileNotFoundError, match="missing 1 clip folders"):
        validate_glitchbench_bundle(package_root)


def test_validate_glitchbench_bundle_rejects_locked_test_true(tmp_path: Path):
    package_root = _package_root(tmp_path)
    (package_root / "k2_input_audit.json").write_text(
        json.dumps({"locked_test_materialized": True, "locked_test_scored": False}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="locked_test_materialized=false"):
        validate_glitchbench_bundle(package_root)


def test_validate_glitchbench_bundle_uses_external_temp_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    package_root = _package_root(tmp_path)
    external_temp = tmp_path / "external_temp"
    before_files = sorted(path.relative_to(package_root) for path in package_root.rglob("*"))

    class _TemporaryDirectory:
        def __init__(self, *args, **kwargs) -> None:
            return None

        def __enter__(self) -> str:
            external_temp.mkdir(parents=True, exist_ok=True)
            return str(external_temp)

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr(validator_module.tempfile, "TemporaryDirectory", _TemporaryDirectory)

    receipt = validate_glitchbench_bundle(package_root)

    after_files = sorted(path.relative_to(package_root) for path in package_root.rglob("*"))
    assert receipt["status"] == "validated"
    assert before_files == after_files
    assert (external_temp / "_validator_glitchbench_records.csv").is_file()
