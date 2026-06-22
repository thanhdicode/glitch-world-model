from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest


def _load_validator():
    path = Path("scripts/validate_r5_xgame_output_bundle.py")
    spec = importlib.util.spec_from_file_location("r5_xgame_bundle_validator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _valid_output(tmp_path: Path) -> tuple[Path, Path]:
    frozen = Path("configs/wob_protocol/r5_xgame_split.csv")
    output = tmp_path / "output"
    output.mkdir()
    shutil.copyfile(frozen, output / "r5_xgame_manifest.csv")
    for name in (
        "r5_xgame_window_manifest.csv",
        "r5_xgame_baseline_scores.csv",
        "r5_xgame_episode_scores.csv",
        "r5_xgame_comparison.csv",
    ):
        (output / name).write_text("value\n", encoding="utf-8")
    for seed in (42, 43, 44):
        (output / f"r5_xgame_lewm_scores_seed{seed}.csv").write_text("value\n", encoding="utf-8")
    (output / "R5_XGAME_REPORT.md").write_text("report\n", encoding="utf-8")
    (output / "stage_preflight.json").write_text("{}\n", encoding="utf-8")
    manifest_hash = _load_validator().sha256(frozen)
    (output / "r5_xgame_metrics.json").write_text(
        json.dumps(
            {
                "auroc": 0.5,
                "auprc": 0.5,
                "f1": 0.5,
                "precision": 0.5,
                "recall": 0.5,
                "fpr_at_95_tpr": 0.5,
                "balanced_accuracy": 0.5,
            }
        ),
        encoding="utf-8",
    )
    (output / "r5_xgame_provenance.json").write_text(
        json.dumps(
            {
                "git_commit": "abc",
                "manifest_sha256": manifest_hash,
                "role_counts": {"train_normal": 36},
                "seeds": [42, 43, 44],
                "train_role_sha256": "a",
                "calibration_role_sha256": "b",
                "evaluation_role_sha256": "c",
                "locked_test_materialized": False,
                "locked_test_scored": False,
                "validation_buggy_used_for_fit_select": False,
                "old_r5_wob_checkpoint_reused": False,
            }
        ),
        encoding="utf-8",
    )
    return output, frozen


def test_validator_rejects_incomplete_output(tmp_path: Path):
    validator = _load_validator()
    with pytest.raises(ValueError, match="incomplete"):
        validator.validate_output_dir(tmp_path, Path("configs/wob_protocol/r5_xgame_split.csv"))


def test_validator_accepts_minimal_safe_structure(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    result = validator.validate_output_dir(output, frozen)
    assert result["status"] == "r5_xgame_output_validated"


def test_validator_rejects_unsafe_provenance(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    provenance_path = output / "r5_xgame_provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["old_r5_wob_checkpoint_reused"] = True
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="Old R5-WOB"):
        validator.validate_output_dir(output, frozen)
