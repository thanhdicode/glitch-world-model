from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any

EXPECTED_STATUS = "READY_FOR_WOB_P1"
EXPECTED_NORMAL_INPUT_ROOT = "/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-normal"
EXPECTED_TEST_INPUT_ROOT = "/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-test"
EXPECTED_SPLIT_CSV = "/kaggle/working/glitch-world-model/configs/wob_protocol/split.csv"
EXPECTED_PHASE = "p0_full_nonlocked"
EXPECTED_MANIFEST_SHA256 = "cc6031f304cb6c39d49567ba25a750e1f7d7e07738b471237db4f4ac8b46ea73"
EXPECTED_AUDIT_MANIFEST_SHA256 = "cefe9f32014bde5aa767d81019479d2f17fbe5fd1dfd388982e8812d4f434d22"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sha256_sidecar(path: Path) -> tuple[str, str]:
    parts = path.read_text(encoding="utf-8-sig").strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError(f"Invalid sha256 sidecar format: {path}")
    return parts[0].lower(), parts[1]


def _read_text_member(archive: tarfile.TarFile, name: str) -> str:
    member = archive.getmember(name)
    handle = archive.extractfile(member)
    if handle is None:
        raise ValueError(f"Tar member is not readable: {name}")
    return handle.read().decode("utf-8")


def _read_json_member(archive: tarfile.TarFile, name: str) -> dict[str, Any]:
    return json.loads(_read_text_member(archive, name))


def verify_wob_p0_kaggle_evidence(tar_path: Path, sidecar_path: Path) -> dict[str, Any]:
    expected_hash, sidecar_target = parse_sha256_sidecar(sidecar_path)
    actual_hash = sha256_file(tar_path)
    if actual_hash != expected_hash:
        raise ValueError(f"Tarball SHA256 mismatch. expected={expected_hash} actual={actual_hash}")

    with tarfile.open(tar_path, "r:gz") as archive:
        names = {member.name for member in archive.getmembers()}
        required = {
            "wob_kaggle_native_outputs/detected_inputs.json",
            "wob_kaggle_native_outputs/preflight.json",
            "wob_p0_materialization_audit/wob_p0_audit.json",
            "wob_p0_materialization_audit/wob_p0_audit.md",
            "wob_root/wob_root_metadata.json",
            "wob_root/wob_root_manifest.sha256",
        }
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"Missing required members: {missing}")

        tar_members = [
            member
            for member in archive.getmembers()
            if member.isfile() and member.name.endswith(".tar")
        ]
        if tar_members:
            raise ValueError(
                "Evidence bundle contains regular raw .tar payloads: "
                + ", ".join(member.name for member in tar_members[:5])
            )
        symlink_tar_members = [
            member
            for member in archive.getmembers()
            if member.issym() and member.name.endswith(".tar")
        ]

        detected_inputs = _read_json_member(
            archive, "wob_kaggle_native_outputs/detected_inputs.json"
        )
        preflight = _read_json_member(archive, "wob_kaggle_native_outputs/preflight.json")
        audit = _read_json_member(archive, "wob_p0_materialization_audit/wob_p0_audit.json")
        root_metadata = _read_json_member(archive, "wob_root/wob_root_metadata.json")
        _read_text_member(archive, "wob_root/wob_root_manifest.sha256").strip()

    checks = {
        "tarball_hash_matches_sidecar": actual_hash == expected_hash,
        "status_ready_for_wob_p1": audit["status"] == EXPECTED_STATUS,
        "normal_input_root": detected_inputs["normal_input_root"] == EXPECTED_NORMAL_INPUT_ROOT,
        "test_input_root": detected_inputs["test_input_root"] == EXPECTED_TEST_INPUT_ROOT,
        "split_csv": detected_inputs["split_csv"] == EXPECTED_SPLIT_CSV,
        "phase": detected_inputs["phase"] == EXPECTED_PHASE,
        "selected_rows": root_metadata["selected_rows"] == 120,
        "resolved_rows": root_metadata["resolved_rows"] == 120,
        "missing_rows": root_metadata["missing_rows"] == 0,
        "locked_rows_skipped": root_metadata["locked_rows_skipped"] == 59,
        "no_locked": root_metadata["no_locked"] is True,
        "locked_test_materialized": audit["locked_test_materialized"] is False,
        "locked_test_scored": audit["locked_test_scored"] is False,
        "performance_metrics_present": audit["performance_metrics_present"] is False,
        "action_metadata_present": audit["action_metadata_present"] is True,
        "semantic_action_synchronization_verified": audit[
            "semantic_action_synchronization_verified"
        ]
        is False,
        "manifest_sha256": root_metadata["manifest_sha256"] == EXPECTED_MANIFEST_SHA256,
        "audit_manifest_sha256": audit["manifest_sha256"] == EXPECTED_AUDIT_MANIFEST_SHA256,
        "gpu_name": preflight["gpu_name"] == "Tesla T4",
        "gpu_compute_capability": preflight["gpu_compute_capability"] == "sm_75",
        "future_training_gpu_ok": preflight["future_training_gpu_ok"] is True,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError("Evidence facts did not match expected values: " + ", ".join(failed))

    return {
        "status": audit["status"],
        "tarball_sha256": actual_hash,
        "sha256_sidecar_target": sidecar_target,
        "selected_rows": root_metadata["selected_rows"],
        "resolved_rows": root_metadata["resolved_rows"],
        "missing_rows": root_metadata["missing_rows"],
        "locked_rows_skipped": root_metadata["locked_rows_skipped"],
        "locked_test_materialized": audit["locked_test_materialized"],
        "locked_test_scored": audit["locked_test_scored"],
        "performance_metrics_present": audit["performance_metrics_present"],
        "action_metadata_present": audit["action_metadata_present"],
        "semantic_action_synchronization_verified": audit[
            "semantic_action_synchronization_verified"
        ],
        "manifest_sha256": root_metadata["manifest_sha256"],
        "audit_manifest_sha256": audit["manifest_sha256"],
        "gpu_name": preflight["gpu_name"],
        "gpu_compute_capability": preflight["gpu_compute_capability"],
        "future_training_gpu_ok": preflight["future_training_gpu_ok"],
        "raw_tar_regular_files_present": len(tar_members),
        "raw_tar_symlink_entries_present": len(symlink_tar_members),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the downloaded WOB-P0 Kaggle audit bundle."
    )
    parser.add_argument("--tarball", required=True, type=Path)
    parser.add_argument("--sha256", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(json.dumps(verify_wob_p0_kaggle_evidence(args.tarball, args.sha256), indent=2))


if __name__ == "__main__":
    main()
