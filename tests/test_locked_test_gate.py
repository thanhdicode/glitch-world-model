import hashlib
import json
from pathlib import Path

import pytest

from scripts.evaluate_tempglitch_locked_test import (
    LOCKED_TEST_AUTHORIZATION,
    validate_locked_test_release,
)


def _release_files(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    selected = tmp_path / "selected_protocol_config.json"
    selected.write_text('{"scorer": "frame_diff", "aggregation": "mean"}\n', encoding="utf-8")
    selected_sha256 = hashlib.sha256(selected.read_bytes()).hexdigest()
    decision = tmp_path / "validation_decision.md"
    decision.write_text("Locked test has not been scored yet.\n", encoding="utf-8")
    approval = tmp_path / "locked_test_approval.json"
    approval.write_text(
        json.dumps(
            {
                "authorization": LOCKED_TEST_AUTHORIZATION,
                "selected_config_sha256": selected_sha256,
            }
        ),
        encoding="utf-8",
    )
    return selected, decision, approval, selected_sha256


def test_locked_test_gate_requires_user_approval_file(tmp_path: Path):
    selected, decision, approval, _ = _release_files(tmp_path)
    approval.unlink()

    with pytest.raises(PermissionError, match="approval file"):
        validate_locked_test_release(selected, decision, approval)


def test_locked_test_gate_rejects_changed_selected_config(tmp_path: Path):
    selected, decision, approval, _ = _release_files(tmp_path)
    selected.write_text('{"scorer": "mini_latent", "aggregation": "p95"}\n', encoding="utf-8")

    with pytest.raises(PermissionError, match="does not match"):
        validate_locked_test_release(selected, decision, approval)


def test_locked_test_gate_accepts_exact_fingerprint_bound_approval(tmp_path: Path):
    selected, decision, approval, selected_sha256 = _release_files(tmp_path)

    assert validate_locked_test_release(selected, decision, approval) == selected_sha256
