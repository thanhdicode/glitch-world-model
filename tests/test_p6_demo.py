"""Tests for the P6 qualitative demo lane."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEMO_PATH = REPO_ROOT / "demo" / "run_glitch_demo.py"


def _load_demo_module() -> ModuleType:
    try:
        import demo.run_glitch_demo as module  # noqa: PLC0415

        return module
    except ImportError:
        spec = importlib.util.spec_from_file_location("run_glitch_demo", DEMO_PATH)
        assert spec is not None and spec.loader is not None, f"Could not load {DEMO_PATH}"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def test_receipt_temporal_metrics_claimed_is_false() -> None:
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["temporal_metrics_claimed"] is False


def test_receipt_locked_test_used_is_false() -> None:
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["locked_test_used"] is False


def test_receipt_kaggle_required_is_false() -> None:
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["kaggle_required"] is False


def test_receipt_ground_truth_spans_available_is_false() -> None:
    module = _load_demo_module()
    assert module._RECEIPT_STATIC["ground_truth_spans_available"] is False


def test_receipt_claim_boundary_mentions_qualitative() -> None:
    module = _load_demo_module()
    boundary = str(module._RECEIPT_STATIC.get("claim_boundary", ""))
    assert "qualitative" in boundary.lower()


def test_receipt_claim_boundary_mentions_no_temporal_localization() -> None:
    module = _load_demo_module()
    boundary = str(module._RECEIPT_STATIC.get("claim_boundary", ""))
    assert "no temporal-localization metric" in boundary.lower()


def test_receipt_claim_boundary_mentions_no_locked_test() -> None:
    module = _load_demo_module()
    boundary = str(module._RECEIPT_STATIC.get("claim_boundary", ""))
    assert "no locked test" in boundary.lower()


def test_receipt_demo_phase_is_p6() -> None:
    module = _load_demo_module()
    assert module._RECEIPT_STATIC.get("demo_phase") == "P6"


def test_dry_run_exits_zero(tmp_path: Path) -> None:
    module = _load_demo_module()
    rc = module.main(["--dry-run", "--output-dir", str(tmp_path / "out")])
    assert rc == 0


def test_dry_run_writes_receipt(tmp_path: Path) -> None:
    module = _load_demo_module()
    output_dir = tmp_path / "out"
    rc = module.main(["--dry-run", "--output-dir", str(output_dir)])
    assert rc == 0
    assert (output_dir / "demo_receipt.json").is_file()


def test_dry_run_receipt_valid_json(tmp_path: Path) -> None:
    module = _load_demo_module()
    output_dir = tmp_path / "out"
    rc = module.main(["--dry-run", "--output-dir", str(output_dir)])
    assert rc == 0
    receipt = json.loads((output_dir / "demo_receipt.json").read_text(encoding="utf-8"))
    assert isinstance(receipt, dict)


def test_dry_run_receipt_flags(tmp_path: Path) -> None:
    module = _load_demo_module()
    output_dir = tmp_path / "out"
    rc = module.main(["--dry-run", "--output-dir", str(output_dir)])
    assert rc == 0
    receipt = json.loads((output_dir / "demo_receipt.json").read_text(encoding="utf-8"))
    assert receipt["temporal_metrics_claimed"] is False
    assert receipt["locked_test_used"] is False
    assert receipt["kaggle_required"] is False
    assert receipt["ground_truth_spans_available"] is False
    assert receipt["mode"] == "dry_run"


def test_dry_run_no_pngs(tmp_path: Path) -> None:
    module = _load_demo_module()
    output_dir = tmp_path / "out"
    rc = module.main(["--dry-run", "--output-dir", str(output_dir)])
    assert rc == 0
    assert list(output_dir.glob("*.png")) == []


def test_no_temporal_metric_names_in_source() -> None:
    source = DEMO_PATH.read_text(encoding="utf-8")
    forbidden = [
        "onset_f1",
        "offset_f1",
        "temporal_iou",
        "localization_f1",
        "span_recall",
        "span_precision",
    ]
    for name in forbidden:
        assert name not in source, f"Demo source must not contain {name!r}"


def test_no_locked_test_path_fragments_in_source() -> None:
    source = DEMO_PATH.read_text(encoding="utf-8")
    forbidden = ["test_split", "test_manifest", "locked/", "locked_test_manifest"]
    for fragment in forbidden:
        assert fragment not in source, f"Demo source must not contain {fragment!r}"
