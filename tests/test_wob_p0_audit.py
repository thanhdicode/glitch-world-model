import csv
import json
from pathlib import Path

import pytest

from glitch_detection.wob_p0_audit import WobP0Config, run_audit


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path, *, with_sources: bool) -> WobP0Config:
    wob_root = tmp_path / "wob_root"
    normal_tar = wob_root / "NORMAL-TRAIN" / "ep-0000" / "ep-0000.tar"
    bug_tar = wob_root / "TEST" / "BlackScreen" / "ep-0000" / "ep-0000.tar"
    if with_sources:
        normal_tar.parent.mkdir(parents=True, exist_ok=True)
        normal_tar.write_bytes(b"normal")
        bug_tar.parent.mkdir(parents=True, exist_ok=True)
        bug_tar.write_bytes(b"bug")

    split_path = tmp_path / "split.csv"
    _write_csv(
        split_path,
        [
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-normal",
                "source": "NORMAL-TRAIN/ep-0000/ep-0000.tar",
                "episode_id": "normal/ep-0000",
                "pair_id": "normal/ep-0000",
                "category": "Normal",
                "label": "Normal",
                "split": "train",
                "action_mode": "real",
                "use_for_training": "True",
                "materialize": "True",
            },
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-test",
                "source": "TEST/BlackScreen/ep-0000/ep-0000.tar",
                "episode_id": "BlackScreen/ep-0000",
                "pair_id": "BlackScreen/ep-0000",
                "category": "BlackScreen",
                "label": "Buggy",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
            },
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-test",
                "source": "TEST/BlackScreen/ep-0001/ep-0001.tar",
                "episode_id": "BlackScreen/ep-0001",
                "pair_id": "BlackScreen/ep-0001",
                "category": "BlackScreen",
                "label": "Buggy",
                "split": "test",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "False",
            },
        ],
    )
    protocol_path = tmp_path / "protocol_audit.json"
    _write_json(
        protocol_path,
        {
            "normal_inventory": {"episode_count": 1},
            "test_inventory": {"episode_count": 2},
            "normal_sample": {"action_shape": [], "required_numeric_schema_valid": True},
            "bug_sample": {"action_shape": [], "required_numeric_schema_valid": True},
            "semantic_action_synchronization_verified": False,
        },
    )
    split_audit_path = tmp_path / "split.audit.json"
    _write_json(
        split_audit_path,
        {
            "split_counts": {"train": 1, "validation": 1, "test": 1},
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )
    return WobP0Config(
        wob_root=wob_root,
        output_dir=tmp_path / "out",
        split_path=split_path,
        protocol_audit_path=protocol_path,
        split_audit_path=split_audit_path,
        dry_run=True,
        allow_materialization_check=True,
        no_locked=True,
        write_manifest_preview=True,
    )


def test_wob_p0_audit_refuses_locked_test_root(tmp_path: Path):
    config = _fixture(tmp_path, with_sources=False)
    locked_root = config.wob_root / "TEST"
    with pytest.raises(ValueError, match="locked-test path"):
        run_audit(
            WobP0Config(
                wob_root=locked_root,
                output_dir=config.output_dir,
                split_path=config.split_path,
                protocol_audit_path=config.protocol_audit_path,
                split_audit_path=config.split_audit_path,
                dry_run=True,
                allow_materialization_check=False,
                no_locked=True,
                write_manifest_preview=False,
            )
        )


def test_wob_p0_dry_run_works_on_small_fixture(tmp_path: Path):
    config = _fixture(tmp_path, with_sources=True)
    report = run_audit(config)
    assert report["status"] == "READY_FOR_WOB_P1"
    assert Path(report["json_path"]).is_file()
    assert Path(report["markdown_path"]).is_file()


def test_wob_p0_reports_missing_source_inputs_clearly(tmp_path: Path):
    config = _fixture(tmp_path, with_sources=False)
    report = run_audit(config)
    assert report["status"] == "BLOCKED_MISSING_INPUTS"
    assert report["missing_inputs"]
    assert any("NORMAL-TRAIN" in path for path in report["missing_inputs"])


def test_wob_p0_manifest_preview_is_deterministic(tmp_path: Path):
    config = _fixture(tmp_path, with_sources=True)
    first = run_audit(config)
    second = run_audit(config)
    assert first["manifest_sha256"] == second["manifest_sha256"]


def test_wob_p0_does_not_write_performance_metrics_or_execution_claims(tmp_path: Path):
    config = _fixture(tmp_path, with_sources=True)
    report = run_audit(config)
    assert report["performance_metrics_present"] is False
    assert report["execution_claim_present"] is False


def test_wob_p0_preserves_action_caveat_wording(tmp_path: Path):
    config = _fixture(tmp_path, with_sources=True)
    report = run_audit(config)
    assert report["action_caveat"] == "semantic_action_synchronization_verified=false"
