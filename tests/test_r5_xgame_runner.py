from __future__ import annotations

import importlib.util
from pathlib import Path


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
