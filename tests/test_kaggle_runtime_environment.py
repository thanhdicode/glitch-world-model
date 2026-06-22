import json
from pathlib import Path

import tomllib


def test_kaggle_runtime_pins_are_optional_and_parseable():
    repo = Path(__file__).resolve().parents[1]
    lines = [
        line.strip()
        for line in (repo / "requirements" / "kaggle_runtime.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    pins = dict(line.split("==", 1) for line in lines)

    assert pins["stable-worldmodel"] == "0.1.1"
    assert pins["stable-pretraining"] == "0.1.7"
    assert pins["transformers"] == "4.57.6"
    assert pins["lancedb"] == "0.30.0"
    assert pins["pylance"] == "4.0.0"

    project = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    assert all(
        "torch" not in dependency.lower() for dependency in project["project"]["dependencies"]
    )


def test_devcontainer_uses_linux_python_without_gpu_default_install():
    repo = Path(__file__).resolve().parents[1]
    payload = json.loads((repo / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))
    assert "bookworm" in payload["image"]
    assert payload["postCreateCommand"] == "python -m pip install -e .[dev]"
    assert payload["remoteEnv"]["PYTHONUTF8"] == "1"
