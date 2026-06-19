from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.prepare_wob_expansion_readiness import (
    DEFAULT_SPLIT_CSV,
    ROOT,
    build_eval_manifest_rows,
    prepare,
)
from scripts.validate_wob_expansion_readiness import validate_readiness


def _read_split_rows() -> list[dict[str, str]]:
    import csv

    with (ROOT / DEFAULT_SPLIT_CSV).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _seed_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Copy the real protocol split into an isolated tmp repo root and freeze the gate there."""

    split = tmp_path / "configs/wob_protocol/split.csv"
    split.parent.mkdir(parents=True, exist_ok=True)
    split.write_bytes((ROOT / DEFAULT_SPLIT_CSV).read_bytes())
    eval_manifest = tmp_path / "configs/wob_protocol/wob_expansion_eval_manifest.csv"
    readiness_json = tmp_path / "configs/wob_protocol/wob_expansion_readiness.json"
    prepare(
        repo_root=tmp_path,
        split_csv=split,
        eval_manifest=eval_manifest,
        readiness_json=readiness_json,
        dry_run=False,
    )
    return eval_manifest, readiness_json


def _rehash_manifest(eval_manifest: Path, readiness_json: Path) -> None:
    """Recompute and store the manifest hash so a tampered manifest passes the hash gate."""

    payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    payload["eval_manifest_sha256"] = hashlib.sha256(eval_manifest.read_bytes()).hexdigest()
    readiness_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_prepare_selects_72_validation_rows_excludes_locked_and_train():
    rows = build_eval_manifest_rows(_read_split_rows())
    assert len(rows) == 72
    assert sum(r["evaluation_role"] == "calibration_normal" for r in rows) == 12
    assert sum(r["evaluation_role"] == "evaluation_buggy" for r in rows) == 60
    # No locked (split=test) or train rows leak into the evaluation manifest.
    assert all(r["split"] == "validation" for r in rows)
    assert all(r["label"] == "Normal" for r in rows if r["evaluation_role"] == "calibration_normal")
    assert all(r["label"] == "Buggy" for r in rows if r["evaluation_role"] == "evaluation_buggy")


def test_prepare_flags_false_and_validate_round_trip(tmp_path: Path):
    eval_manifest, readiness_json = _seed_repo(tmp_path)
    payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    assert payload["validation_buggy_used_for_fit_select"] is False
    assert payload["locked_test_materialized"] is False
    assert payload["locked_test_scored"] is False
    assert payload["evaluation_run"] is False
    assert payload["action_synchronization_verified"] is False

    result = validate_readiness(readiness_json, repo_root=tmp_path)
    assert result["status"] == "wob_expansion_readiness_passed"
    assert result["calibration_normal_count"] == 12
    assert result["evaluation_buggy_count"] == 60
    assert result["locked_rows_excluded"] == 59


def test_claim_boundary_and_forbidden_claims_frozen(tmp_path: Path):
    _eval_manifest, readiness_json = _seed_repo(tmp_path)
    payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    assert payload["claim_boundary"].strip()
    assert isinstance(payload["forbidden_claims"], list)
    assert len(payload["forbidden_claims"]) >= 1
    # Recorded hashes pin the upstream verified artifacts.
    assert payload["recorded_artifact_hashes"]["wob_p1_seed42_artifact_sha256"].startswith("54bb2b")


def test_validate_fails_when_locked_row_injected(tmp_path: Path):
    eval_manifest, readiness_json = _seed_repo(tmp_path)
    with eval_manifest.open("a", encoding="utf-8", newline="") as handle:
        handle.write(
            "benedictwilkinsai/world-of-bugs-test,TEST/BlackScreen/ep-0099/ep-0099.tar,"
            "BlackScreen/ep-0099,BlackScreen/ep-0099,BlackScreen,Buggy,test,real,False,True,"
            "evaluation_buggy\n"
        )
    _rehash_manifest(
        eval_manifest, readiness_json
    )  # pass the hash gate to isolate the locked check
    with pytest.raises(ValueError, match="locked rows"):
        validate_readiness(readiness_json, repo_root=tmp_path)


def test_validate_fails_on_manifest_hash_mismatch(tmp_path: Path):
    eval_manifest, readiness_json = _seed_repo(tmp_path)
    with eval_manifest.open("a", encoding="utf-8", newline="") as handle:
        handle.write(
            "benedictwilkinsai/world-of-bugs-normal,NORMAL-TRAIN/ep-0099/ep-0099.tar,"
            "normal/ep-0099,normal/ep-0099,Normal,Normal,validation,real,False,True,"
            "calibration_normal\n"
        )
    with pytest.raises(ValueError, match="SHA256 does not match"):
        validate_readiness(readiness_json, repo_root=tmp_path)


def test_validate_fails_when_validation_buggy_used_for_fit_select(tmp_path: Path):
    _eval_manifest, readiness_json = _seed_repo(tmp_path)
    payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    payload["validation_buggy_used_for_fit_select"] = True
    readiness_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="fit/select"):
        validate_readiness(readiness_json, repo_root=tmp_path)


def test_validate_fails_on_seed42_artifact_hash_mismatch(tmp_path: Path):
    _eval_manifest, readiness_json = _seed_repo(tmp_path)
    payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    payload["recorded_artifact_hashes"]["wob_p1_seed42_artifact_sha256"] = "deadbeef"
    readiness_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="seed42 artifact hash"):
        validate_readiness(readiness_json, repo_root=tmp_path)
