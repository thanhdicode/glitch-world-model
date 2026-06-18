from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import tarfile
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "cloud_runtime_preflight.json",
    "preflight_passed.json",
    "training_metadata.json",
    "loss_history.json",
    "validation_history.json",
    "collapse_diagnostics.json",
    "checkpoint_weights.pt",
    "weights.pt",
    "best_weights.pt",
    "best_checkpoint_metadata.json",
    "config.json",
    "checkpoint.sha256",
)

TARBALL_PREFIX = "wob_outputs/wob_seed42/"
METADATA_PREFIX = "wob_p1_metadata/"
REQUIRED_TARBALL_FILES = tuple(f"{TARBALL_PREFIX}{name}" for name in REQUIRED_FILES) + (
    f"{TARBALL_PREFIX}artifact_manifest.json",
    f"{TARBALL_PREFIX}validator_report.json",
    f"{METADATA_PREFIX}wob_p1_selected_split.csv",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _finite_numbers(payload: Any, *, label: str, errors: list[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _finite_numbers(value, label=f"{label}.{key}", errors=errors)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _finite_numbers(value, label=f"{label}[{index}]", errors=errors)
    elif isinstance(payload, int | float):
        if not math.isfinite(float(payload)):
            errors.append(f"{label} is not finite")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_tar_member(archive: tarfile.TarFile, name: str) -> str:
    digest = hashlib.sha256()
    handle = archive.extractfile(name)
    if handle is None:
        raise ValueError(f"Tar member is not readable: {name}")
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _parse_sha256_sidecar(path: Path) -> tuple[str, str]:
    parts = path.read_text(encoding="utf-8-sig").strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError(f"Invalid sha256 sidecar format: {path}")
    return parts[0].lower(), parts[1]


def _read_text_member(archive: tarfile.TarFile, name: str) -> str:
    handle = archive.extractfile(name)
    if handle is None:
        raise ValueError(f"Tar member is not readable: {name}")
    return handle.read().decode("utf-8-sig")


def _read_json_member(archive: tarfile.TarFile, name: str) -> Any:
    return json.loads(_read_text_member(archive, name))


def validate_artifacts(
    artifact_root: Path,
    *,
    expected_seed: int,
    expected_target_updates: int,
) -> dict[str, Any]:
    errors: list[str] = []
    _assert(artifact_root.is_dir(), f"artifact root does not exist: {artifact_root}", errors)
    for name in REQUIRED_FILES:
        _assert((artifact_root / name).is_file(), f"missing required artifact: {name}", errors)
    if errors:
        raise ValueError("; ".join(errors))

    runtime = _read_json(artifact_root / "cloud_runtime_preflight.json")
    preflight = _read_json(artifact_root / "preflight_passed.json")
    metadata = _read_json(artifact_root / "training_metadata.json")
    loss_history = _read_json(artifact_root / "loss_history.json")
    validation_history = _read_json(artifact_root / "validation_history.json")
    diagnostics = _read_json(artifact_root / "collapse_diagnostics.json")
    best_metadata = _read_json(artifact_root / "best_checkpoint_metadata.json")
    config_json = _read_json(artifact_root / "config.json")

    _assert(runtime.get("status") == "passed", "cloud runtime preflight did not pass", errors)
    gpus = runtime.get("gpus", [])
    _assert(bool(gpus), "cloud runtime preflight has no GPU records", errors)
    for gpu in gpus:
        capability = gpu.get("compute_capability", [0, 0])
        _assert(
            int(capability[0]) >= 7, f"GPU compute capability below sm_70: {capability}", errors
        )
        _assert(float(gpu.get("total_memory_gb", 0.0)) >= 14.0, "GPU VRAM below 14 GB", errors)
    _assert(preflight.get("status") == "passed", "preflight_passed.json is not passed", errors)
    _assert(preflight.get("phase") == "p1_train_only", "phase is not p1_train_only", errors)
    _assert(preflight.get("seed") == expected_seed, "seed mismatch", errors)
    _assert(preflight.get("train_normal_count") == 48, "train-normal count mismatch", errors)
    _assert(
        preflight.get("validation_normal_count") == 12,
        "validation-normal count mismatch",
        errors,
    )
    _assert(
        preflight.get("validation_buggy_excluded_count") == 60,
        "validation-buggy excluded count mismatch",
        errors,
    )
    _assert(preflight.get("locked_rows_skipped") == 59, "locked rows skipped mismatch", errors)
    _assert(
        preflight.get("locked_test_materialized") is False,
        "locked test materialized",
        errors,
    )
    _assert(preflight.get("locked_test_scored") is False, "locked test scored", errors)
    _assert(metadata.get("config", {}).get("seed") == expected_seed, "seed mismatch", errors)
    _assert(
        metadata.get("target_optimizer_updates") == expected_target_updates,
        "target optimizer update count mismatch",
        errors,
    )
    _assert(
        metadata.get("action_dim") == 4, "action_dim must be 4 for WOB real-action runs", errors
    )
    _assert(
        metadata.get("validation_buggy_used_for_fit_select") is False,
        "validation-buggy was used for fit/select",
        errors,
    )
    _assert(metadata.get("locked_test_materialized") is False, "locked test materialized", errors)
    _assert(metadata.get("locked_test_scored") is False, "locked test scored", errors)
    _assert(
        best_metadata.get("selection_split") == "validation_normal",
        "selection split mismatch",
        errors,
    )
    _assert(bool(loss_history), "loss history is empty", errors)
    _assert(bool(validation_history), "validation history is empty", errors)
    _assert(bool(config_json), "config.json is empty", errors)
    _finite_numbers(loss_history, label="loss_history", errors=errors)
    _finite_numbers(validation_history, label="validation_history", errors=errors)
    _finite_numbers(diagnostics, label="collapse_diagnostics", errors=errors)
    _assert(
        diagnostics.get("finite") is True, "collapse diagnostics finite flag is not true", errors
    )
    checkpoint_hash = (artifact_root / "checkpoint.sha256").read_text(encoding="utf-8-sig").strip()
    _assert(
        checkpoint_hash == _sha256_file(artifact_root / "checkpoint_weights.pt"),
        "checkpoint.sha256 does not match checkpoint_weights.pt",
        errors,
    )

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "wob_seed42_validated",
        "artifact_root": str(artifact_root),
        "seed": expected_seed,
        "target_optimizer_updates": expected_target_updates,
        "train_normal_count": preflight["train_normal_count"],
        "validation_normal_count": preflight["validation_normal_count"],
        "validation_buggy_excluded_count": preflight["validation_buggy_excluded_count"],
        "locked_rows_skipped": preflight["locked_rows_skipped"],
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def validate_artifact_tarball(
    tarball: Path,
    sidecar: Path,
    *,
    expected_seed: int,
    expected_target_updates: int,
) -> dict[str, Any]:
    expected_hash, sidecar_target = _parse_sha256_sidecar(sidecar)
    actual_hash = _sha256_file(tarball)
    if actual_hash != expected_hash:
        raise ValueError(f"Tarball SHA256 mismatch. expected={expected_hash} actual={actual_hash}")

    errors: list[str] = []
    with tarfile.open(tarball, "r:gz") as archive:
        members = archive.getmembers()
        names = {member.name for member in members}
        missing = sorted(set(REQUIRED_TARBALL_FILES) - names)
        if missing:
            raise ValueError(f"Missing required tarball members: {missing}")
        raw_tar_members = [
            member.name for member in members if member.isfile() and member.name.endswith(".tar")
        ]
        if raw_tar_members:
            raise ValueError(
                "Artifact bundle contains regular raw WOB .tar payloads: "
                + ", ".join(raw_tar_members[:5])
            )

        runtime = _read_json_member(archive, f"{TARBALL_PREFIX}cloud_runtime_preflight.json")
        preflight = _read_json_member(archive, f"{TARBALL_PREFIX}preflight_passed.json")
        metadata = _read_json_member(archive, f"{TARBALL_PREFIX}training_metadata.json")
        loss_history = _read_json_member(archive, f"{TARBALL_PREFIX}loss_history.json")
        validation_history = _read_json_member(archive, f"{TARBALL_PREFIX}validation_history.json")
        diagnostics = _read_json_member(archive, f"{TARBALL_PREFIX}collapse_diagnostics.json")
        best_metadata = _read_json_member(archive, f"{TARBALL_PREFIX}best_checkpoint_metadata.json")
        config_json = _read_json_member(archive, f"{TARBALL_PREFIX}config.json")
        artifact_manifest = _read_json_member(archive, f"{TARBALL_PREFIX}artifact_manifest.json")
        validator_report = _read_json_member(archive, f"{TARBALL_PREFIX}validator_report.json")
        selected_split_text = _read_text_member(
            archive, f"{METADATA_PREFIX}wob_p1_selected_split.csv"
        )

        _assert(artifact_manifest.get("phase") == "wob_p1_seed42", "phase mismatch", errors)
        _assert(
            artifact_manifest.get("training_completed") is True,
            "training was not completed",
            errors,
        )
        _assert(
            artifact_manifest.get("validator_passed") is True,
            "artifact manifest does not report validator pass",
            errors,
        )
        _assert(
            artifact_manifest.get("training_status") == "research_update_run_complete_unvalidated",
            "training status mismatch",
            errors,
        )
        _assert(
            artifact_manifest.get("updates_completed") == 4000,
            "artifact updates_completed mismatch",
            errors,
        )
        _assert(
            artifact_manifest.get("best_validation_loss") == 0.6093359693480057,
            "artifact best validation loss mismatch",
            errors,
        )
        _assert(
            artifact_manifest.get("locked_test_materialized") is False,
            "artifact manifest reports locked-test materialization",
            errors,
        )
        _assert(
            artifact_manifest.get("locked_test_scored") is False,
            "artifact manifest reports locked-test scoring",
            errors,
        )
        _assert(
            artifact_manifest.get("evaluation_run") is False,
            "artifact manifest reports evaluation run",
            errors,
        )

        _assert(runtime.get("status") == "passed", "cloud runtime preflight did not pass", errors)
        for gpu in runtime.get("gpus", []):
            capability = gpu.get("compute_capability", [0, 0])
            _assert(int(capability[0]) >= 7, f"GPU compute below sm_70: {capability}", errors)
            _assert(float(gpu.get("total_memory_gb", 0.0)) >= 14.0, "GPU VRAM below 14 GB", errors)
        _assert(preflight.get("phase") == "p1_train_only", "preflight phase mismatch", errors)
        _assert(preflight.get("seed") == expected_seed, "preflight seed mismatch", errors)
        _assert(preflight.get("train_normal_count") == 48, "train-normal count mismatch", errors)
        _assert(
            preflight.get("validation_normal_count") == 12,
            "validation-normal count mismatch",
            errors,
        )
        _assert(
            preflight.get("validation_buggy_excluded_count") == 60,
            "validation-buggy excluded count mismatch",
            errors,
        )
        _assert(preflight.get("locked_rows_skipped") == 59, "locked rows skipped mismatch", errors)
        _assert(
            preflight.get("validation_buggy_used_for_fit_select") is False,
            "validation-buggy was used for fit/select",
            errors,
        )
        _assert(
            preflight.get("locked_test_materialized") is False, "locked test materialized", errors
        )
        _assert(preflight.get("locked_test_scored") is False, "locked test scored", errors)

        _assert(metadata.get("config", {}).get("seed") == expected_seed, "seed mismatch", errors)
        _assert(metadata.get("device") == "cuda", "device is not cuda", errors)
        _assert(metadata.get("action_dim") == 4, "action_dim mismatch", errors)
        _assert(
            metadata.get("target_optimizer_updates") == expected_target_updates,
            "target optimizer update count mismatch",
            errors,
        )
        _assert(metadata.get("updates_completed") == 4000, "metadata updates mismatch", errors)
        _assert(
            metadata.get("validation_evaluations") == 8,
            "validation evaluation count mismatch",
            errors,
        )
        _assert(metadata.get("best_update") == 1500, "best update mismatch", errors)
        _assert(
            metadata.get("best_validation_loss") == 0.6093359693480057,
            "metadata best validation loss mismatch",
            errors,
        )
        _assert(metadata.get("stopped_early") is True, "early stopping flag mismatch", errors)
        _assert(
            metadata.get("stopped_early_reason") == "early_stopping_patience",
            "early stopping reason mismatch",
            errors,
        )
        reload_report = metadata.get("checkpoint_reload", {})
        _assert(
            reload_report.get("weights_reload_verified") is True,
            "weights reload was not verified",
            errors,
        )
        _assert(
            reload_report.get("optimizer_reload_verified") is True,
            "optimizer reload was not verified",
            errors,
        )
        _assert(
            metadata.get("validation_buggy_used_for_fit_select") is False,
            "metadata reports validation-buggy fit/select",
            errors,
        )
        _assert(
            metadata.get("locked_test_materialized") is False, "locked test materialized", errors
        )
        _assert(metadata.get("locked_test_scored") is False, "locked test scored", errors)

        _assert(
            best_metadata.get("selection_split") == "validation_normal",
            "selection split mismatch",
            errors,
        )
        _assert(best_metadata.get("update") == 1500, "best checkpoint update mismatch", errors)
        _assert(bool(loss_history), "loss history is empty", errors)
        _assert(bool(validation_history), "validation history is empty", errors)
        _assert(bool(config_json), "config.json is empty", errors)
        _finite_numbers(loss_history, label="loss_history", errors=errors)
        _finite_numbers(validation_history, label="validation_history", errors=errors)
        _finite_numbers(diagnostics, label="collapse_diagnostics", errors=errors)
        _assert(
            diagnostics.get("finite") is True, "collapse diagnostics finite flag mismatch", errors
        )
        checkpoint_hash = _read_text_member(archive, f"{TARBALL_PREFIX}checkpoint.sha256").strip()
        _assert(
            checkpoint_hash
            == _sha256_tar_member(archive, f"{TARBALL_PREFIX}checkpoint_weights.pt"),
            "checkpoint.sha256 does not match checkpoint_weights.pt",
            errors,
        )

        selected_rows = list(csv.DictReader(selected_split_text.splitlines()))
        _assert(len(selected_rows) == 60, "selected split row count mismatch", errors)
        _assert(
            all(row["label"] == "Normal" for row in selected_rows),
            "selected split contains non-normal rows",
            errors,
        )
        _assert(
            validator_report.get("status") == "wob_seed42_validated",
            "validator report status mismatch",
            errors,
        )

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "wob_seed42_validated",
        "tarball": str(tarball),
        "tarball_sha256": actual_hash,
        "sha256_sidecar_target": sidecar_target,
        "artifact_entries": len(members),
        "raw_wob_tar_regular_files": 0,
        "seed": expected_seed,
        "target_optimizer_updates": expected_target_updates,
        "updates_completed": 4000,
        "best_update": 1500,
        "best_validation_loss": 0.6093359693480057,
        "train_normal_count": 48,
        "validation_normal_count": 12,
        "validation_buggy_excluded_count": 60,
        "locked_rows_skipped": 59,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": False,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate WOB seed42 training artifacts.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--artifact-root", type=Path)
    source.add_argument("--tarball", type=Path)
    parser.add_argument("--sha256", type=Path)
    parser.add_argument("--expected-seed", default=42, type=int)
    parser.add_argument("--expected-target-updates", default=15000, type=int)
    args = parser.parse_args(argv)
    if args.tarball is not None:
        if args.sha256 is None:
            raise SystemExit("--sha256 is required with --tarball")
        result = validate_artifact_tarball(
            args.tarball,
            args.sha256,
            expected_seed=args.expected_seed,
            expected_target_updates=args.expected_target_updates,
        )
    else:
        result = validate_artifacts(
            args.artifact_root,
            expected_seed=args.expected_seed,
            expected_target_updates=args.expected_target_updates,
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
