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

SUPPORTED_SEEDS = {42, 43, 44}
METADATA_PREFIX = "wob_p1_metadata/"
SEED42_EXACT_EXPECTATIONS = {
    "updates_completed": 4000,
    "best_update": 1500,
    "best_validation_loss": 0.6093359693480057,
    "validation_evaluations": 8,
    "stopped_early": True,
    "stopped_early_reason": "early_stopping_patience",
}


def seed_name(seed: int) -> str:
    if seed not in SUPPORTED_SEEDS:
        raise ValueError(f"Unsupported WOB seed: {seed}")
    return f"wob_seed{seed}"


def validator_status(seed: int) -> str:
    return f"{seed_name(seed)}_validated"


def phase_name(seed: int) -> str:
    return f"wob_p1_seed{seed}"


def tarball_prefix(seed: int) -> str:
    return f"wob_outputs/{seed_name(seed)}/"


def required_tarball_files(seed: int) -> tuple[str, ...]:
    prefix = tarball_prefix(seed)
    return tuple(f"{prefix}{name}" for name in REQUIRED_FILES) + (
        f"{prefix}artifact_manifest.json",
        f"{prefix}validator_report.json",
        f"{METADATA_PREFIX}wob_p1_selected_split.csv",
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _assert_false_if_present(payload: dict[str, Any], key: str, errors: list[str]) -> None:
    if key in payload:
        _assert(payload.get(key) is False, f"{key} must remain false", errors)


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


def _validate_runtime_and_preflight(
    runtime: dict[str, Any],
    preflight: dict[str, Any],
    *,
    expected_seed: int,
    errors: list[str],
) -> None:
    _assert(runtime.get("status") == "passed", "cloud runtime preflight did not pass", errors)
    gpus = runtime.get("gpus", [])
    _assert(bool(gpus), "cloud runtime preflight has no GPU records", errors)
    for gpu in gpus:
        capability = gpu.get("compute_capability", [0, 0])
        _assert(int(capability[0]) >= 7, f"GPU compute below sm_70: {capability}", errors)
        total_memory_gb = gpu.get("total_memory_gb")
        if total_memory_gb is None:
            total_memory_gb = gpu.get("vram_gb", 0.0)
        _assert(float(total_memory_gb) >= 14.0, "GPU VRAM below 14 GB", errors)

    _assert(preflight.get("status") == "passed", "preflight status is not passed", errors)
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
        preflight.get("checkpoint_selected_by") == "validation_normal_only",
        "checkpoint selection rule mismatch",
        errors,
    )
    _assert(preflight.get("action_mode") in {None, "real"}, "action mode must remain real", errors)
    if preflight.get("action_dim") is not None:
        _assert(preflight.get("action_dim") == 4, "preflight action_dim mismatch", errors)
    _assert(preflight.get("locked_test_materialized") is False, "locked test materialized", errors)
    _assert(preflight.get("locked_test_scored") is False, "locked test scored", errors)
    _assert_false_if_present(preflight, "evaluation_run", errors)


def _validate_metadata_payloads(
    metadata: dict[str, Any],
    best_metadata: dict[str, Any],
    loss_history: Any,
    validation_history: Any,
    diagnostics: dict[str, Any],
    config_json: dict[str, Any],
    *,
    expected_seed: int,
    expected_target_updates: int,
    errors: list[str],
) -> None:
    _assert(metadata.get("config", {}).get("seed") == expected_seed, "seed mismatch", errors)
    _assert(metadata.get("device") == "cuda", "device is not cuda", errors)
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
        "metadata reports validation-buggy fit/select",
        errors,
    )
    _assert(metadata.get("locked_test_materialized") is False, "locked test materialized", errors)
    _assert(metadata.get("locked_test_scored") is False, "locked test scored", errors)
    _assert_false_if_present(metadata, "evaluation_run", errors)
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
    if "scheduler_reload_verified" in reload_report:
        _assert(
            reload_report.get("scheduler_reload_verified") in {True, None},
            "scheduler reload verification failed",
            errors,
        )

    _assert(
        best_metadata.get("selection_split") == "validation_normal",
        "selection split mismatch",
        errors,
    )
    _assert(
        best_metadata.get("seed") in {None, expected_seed}, "best metadata seed mismatch", errors
    )
    _assert(bool(loss_history), "loss history is empty", errors)
    _assert(bool(validation_history), "validation history is empty", errors)
    _assert(bool(config_json), "config.json is empty", errors)
    _finite_numbers(metadata, label="training_metadata", errors=errors)
    _finite_numbers(best_metadata, label="best_checkpoint_metadata", errors=errors)
    _finite_numbers(loss_history, label="loss_history", errors=errors)
    _finite_numbers(validation_history, label="validation_history", errors=errors)
    _finite_numbers(diagnostics, label="collapse_diagnostics", errors=errors)
    _assert(diagnostics.get("finite") is True, "collapse diagnostics finite flag mismatch", errors)

    if expected_seed == 42:
        for key, expected in SEED42_EXACT_EXPECTATIONS.items():
            _assert(metadata.get(key) == expected, f"seed42 {key} mismatch", errors)
        _assert(
            best_metadata.get("update") == SEED42_EXACT_EXPECTATIONS["best_update"],
            "seed42 best checkpoint update mismatch",
            errors,
        )
        _assert(
            best_metadata.get("validation_loss")
            in {None, SEED42_EXACT_EXPECTATIONS["best_validation_loss"]}
            or math.isclose(
                float(best_metadata.get("validation_loss")),
                SEED42_EXACT_EXPECTATIONS["best_validation_loss"],
                rel_tol=0.0,
                abs_tol=1e-12,
            ),
            "seed42 best checkpoint validation loss mismatch",
            errors,
        )


def _validate_selected_split_text(selected_split_text: str, errors: list[str]) -> None:
    selected_rows = list(csv.DictReader(selected_split_text.splitlines()))
    _assert(len(selected_rows) == 60, "selected split row count mismatch", errors)
    _assert(
        all(row["label"] == "Normal" for row in selected_rows),
        "selected split contains non-normal rows",
        errors,
    )


def _validate_artifact_manifest(
    artifact_manifest: dict[str, Any],
    validator_report: dict[str, Any],
    *,
    expected_seed: int,
    errors: list[str],
) -> None:
    _assert(artifact_manifest.get("phase") == phase_name(expected_seed), "phase mismatch", errors)
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
        artifact_manifest.get("locked_test_materialized") is False,
        "artifact manifest reports locked-test materialization",
        errors,
    )
    _assert(
        artifact_manifest.get("locked_test_scored") is False,
        "artifact manifest reports locked-test scoring",
        errors,
    )
    _assert_false_if_present(artifact_manifest, "evaluation_run", errors)
    _assert(
        validator_report.get("status") == validator_status(expected_seed),
        "validator report status mismatch",
        errors,
    )

    if expected_seed == 42:
        _assert(
            artifact_manifest.get("updates_completed")
            == SEED42_EXACT_EXPECTATIONS["updates_completed"],
            "seed42 artifact updates_completed mismatch",
            errors,
        )
        _assert(
            artifact_manifest.get("best_validation_loss")
            == SEED42_EXACT_EXPECTATIONS["best_validation_loss"],
            "seed42 artifact best validation loss mismatch",
            errors,
        )


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
    raw_tar_members = [
        str(path.relative_to(artifact_root)) for path in artifact_root.rglob("*.tar")
    ]
    _assert(not raw_tar_members, "artifact root contains raw WOB .tar payloads", errors)
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

    _validate_runtime_and_preflight(runtime, preflight, expected_seed=expected_seed, errors=errors)
    _validate_metadata_payloads(
        metadata,
        best_metadata,
        loss_history,
        validation_history,
        diagnostics,
        config_json,
        expected_seed=expected_seed,
        expected_target_updates=expected_target_updates,
        errors=errors,
    )

    checkpoint_hash = (artifact_root / "checkpoint.sha256").read_text(encoding="utf-8-sig").strip()
    _assert(
        checkpoint_hash == _sha256_file(artifact_root / "checkpoint_weights.pt"),
        "checkpoint.sha256 does not match checkpoint_weights.pt",
        errors,
    )

    artifact_manifest_path = artifact_root / "artifact_manifest.json"
    validator_report_path = artifact_root / "validator_report.json"
    if artifact_manifest_path.is_file() and validator_report_path.is_file():
        _validate_artifact_manifest(
            _read_json(artifact_manifest_path),
            _read_json(validator_report_path),
            expected_seed=expected_seed,
            errors=errors,
        )

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": validator_status(expected_seed),
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

    prefix = tarball_prefix(expected_seed)
    errors: list[str] = []
    with tarfile.open(tarball, "r:gz") as archive:
        members = archive.getmembers()
        names = {member.name for member in members}
        missing = sorted(set(required_tarball_files(expected_seed)) - names)
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

        runtime = _read_json_member(archive, f"{prefix}cloud_runtime_preflight.json")
        preflight = _read_json_member(archive, f"{prefix}preflight_passed.json")
        metadata = _read_json_member(archive, f"{prefix}training_metadata.json")
        loss_history = _read_json_member(archive, f"{prefix}loss_history.json")
        validation_history = _read_json_member(archive, f"{prefix}validation_history.json")
        diagnostics = _read_json_member(archive, f"{prefix}collapse_diagnostics.json")
        best_metadata = _read_json_member(archive, f"{prefix}best_checkpoint_metadata.json")
        config_json = _read_json_member(archive, f"{prefix}config.json")
        artifact_manifest = _read_json_member(archive, f"{prefix}artifact_manifest.json")
        validator_report = _read_json_member(archive, f"{prefix}validator_report.json")
        selected_split_text = _read_text_member(
            archive, f"{METADATA_PREFIX}wob_p1_selected_split.csv"
        )

        _validate_runtime_and_preflight(
            runtime, preflight, expected_seed=expected_seed, errors=errors
        )
        _validate_metadata_payloads(
            metadata,
            best_metadata,
            loss_history,
            validation_history,
            diagnostics,
            config_json,
            expected_seed=expected_seed,
            expected_target_updates=expected_target_updates,
            errors=errors,
        )
        _validate_artifact_manifest(
            artifact_manifest,
            validator_report,
            expected_seed=expected_seed,
            errors=errors,
        )
        _validate_selected_split_text(selected_split_text, errors)

        checkpoint_hash = _read_text_member(archive, f"{prefix}checkpoint.sha256").strip()
        _assert(
            checkpoint_hash == _sha256_tar_member(archive, f"{prefix}checkpoint_weights.pt"),
            "checkpoint.sha256 does not match checkpoint_weights.pt",
            errors,
        )

        if errors:
            raise ValueError("; ".join(errors))
        return {
            "status": validator_status(expected_seed),
            "tarball": str(tarball),
            "tarball_sha256": actual_hash,
            "sha256_sidecar_target": sidecar_target,
            "artifact_entries": len(members),
            "raw_wob_tar_regular_files": 0,
            "seed": expected_seed,
            "target_optimizer_updates": expected_target_updates,
            "updates_completed": metadata.get("updates_completed"),
            "best_update": metadata.get("best_update"),
            "best_validation_loss": metadata.get("best_validation_loss"),
            "train_normal_count": 48,
            "validation_normal_count": 12,
            "validation_buggy_excluded_count": 60,
            "locked_rows_skipped": 59,
            "validation_buggy_used_for_fit_select": False,
            "locked_test_materialized": False,
            "locked_test_scored": False,
            "evaluation_run": False,
        }


def build_parser(*, description: str, default_seed: int) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--artifact-root", type=Path)
    source.add_argument("--tarball", type=Path)
    parser.add_argument("--sha256", type=Path)
    parser.add_argument("--expected-seed", default=default_seed, type=int)
    parser.add_argument("--expected-target-updates", default=15000, type=int)
    return parser


def run_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.expected_seed not in SUPPORTED_SEEDS:
        raise SystemExit(f"--expected-seed must be one of {sorted(SUPPORTED_SEEDS)}")
    if args.tarball is not None:
        if args.sha256 is None:
            raise SystemExit("--sha256 is required with --tarball")
        return validate_artifact_tarball(
            args.tarball,
            args.sha256,
            expected_seed=args.expected_seed,
            expected_target_updates=args.expected_target_updates,
        )
    return validate_artifacts(
        args.artifact_root,
        expected_seed=args.expected_seed,
        expected_target_updates=args.expected_target_updates,
    )


def main(argv: list[str] | None = None) -> None:
    parser = build_parser(
        description="Validate WOB seed training artifacts for seeds 42, 43, or 44.",
        default_seed=42,
    )
    args = parser.parse_args(argv)
    result = run_from_args(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
