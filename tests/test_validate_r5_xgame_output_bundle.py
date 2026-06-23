from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import tarfile
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
    validator = _load_validator()
    frozen = Path("configs/wob_protocol/r5_xgame_split.csv")
    output = tmp_path / "output"
    output.mkdir()
    shutil.copyfile(frozen, output / "r5_xgame_manifest.csv")
    for name in (
        "r5_xgame_window_manifest.csv",
        "r5_xgame_baseline_scores.csv",
        "r5_xgame_comparison.csv",
    ):
        (output / name).write_text("value\n", encoding="utf-8")
    for seed in (42, 43, 44):
        (output / f"r5_xgame_lewm_scores_seed{seed}.csv").write_text(
            "window_id,mse_t1,mse_t2,mse_t3,l2_t1,l2_t2,l2_t3\n",
            encoding="utf-8",
        )
    with (output / "r5_xgame_episode_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method_family",
                "method",
                "window_scorer",
                "seed",
                "episode_aggregation",
                "source_episode_id",
                "source",
                "pair_id",
                "category",
                "label",
                "dataset_name",
                "evaluation_role",
                "window_count",
                "score",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "method_family": "baseline",
                "method": "frame_diff",
                "window_scorer": "frame_diff",
                "seed": "",
                "episode_aggregation": "mean",
                "source_episode_id": "normal/eval",
                "source": "NORMAL-TRAIN/eval.tar",
                "pair_id": "normal/eval",
                "category": "world_of_bugs",
                "label": "Normal",
                "dataset_name": "normal_validation",
                "evaluation_role": "evaluation",
                "window_count": "1",
                "score": "0.1",
            }
        )
        writer.writerow(
            {
                "method_family": "baseline",
                "method": "frame_diff",
                "window_scorer": "frame_diff",
                "seed": "",
                "episode_aggregation": "mean",
                "source_episode_id": "buggy/eval",
                "source": "TEST/eval.tar",
                "pair_id": "buggy/eval",
                "category": "world_of_bugs",
                "label": "Buggy",
                "dataset_name": "buggy_probe",
                "evaluation_role": "evaluation",
                "window_count": "1",
                "score": "0.9",
            }
        )
    (output / "R5_XGAME_REPORT.md").write_text("report\n", encoding="utf-8")
    manifest_hash = validator.sha256(frozen)
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
                "results": [{"method": "frame_diff"}],
                "locked_test_materialized": False,
                "locked_test_scored": False,
                "validation_buggy_used_for_fit_select": False,
            }
        ),
        encoding="utf-8",
    )
    (output / "r5_xgame_provenance.json").write_text(
        json.dumps(
            {
                "git_commit": "abc",
                "manifest_sha256": manifest_hash,
                "role_counts": {
                    "train_normal": 36,
                    "calibration_normal": 12,
                    "evaluation_normal_negative": 12,
                    "evaluation_buggy_positive": 60,
                },
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
    for name in validator.REQUIRED_STAGE_MARKERS:
        (output / name).write_text("{}\n", encoding="utf-8")
    tarball = output / "r5_xgame_outputs.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        for path in sorted(output.iterdir()):
            if path.name == tarball.name or path.suffix == ".sha256":
                continue
            archive.add(path, arcname=path.name)
    (output / "r5_xgame_outputs.tar.gz.sha256").write_text(
        f"{validator.sha256(tarball)}  {tarball.name}\n",
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
    assert result["manifest_raw_sha256_match"] is True
    assert result["manifest_normalized_sha256_match"] is True


def test_validator_rejects_one_class_evaluation(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    rows = list(csv.DictReader((output / "r5_xgame_episode_scores.csv").open(encoding="utf-8")))
    for row in rows:
        row["label"] = "Normal"
    with (output / "r5_xgame_episode_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="both evaluation classes"):
        validator.validate_output_dir(output, frozen)


def test_validator_rejects_unsafe_provenance(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    provenance_path = output / "r5_xgame_provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["old_r5_wob_checkpoint_reused"] = True
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="Old R5-WOB"):
        validator.validate_output_dir(output, frozen)


def test_validator_accepts_tarball_pair(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    result = validator.validate_tarball(
        output / "r5_xgame_outputs.tar.gz",
        output / "r5_xgame_outputs.tar.gz.sha256",
        frozen,
    )
    assert result["status"] == "r5_xgame_tarball_validated"


def test_validator_refuses_missing_stage_lewm_score_marker(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    (output / "stage_lewm_score.json").unlink()
    with pytest.raises(ValueError, match="stage_lewm_score.json"):
        validator.validate_output_dir(output, frozen)


def test_validator_accepts_manifest_with_crlf_frozen_and_lf_output(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    lf_manifest = (output / "r5_xgame_manifest.csv").read_text(encoding="utf-8")
    (output / "r5_xgame_manifest.csv").write_text(
        lf_manifest.replace("\r\n", "\n"), encoding="utf-8"
    )
    frozen_crlf = tmp_path / "frozen_crlf.csv"
    frozen_text = frozen.read_text(encoding="utf-8")
    frozen_crlf.write_text(frozen_text.replace("\n", "\r\n"), encoding="utf-8")
    result = validator.validate_output_dir(output, frozen_crlf)
    assert result["status"] == "r5_xgame_output_validated"
    assert result["manifest_raw_sha256_match"] is False
    assert result["manifest_normalized_sha256_match"] is True


def test_validator_reports_legacy_stage_package_tarball_sha(tmp_path: Path):
    validator = _load_validator()
    output, frozen = _valid_output(tmp_path)
    stage_package = {
        "schema_version": 1,
        "stage": "package",
        "status": "package_complete",
        "files": {
            "r5_xgame_outputs.tar.gz": {
                "path": "/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz",
                "path_type": "file",
                "sha256": "05d298c29904142d9e28db97e485db80b8b68eb56b520450594936593970fbd2",
            },
            "r5_xgame_outputs.tar.gz.sha256": {
                "path": "/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz.sha256",
                "path_type": "file",
                "sha256": "legacy-sidecar",
            },
        },
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    (output / "stage_package.json").write_text(json.dumps(stage_package), encoding="utf-8")
    result = validator.validate_output_dir(output, frozen)
    marker = result["stage_package_marker"]
    assert marker["has_legacy_tarball_record"] is True
    assert marker["stale_legacy_tarball_sha256"] is True
