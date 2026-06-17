from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "cloud" / "r3_seed42" / "run_seed_full.sh"
WRAPPER = ROOT / "cloud" / "r3_seed42" / "run_seed42_full.sh"


def _script_words(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split()


def test_run_seed_full_defaults_to_seed_42():
    text = RUNNER.read_text(encoding="utf-8")

    assert 'LEWM_SEED="${LEWM_SEED:-42}"' in text


def test_run_seed_full_passes_seed_and_parameterized_log_path():
    text = RUNNER.read_text(encoding="utf-8")

    assert '--seed "$LEWM_SEED"' in text
    assert "r3_seed${LEWM_SEED}_run.log" in text


def test_run_seed_full_preserves_frozen_training_args():
    words = _script_words(RUNNER)
    frozen_args = {
        "--device": "cuda",
        "--run-kind": "research",
        "--batch-size": "8",
        "--num-workers": "0",
        "--early-stopping-patience": "5",
        "--target-optimizer-updates": "15000",
        "--evaluation-interval-updates": "500",
        "--checkpoint-interval-updates": "500",
    }

    for flag, value in frozen_args.items():
        index = words.index(flag)
        assert words[index + 1] == value
    assert "--pin-memory" in words
    assert "--mixed-precision" in words


def test_run_seed_full_requires_preflight_passed_json():
    text = RUNNER.read_text(encoding="utf-8")

    assert '"$LEWM_OUTPUT_ROOT/preflight_passed.json"' in text


def test_run_seed42_full_is_backward_compatible_wrapper():
    text = WRAPPER.read_text(encoding="utf-8")

    assert "export LEWM_SEED=42" in text
    assert "exec bash cloud/r3_seed42/run_seed_full.sh" in text
