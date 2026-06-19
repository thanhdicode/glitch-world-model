from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.validate_wob_seed_artifacts import validate_artifacts


def _write_seed_artifact_root(tmp_path: Path, *, seed: int) -> Path:
    root = tmp_path / f"wob_seed{seed}"
    root.mkdir(parents=True)
    checkpoint_bytes = f"checkpoint-seed-{seed}".encode("utf-8")
    (root / "checkpoint_weights.pt").write_bytes(checkpoint_bytes)
    (root / "weights.pt").write_bytes(b"weights")
    (root / "best_weights.pt").write_bytes(b"best-weights")
    (root / "checkpoint.sha256").write_text(
        hashlib.sha256(checkpoint_bytes).hexdigest(),
        encoding="utf-8",
    )
    (root / "cloud_runtime_preflight.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "gpus": [{"compute_capability": [7, 5], "total_memory_gb": 15.5}],
            }
        ),
        encoding="utf-8",
    )
    (root / "preflight_passed.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "phase": "p1_train_only",
                "seed": seed,
                "train_normal_count": 48,
                "validation_normal_count": 12,
                "validation_buggy_excluded_count": 60,
                "locked_rows_skipped": 59,
                "validation_buggy_used_for_fit_select": False,
                "locked_test_materialized": False,
                "locked_test_scored": False,
                "checkpoint_selected_by": "validation_normal_only",
                "action_mode": "real",
                "action_dim": 4,
            }
        ),
        encoding="utf-8",
    )
    exact_seed42 = {
        "updates_completed": 4000,
        "best_update": 1500,
        "best_validation_loss": 0.6093359693480057,
        "validation_evaluations": 8,
        "stopped_early": True,
        "stopped_early_reason": "early_stopping_patience",
    }
    generic = {
        "updates_completed": 3500,
        "best_update": 1000,
        "best_validation_loss": 0.62,
        "validation_evaluations": 7,
        "stopped_early": True,
        "stopped_early_reason": "early_stopping_patience",
    }
    metadata_overrides = exact_seed42 if seed == 42 else generic
    (root / "training_metadata.json").write_text(
        json.dumps(
            {
                "config": {"seed": seed},
                "device": "cuda",
                "target_optimizer_updates": 15000,
                "action_dim": 4,
                "validation_buggy_used_for_fit_select": False,
                "locked_test_materialized": False,
                "locked_test_scored": False,
                "checkpoint_reload": {
                    "weights_reload_verified": True,
                    "optimizer_reload_verified": True,
                },
                **metadata_overrides,
            }
        ),
        encoding="utf-8",
    )
    (root / "loss_history.json").write_text(json.dumps([1.0, 0.8, 0.6]), encoding="utf-8")
    (root / "validation_history.json").write_text(json.dumps([0.9, 0.7, 0.65]), encoding="utf-8")
    (root / "collapse_diagnostics.json").write_text(
        json.dumps({"finite": True, "variance": 0.1}), encoding="utf-8"
    )
    (root / "best_checkpoint_metadata.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "selection_split": "validation_normal",
                "update": metadata_overrides["best_update"],
                "validation_loss": metadata_overrides["best_validation_loss"],
            }
        ),
        encoding="utf-8",
    )
    (root / "config.json").write_text(
        json.dumps({"seed": seed, "action_mode": "real"}), encoding="utf-8"
    )
    return root


@pytest.mark.parametrize("seed", [42, 43, 44])
def test_validator_accepts_supported_seed_roots(tmp_path: Path, seed: int):
    root = _write_seed_artifact_root(tmp_path, seed=seed)
    result = validate_artifacts(root, expected_seed=seed, expected_target_updates=15000)
    assert result["status"] == f"wob_seed{seed}_validated"
    assert result["seed"] == seed


def test_validator_fails_on_seed_mismatch(tmp_path: Path):
    root = _write_seed_artifact_root(tmp_path, seed=43)
    with pytest.raises(ValueError, match="seed mismatch"):
        validate_artifacts(root, expected_seed=42, expected_target_updates=15000)


def test_validator_fails_if_validation_buggy_used_for_fit_select(tmp_path: Path):
    root = _write_seed_artifact_root(tmp_path, seed=43)
    payload = json.loads((root / "training_metadata.json").read_text(encoding="utf-8"))
    payload["validation_buggy_used_for_fit_select"] = True
    (root / "training_metadata.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="fit/select"):
        validate_artifacts(root, expected_seed=43, expected_target_updates=15000)


def test_validator_fails_if_locked_test_flags_true(tmp_path: Path):
    root = _write_seed_artifact_root(tmp_path, seed=44)
    preflight = json.loads((root / "preflight_passed.json").read_text(encoding="utf-8"))
    preflight["locked_test_materialized"] = True
    (root / "preflight_passed.json").write_text(json.dumps(preflight), encoding="utf-8")
    with pytest.raises(ValueError, match="locked test materialized"):
        validate_artifacts(root, expected_seed=44, expected_target_updates=15000)

    root = _write_seed_artifact_root(tmp_path / "second", seed=44)
    metadata = json.loads((root / "training_metadata.json").read_text(encoding="utf-8"))
    metadata["locked_test_scored"] = True
    (root / "training_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="locked test scored"):
        validate_artifacts(root, expected_seed=44, expected_target_updates=15000)


def test_validator_fails_if_raw_tar_payload_present(tmp_path: Path):
    root = _write_seed_artifact_root(tmp_path, seed=43)
    (root / "raw_dataset.tar").write_bytes(b"raw")
    with pytest.raises(ValueError, match="raw WOB \\.tar payloads"):
        validate_artifacts(root, expected_seed=43, expected_target_updates=15000)
