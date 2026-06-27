from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_demo_module():
    try:
        import demo.run_glitch_demo as module  # noqa: PLC0415

        return module
    except ImportError:
        pass
    demo_path = REPO_ROOT / "demo" / "run_glitch_demo.py"
    spec = importlib.util.spec_from_file_location("run_glitch_demo", demo_path)
    assert spec and spec.loader, f"Could not load {demo_path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_receipt_temporal_metrics_claimed_is_false():
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["temporal_metrics_claimed"] is False


def test_receipt_locked_test_used_is_false():
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["locked_test_used"] is False


def test_receipt_kaggle_required_is_false():
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["kaggle_required"] is False


def test_receipt_ground_truth_spans_available_is_false():
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["ground_truth_spans_available"] is False


def test_receipt_claim_boundary_mentions_qualitative_temporal_and_locked():
    module = _load_demo_module()
    boundary = str(module._RECEIPT_STATIC["claim_boundary"]).lower()
    assert "qualitative" in boundary
    assert "temporal" in boundary
    assert "locked" in boundary


def test_receipt_demo_phase_is_p6():
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["demo_phase"] == "P6"


def test_dry_run_exits_zero(tmp_path: Path):
    module = _load_demo_module()
    rc = module.main(["--dry-run", "--output-dir", str(tmp_path / "out")])
    assert rc == 0


def test_dry_run_writes_receipt(tmp_path: Path):
    module = _load_demo_module()
    out_dir = tmp_path / "out"
    module.main(["--dry-run", "--output-dir", str(out_dir)])
    assert (out_dir / "demo_receipt.json").is_file()


def test_dry_run_receipt_is_valid_json(tmp_path: Path):
    module = _load_demo_module()
    out_dir = tmp_path / "out"
    module.main(["--dry-run", "--output-dir", str(out_dir)])
    receipt = json.loads((out_dir / "demo_receipt.json").read_text(encoding="utf-8"))
    assert isinstance(receipt, dict)


def test_dry_run_receipt_has_expected_flags(tmp_path: Path):
    module = _load_demo_module()
    out_dir = tmp_path / "out"
    module.main(["--dry-run", "--output-dir", str(out_dir)])
    receipt = json.loads((out_dir / "demo_receipt.json").read_text(encoding="utf-8"))
    assert receipt["temporal_metrics_claimed"] is False
    assert receipt["locked_test_used"] is False
    assert receipt["kaggle_required"] is False
    assert receipt["ground_truth_spans_available"] is False
    assert receipt["mode"] == "dry_run"


def test_dry_run_produces_no_pngs(tmp_path: Path):
    module = _load_demo_module()
    out_dir = tmp_path / "out"
    module.main(["--dry-run", "--output-dir", str(out_dir)])
    assert list(out_dir.glob("*.png")) == []


_DEMO_SOURCE = (REPO_ROOT / "demo" / "run_glitch_demo.py").read_text(encoding="utf-8")


def test_demo_source_avoids_temporal_metric_names():
    forbidden = [
        "onset_f1",
        "offset_f1",
        "temporal_iou",
        "localization_f1",
        "span_recall",
        "span_precision",
    ]
    for item in forbidden:
        assert item not in _DEMO_SOURCE


def test_demo_source_avoids_locked_test_path_fragments():
    forbidden = ["test_split", "test_manifest", "locked/", "locked_test_manifest"]
    for item in forbidden:
        assert item not in _DEMO_SOURCE
