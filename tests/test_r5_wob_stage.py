from __future__ import annotations

import json
import tarfile
from pathlib import Path

from glitch_detection import r5_wob_staged


def test_resolve_seed_inputs_repacks_extracted_seed_folder(tmp_path: Path):
    input_root = tmp_path / "input"
    extracted_root = input_root / "dataset" / "wob_seed42_artifacts" / "wob_outputs" / "wob_seed42"
    extracted_root.mkdir(parents=True)
    (extracted_root / "training_metadata.json").write_text("{}", encoding="utf-8")
    repack_root = tmp_path / "repacked"

    result = r5_wob_staged._resolve_seed_inputs(input_root, seed=42, repack_root=repack_root)

    assert result["mode"] == "repacked_extracted_folder"
    tarball = Path(result["tarball"])
    sidecar = Path(result["sidecar"])
    assert tarball.is_file()
    assert sidecar.is_file()
    with tarfile.open(tarball, "r:gz") as archive:
        assert "wob_outputs/wob_seed42/training_metadata.json" in archive.getnames()


def test_resolve_seed_inputs_direct_tarball_avoids_recursive_scan(tmp_path: Path, monkeypatch):
    input_root = tmp_path / "input"
    artifact_root = input_root / "wob-artifacts"
    artifact_root.mkdir(parents=True)
    (artifact_root / "wob_seed42_artifacts.tar.gz").write_bytes(b"seed42")
    (artifact_root / "wob_seed42_artifacts.tar.gz.sha256").write_text("hash\n", encoding="utf-8")
    repack_root = tmp_path / "repacked"

    def explode(self: Path, pattern: str):
        raise AssertionError(f"unexpected recursive scan for {self} / {pattern}")

    monkeypatch.setattr(Path, "rglob", explode)

    result = r5_wob_staged._resolve_seed_inputs(input_root, seed=42, repack_root=repack_root)

    assert result["mode"] == "direct_tarball"
    assert result["tarball"].endswith("wob_seed42_artifacts.tar.gz")


def test_validate_stage_outputs_reports_missing_markers(tmp_path: Path):
    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)
    assert result["stages"]["preflight"]["status"] == "missing"
    assert result["stages"]["validate_package"]["status"] == "missing"


def test_validate_stage_outputs_accepts_complete_marker(tmp_path: Path):
    file_path = tmp_path / "artifact.txt"
    file_path.write_text("ok", encoding="utf-8")
    marker_path = tmp_path / "stage_preflight.json"
    marker_path.write_text(
        json.dumps(
            {
                "stage": "preflight",
                "schema_version": 1,
                "status": "preflight_complete",
                "smoke": False,
                "files": {"artifact": r5_wob_staged._file_record(file_path)},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)

    assert result["stages"]["preflight"]["status"] == "complete"
    assert result["stages"]["preflight"]["summary_status"] == "preflight_complete"


def test_file_record_and_stage_validation_accept_lance_directory(tmp_path: Path):
    lance_dir = tmp_path / "_wob_train_normal.lance"
    (lance_dir / "data").mkdir(parents=True)
    (lance_dir / "data" / "part-0.bin").write_bytes(b"lance bytes")

    record = r5_wob_staged._file_record(lance_dir)
    assert record["path_type"] == "directory"

    marker_path = tmp_path / "stage_materialize_lance.json"
    marker_path.write_text(
        json.dumps(
            {
                "stage": "materialize_lance",
                "schema_version": 1,
                "status": "materialize_lance_complete",
                "smoke": False,
                "files": {"train_lance": record},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)

    assert result["stages"]["materialize_lance"]["status"] == "complete"


def test_validate_stage_outputs_rejects_smoke_mismatch(tmp_path: Path):
    marker_path = tmp_path / "stage_preflight.json"
    marker_path.write_text(
        json.dumps(
            {
                "stage": "preflight",
                "schema_version": 1,
                "status": "preflight_complete",
                "smoke": True,
                "files": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)

    assert result["stages"]["preflight"]["status"] == "invalid"
    assert "smoke mismatch" in result["stages"]["preflight"]["error"]


def test_staged_pipeline_uses_core_lance_eval_module_not_cli_wrapper():
    source = Path("src/glitch_detection/r5_wob_staged.py").read_text(encoding="utf-8")
    assert '_load_script_module("run_gate7_lance_scoring")' not in source
