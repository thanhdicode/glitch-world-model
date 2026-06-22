from __future__ import annotations

import importlib.util
import json
import tarfile
from pathlib import Path

import pytest


def _runner():
    path = Path("scripts/run_r5_xgame_staged.py")
    spec = importlib.util.spec_from_file_location("r5_xgame_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preflight_reports_missing_archives_by_role(tmp_path: Path):
    runner = _runner()
    result = runner.preflight(
        Path("configs/wob_protocol/r5_xgame_split.csv"),
        tmp_path / "missing",
        tmp_path / "out",
        [42, 43, 44],
    )
    assert result["status"] == "preflight_missing_inputs"
    assert len(result["missing_by_role"]["train_normal"]) == 36
    assert len(result["missing_by_role"]["evaluation_normal_negative"]) == 12
    assert len(result["missing_by_role"]["calibration_normal"]) == 12
    assert len(result["missing_by_role"]["evaluation_buggy_positive"]) == 60
    assert (tmp_path / "out" / "stage_preflight.json").is_file()


def test_preflight_resolves_all_sources_from_a_matching_root(tmp_path: Path):
    runner = _runner()
    manifest = Path("configs/wob_protocol/r5_xgame_split.csv")
    for row in __import__("csv").DictReader(manifest.open(encoding="utf-8")):
        target = tmp_path / row["source"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x")
    result = runner.preflight(manifest, tmp_path, tmp_path / "out", [42, 43, 44])
    assert result["status"] == "preflight_complete"
    assert not any(result["missing_by_role"].values())


def test_preflight_rejects_old_r5_wob_artifact_roots(tmp_path: Path):
    runner = _runner()
    input_root = tmp_path / "input"
    (input_root / "r5_wob_seed42_artifacts").mkdir(parents=True)
    with pytest.raises(ValueError, match="R5-WOB"):
        runner.preflight(
            Path("configs/wob_protocol/r5_xgame_split.csv"),
            input_root,
            tmp_path / "out",
            [42, 43, 44],
        )


def test_package_writes_tarball_and_sidecar(tmp_path: Path, monkeypatch):
    runner = _runner()
    manifest = Path("configs/wob_protocol/r5_xgame_split.csv")
    output = tmp_path / "out"
    output.mkdir()
    for name in runner.PLANNED_OUTPUTS:
        if name.endswith(".tar.gz") or name.endswith(".sha256"):
            continue
        (output / name).write_text("x\n", encoding="utf-8")
    (output / "r5_xgame_metrics.json").write_text(
        json.dumps(
            {
                "summary_row": {
                    "method": "frame_diff",
                    "seed": "",
                    "window_scorer": "frame_diff",
                    "episode_aggregation": "mean",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "runtime_provenance",
        lambda include_lewm: {"git_sha": "abc"} if not include_lewm else {"git_sha": "abc"},
    )
    result = runner.run_package(manifest=manifest, output_dir=output)
    assert result["status"] == "package_complete"
    assert (output / "r5_xgame_outputs.tar.gz").is_file()
    assert (output / "r5_xgame_outputs.tar.gz.sha256").is_file()
    with tarfile.open(output / "r5_xgame_outputs.tar.gz", "r:gz") as archive:
        assert "r5_xgame_manifest.csv" in archive.getnames()


def test_kaggle_launch_script_and_required_input_doc_exist():
    script = Path("cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh")
    doc = Path("docs/research/r5_xgame_required_kaggle_inputs.md")
    assert script.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "benedictwilkinsai/world-of-bugs-normal" in text
    assert "benedictwilkinsai/world-of-bugs-test" in text
    assert "NORMAL-TRAIN/" in text
    assert "TEST/" in text


def test_kaggle_launch_script_passes_audit_output_path():
    script_text = Path(
        "cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh"
    ).read_text(encoding="utf-8")
    assert "scripts/audit_r5_xgame_split.py" in script_text
    assert "--output" in script_text
    assert "r5_xgame_leakage_audit.json" in script_text
    assert 'mkdir -p "$OUTPUT_DIR"' in script_text
