import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r2_research_mvp_config_is_frozen_for_main_run():
    validator = load_script("validate_lewm_research_mvp_config")

    result = validator.validate_research_mvp_config(ROOT / "configs/lewm_research_mvp.yaml")

    assert result["status"] == "lewm_research_mvp_config_validated"
    assert result["target_optimizer_updates"] == 15000
    assert result["seeds"] == [42, 43, 44]
    assert result["locked_test_enabled"] is False


def test_r2_config_validator_rejects_wrong_seed_order(tmp_path: Path):
    validator = load_script("validate_lewm_research_mvp_config")
    config = (ROOT / "configs/lewm_research_mvp.yaml").read_text(encoding="utf-8")
    bad = config.replace("    - 42\n    - 43\n    - 44", "    - 43\n    - 42\n    - 44", 1)
    path = tmp_path / "bad.yaml"
    path.write_text(bad, encoding="utf-8")

    with pytest.raises(ValueError, match="seeds must be"):
        validator.validate_research_mvp_config(path)


def test_optional_frozen_video_baseline_writes_non_blocking_skip_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from glitch_detection import frozen_video_representation as baseline

    monkeypatch.setattr(
        baseline,
        "dependency_status",
        lambda: {"torch": True, "transformers": False},
    )

    result = baseline.plan_frozen_video_representation_baseline(tmp_path)

    assert result["status"] == "skipped"
    assert result["blocks_lewm_critical_path"] is False
    written = json.loads(
        (tmp_path / "frozen_video_representation_skip.json").read_text(encoding="utf-8")
    )
    assert written["reason"] == "missing_optional_dependency"
