from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

from scripts import (
    run_r5_xgame_comparison,
    validate_r5_xgame_comparison,
    verify_r5_wob_upload,
)


def _write_success_tarball(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source" / "r5_wob_identical_episode"
    source.mkdir(parents=True)
    for name in verify_r5_wob_upload.REQUIRED_OUTPUT_FILES:
        (source / name).write_text("placeholder\n", encoding="utf-8")

    tarball = tmp_path / "r5_wob_identical_episode_outputs.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(source, arcname=source.name)
    sidecar = tmp_path / f"{tarball.name}.sha256"
    sidecar.write_text(
        f"{verify_r5_wob_upload._sha256_file(tarball)}  {tarball.name}\n",
        encoding="utf-8",
    )
    readiness = tmp_path / "readiness.json"
    readiness.write_text("{}\n", encoding="utf-8")
    return tarball, sidecar, readiness


def test_verify_persists_validated_output_and_receipt(tmp_path: Path, monkeypatch):
    tarball, sidecar, readiness = _write_success_tarball(tmp_path)
    monkeypatch.setattr(
        verify_r5_wob_upload,
        "_run_validator",
        lambda output_dir, readiness_json: {
            "valid": True,
            "status": "r5_wob_validated",
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )
    extract_dir = tmp_path / "ingested"

    result = verify_r5_wob_upload.verify(
        tarball,
        sidecar,
        readiness,
        extract_dir=extract_dir,
    )

    receipt_path = extract_dir / "r5_wob_identical_episode" / verify_r5_wob_upload.RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert result["overall"] == "VALID_OUTPUT_BUNDLE"
    assert receipt["status"] == "r5_wob_validated"
    assert receipt["bundle_sha256"] == verify_r5_wob_upload._sha256_file(tarball)
    assert receipt["locked_test_materialized"] is False
    assert receipt["locked_test_scored"] is False


def test_safe_extract_rejects_path_traversal(tmp_path: Path):
    tarball = tmp_path / "unsafe.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        member = tarfile.TarInfo("../outside.txt")
        payload = b"unsafe"
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

    try:
        verify_r5_wob_upload._safe_extract(tarball, tmp_path / "extract")
    except RuntimeError as exc:
        assert "Path traversal" in str(exc)
    else:
        raise AssertionError("Unsafe archive member should have been rejected.")


def test_inspect_failure_debug_classifies_stage_and_runtime_error(tmp_path: Path):
    source = tmp_path / "debug"
    (source / "failure_debug").mkdir(parents=True)
    (source / "working_logs").mkdir(parents=True)
    (source / "failure_debug" / "failure_summary.json").write_text(
        json.dumps(
            {
                "phase": "materialize_lance",
                "exit_code": 1,
                "git_sha": "abc123",
                "locked_test_materialized": False,
                "locked_test_scored": False,
            }
        ),
        encoding="utf-8",
    )
    (source / "working_logs" / "r5_wob_staged.log").write_text(
        "AttributeError: missing scorer symbol\n",
        encoding="utf-8",
    )
    tarball = tmp_path / "failure.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(source / "failure_debug", arcname="failure_debug")
        archive.add(source / "working_logs", arcname="working_logs")

    result = verify_r5_wob_upload.inspect_failure_debug(tarball)

    assert result["overall"] == "FAILURE_CLASSIFIED"
    assert result["failed_stage"] == "materialize_lance"
    assert result["failure_class"] == "training_or_scoring_runtime"
    assert result["locked_test_materialized"] is False
    assert result["locked_test_scored"] is False


def test_r6_queue_keeps_wob_items_blocked():
    queue_path = Path("configs/r6_ablation_queue.json")
    queue = json.loads(queue_path.read_text(encoding="utf-8"))

    tempglitch_cpu = [
        item
        for item in queue["items"]
        if item["dataset"] == "TempGlitch" and item["compute"] == "cpu"
    ]
    wob_items = [item for item in queue["items"] if item["dataset"] == "WorldOfBugs"]
    assert tempglitch_cpu
    assert all(item["status"] == "PREPARABLE_NOT_RUN" for item in tempglitch_cpu)
    assert wob_items
    assert all(item["status"] == "BLOCKED_R5_WOB_VALIDATION" for item in wob_items)


def test_r5_xgame_refuses_metrics_without_validation_receipt(tmp_path: Path):
    tempglitch_metrics = tmp_path / "tempglitch" / "r5_metrics.json"
    wob_metrics = tmp_path / "wob" / "r5_wob_metrics.json"
    tempglitch_metrics.parent.mkdir(parents=True)
    wob_metrics.parent.mkdir(parents=True)
    tempglitch_metrics.write_text("{}\n", encoding="utf-8")
    wob_metrics.write_text("{}\n", encoding="utf-8")

    exit_code = run_r5_xgame_comparison.main(
        [
            "--tempglitch-metrics",
            str(tempglitch_metrics),
            "--wob-metrics",
            str(wob_metrics),
            "--output-dir",
            str(tmp_path / "xgame"),
        ]
    )

    assert exit_code == 1
    assert not (tmp_path / "xgame").exists()


def test_r5_xgame_validator_requires_receipt_hash(tmp_path: Path):
    output_dir = tmp_path / "xgame"
    output_dir.mkdir()
    (output_dir / "r5_xgame_comparison.csv").write_text(
        "dataset,method,seed,scorer,aggregation,auroc,auprc\n"
        "TempGlitch,lewm,42,l2,mean,0.1,0.1\n"
        "WorldOfBugs,lewm,42,l2,mean,0.1,0.1\n",
        encoding="utf-8",
    )
    provenance_path = output_dir / "r5_xgame_provenance.json"
    provenance_path.write_text(
        json.dumps(
            {
                "wob_status": "VALIDATED",
                "locked_test_materialized": False,
                "locked_test_scored": False,
            }
        ),
        encoding="utf-8",
    )

    result = validate_r5_xgame_comparison.validate_r5_xgame(output_dir)

    assert result["valid"] is False
    assert "WOB validation receipt hash is missing" in result["errors"]
