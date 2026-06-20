from __future__ import annotations

import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest


def _load_script(repo_root: Path, stem: str):
    path = repo_root / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r5_xgame_requires_wob_metrics_before_writing(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_script(repo_root, "run_r5_xgame_comparison")
    tempglitch_metrics = tmp_path / "r5_metrics.json"
    tempglitch_metrics.write_text(json.dumps({"results": []}), encoding="utf-8")

    assert module.main(["--tempglitch-metrics", str(tempglitch_metrics)]) == 1


def test_r6_runners_reject_non_dry_execution() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    tempglitch = _load_script(repo_root, "run_r6_tempglitch_ablations")
    wob = _load_script(repo_root, "run_r6_wob_ablations")

    assert tempglitch.main(["--ablation", "aggregation"]) == 1
    assert wob.main(["--ablation", "aggregation"]) == 1


def test_r5_wob_upload_intake_classifies_debug_only_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_script(repo_root, "verify_r5_wob_upload")
    debug_bundle = tmp_path / "failure_debug.tar.gz"
    debug_bundle.write_bytes(b"diagnostic bundle")

    result = module.verify(
        tmp_path / "missing_output.tar.gz",
        tmp_path / "missing_output.tar.gz.sha256",
        repo_root / "configs" / "wob_protocol" / "wob_expansion_readiness.json",
        debug_bundle,
    )

    assert result["overall"] == "FAILURE_DEBUG_BUNDLE"
    assert result["failure_debug_exists"] is True


def test_r5_wob_upload_intake_rejects_tar_path_traversal(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_script(repo_root, "verify_r5_wob_upload")
    tarball = tmp_path / "malicious.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        info = tarfile.TarInfo("../outside.txt")
        payload = b"not allowed"
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    with pytest.raises(RuntimeError, match="Path traversal"):
        module._safe_extract(tarball, tmp_path / "extract")
