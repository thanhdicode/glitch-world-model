from __future__ import annotations

import argparse
import hashlib
import json
import math
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate WOB seed42 training artifacts.")
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--expected-seed", required=True, type=int)
    parser.add_argument("--expected-target-updates", required=True, type=int)
    args = parser.parse_args(argv)
    result = validate_artifacts(
        args.artifact_root,
        expected_seed=args.expected_seed,
        expected_target_updates=args.expected_target_updates,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
