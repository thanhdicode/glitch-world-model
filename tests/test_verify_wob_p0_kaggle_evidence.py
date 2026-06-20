from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from scripts.verify_wob_p0_kaggle_evidence import verify_wob_p0_kaggle_evidence


def _add_text(archive: tarfile.TarFile, name: str, text: str) -> None:
    data = text.encode("utf-8")
    info = tarfile.TarInfo(name)
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))


def _add_symlink(archive: tarfile.TarFile, name: str, target: str) -> None:
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    archive.addfile(info)


def _bundle(tmp_path: Path, *, regular_tar: bool = False) -> tuple[Path, Path]:
    tar_path = tmp_path / "wob_p0.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        _add_text(
            archive,
            "wob_kaggle_native_outputs/detected_inputs.json",
            """
{
  "normal_input_root": "/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-normal",
  "test_input_root": "/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-test",
  "split_csv": "/kaggle/working/glitch-world-model/configs/wob_protocol/split.csv",
  "phase": "p0_full_nonlocked"
}
""".strip(),
        )
        _add_text(
            archive,
            "wob_kaggle_native_outputs/preflight.json",
            """
{
  "gpu_name": "Tesla T4",
  "gpu_compute_capability": "sm_75",
  "future_training_gpu_ok": true,
  "locked_test_materialized": false,
  "locked_test_scored": false
}
""".strip(),
        )
        _add_text(
            archive,
            "wob_p0_materialization_audit/wob_p0_audit.json",
            """
{
  "status": "READY_FOR_WOB_P1",
  "locked_test_materialized": false,
  "locked_test_scored": false,
  "performance_metrics_present": false,
  "action_metadata_present": true,
  "semantic_action_synchronization_verified": false,
  "manifest_sha256": "cefe9f32014bde5aa767d81019479d2f17fbe5fd1dfd388982e8812d4f434d22"
}
""".strip(),
        )
        _add_text(
            archive,
            "wob_p0_materialization_audit/wob_p0_audit.md",
            "# audit\n",
        )
        _add_text(
            archive,
            "wob_root/wob_root_metadata.json",
            """
{
  "selected_rows": 120,
  "resolved_rows": 120,
  "missing_rows": 0,
  "locked_rows_skipped": 59,
  "no_locked": true,
  "manifest_sha256": "cc6031f304cb6c39d49567ba25a750e1f7d7e07738b471237db4f4ac8b46ea73"
}
""".strip(),
        )
        _add_text(
            archive,
            "wob_root/wob_root_manifest.sha256",
            "cc6031f304cb6c39d49567ba25a750e1f7d7e07738b471237db4f4ac8b46ea73  wob_root_manifest.csv\n",
        )
        if regular_tar:
            _add_text(archive, "wob_root/NORMAL-TRAIN/ep-0000/ep-0000.tar", "raw")
        else:
            _add_symlink(
                archive,
                "wob_root/NORMAL-TRAIN/ep-0000/ep-0000.tar",
                "/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-normal/NORMAL-TRAIN/ep-0000/ep-0000.tar",
            )
    digest = __import__("hashlib").sha256(tar_path.read_bytes()).hexdigest()
    sidecar = tmp_path / "wob_p0.tar.gz.sha256"
    sidecar.write_text(
        f"{digest}  /kaggle/working/wob_p0_kaggle_audit_outputs.tar.gz\n", encoding="utf-8"
    )
    return tar_path, sidecar


def test_verify_wob_p0_kaggle_evidence_accepts_symlinked_tar_entries(tmp_path: Path):
    tar_path, sidecar = _bundle(tmp_path)
    result = verify_wob_p0_kaggle_evidence(tar_path, sidecar)
    assert result["status"] == "READY_FOR_WOB_P1"
    assert result["raw_tar_regular_files_present"] == 0
    assert result["raw_tar_symlink_entries_present"] == 1


def test_verify_wob_p0_kaggle_evidence_rejects_regular_tar_payloads(tmp_path: Path):
    tar_path, sidecar = _bundle(tmp_path, regular_tar=True)
    with pytest.raises(ValueError, match="regular raw .tar payloads"):
        verify_wob_p0_kaggle_evidence(tar_path, sidecar)
