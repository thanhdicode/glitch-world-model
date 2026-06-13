import json
import os
import sys
from pathlib import Path

import pytest

from glitch_detection.lewm_gpu_profile_kaggle import (
    LeWMGPUProfileKaggleConfig,
    render_profile_kernel,
)
from scripts.run_kaggle_parity_check import (
    kernel_entrypoint_is_guarded,
    run_kaggle_parity_check,
    run_utf8_subprocess,
)


def _lance_root(tmp_path: Path) -> Path:
    root = tmp_path / "datasets"
    for name in (
        "tempglitch_train_normal_all_local.lance",
        "tempglitch_validation_normal_all_local.lance",
    ):
        path = root / name
        path.mkdir(parents=True)
        (path / "fixture.bin").write_bytes(b"fixture")
    return root


def test_rendered_live_kernel_entrypoint_is_guarded():
    kernel = render_profile_kernel(
        LeWMGPUProfileKaggleConfig(
            dataset_slug="huynhdieuthanh/lewm-parity-private",
            kernel_slug="huynhdieuthanh/lewm-parity-kernel",
            batch_size=8,
            git_sha="abc",
            branch="main",
        ),
        {"optimizer_updates": 500, "validation_batches": 8},
    )
    assert kernel_entrypoint_is_guarded(kernel)


def test_parity_gate_runs_rendered_kernel_spawn_probe_and_writes_safe_receipt(tmp_path: Path):
    output = tmp_path / "parity_receipt.json"
    receipt = run_kaggle_parity_check(tmp_path, _lance_root(tmp_path), output, git_sha="abc")
    assert receipt["pass"] is True
    assert receipt["spawn_verified"] is True
    assert receipt["training_performed"] is False
    assert receipt["validation_buggy_used"] is False
    assert receipt["locked_test_scored"] is False
    assert json.loads(output.read_text(encoding="utf-8")) == receipt


def test_parity_gate_fails_closed_without_real_lance_inputs(tmp_path: Path):
    with pytest.raises(
        FileNotFoundError, match="parity requires local research MVP Lance datasets"
    ):
        run_kaggle_parity_check(
            tmp_path, tmp_path / "missing", tmp_path / "receipt.json", git_sha="x"
        )


def test_parity_subprocess_decode_replaces_non_utf8_byte(tmp_path: Path):
    result = run_utf8_subprocess(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([0x8f]))"],
        cwd=tmp_path,
        environment=dict(os.environ),
    )
    assert result.returncode == 0
    assert result.stdout == "\ufffd"
