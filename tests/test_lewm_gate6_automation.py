import json
from pathlib import Path

import pytest

from glitch_detection.kaggle_automation import (
    AutomationBlockedError,
    AutomationCommandError,
    AutomationState,
    CommandResult,
)
from glitch_detection.lewm_gate6_automation import (
    Gate6AutomationConfig,
    Gate6AutomationHandlers,
)


class FakeRunner:
    def __init__(self, responses: list[CommandResult]):
        self.responses = list(responses)
        self.commands: list[list[str]] = []

    def run(self, _step: str, command: list[str], _log_path: Path) -> CommandResult:
        self.commands.append(command)
        return self.responses.pop(0)


def _config(tmp_path: Path) -> Gate6AutomationConfig:
    return Gate6AutomationConfig(
        repo_root=Path(__file__).resolve().parents[1],
        source_root=tmp_path / "datasets",
        run_root=tmp_path / "run",
        dataset_slug="huynhdieuthanh/lewm-tempglitch-gate6-public-v7",
        kernel_slug="huynhdieuthanh/lewm-gate6-pilot-v7",
        dataset_visibility="public",
        kernel_visibility="public",
        live=True,
    )


def test_public_dataset_create_uses_public_flag(tmp_path: Path):
    runner = FakeRunner(
        [
            CommandResult(returncode=0, stdout="not found", stderr="", attempts=1),
            CommandResult(returncode=0, stdout="created", stderr="", attempts=1),
        ]
    )
    handlers = Gate6AutomationHandlers(_config(tmp_path), command_runner=runner)
    state = AutomationState(dataset_fingerprint="dataset-fp")

    updates = handlers.dataset_create_or_version(state)

    create = runner.commands[-1]
    assert "datasets" in create
    assert "create" in create
    assert "--public" in create
    assert updates["dataset_uploaded_fingerprint"] == "dataset-fp"


def test_kernel_push_uses_python_module_invocation_and_public_metadata(tmp_path: Path):
    runner = FakeRunner([CommandResult(returncode=0, stdout="pushed", stderr="", attempts=1)])
    config = _config(tmp_path)
    kernel_root = config.run_root / "package" / "kernel"
    kernel_root.mkdir(parents=True)
    (kernel_root / "kernel-metadata.json").write_text(
        json.dumps({"is_private": False}),
        encoding="utf-8",
    )
    handlers = Gate6AutomationHandlers(config, command_runner=runner)

    updates = handlers.kernel_push_once(AutomationState(kernel_fingerprint="kernel-fp"))

    assert runner.commands[0][:3] == [
        str(config.python_executable),
        "-c",
        "from kaggle.cli import main; main()",
    ]
    assert updates["kernel_status"] == "running"


def test_error_status_downloads_logs_and_blocks_without_resubmit(tmp_path: Path):
    runner = FakeRunner(
        [
            CommandResult(
                returncode=0,
                stdout='status "KernelWorkerStatus.ERROR"',
                stderr="",
                attempts=1,
            ),
            CommandResult(returncode=0, stdout="downloaded", stderr="", attempts=1),
        ]
    )
    handlers = Gate6AutomationHandlers(_config(tmp_path), command_runner=runner)

    with pytest.raises(AutomationBlockedError, match="runtime failed"):
        handlers.kernel_poll(AutomationState(kernel_fingerprint="kernel-fp"))

    assert sum("push" in command for command in runner.commands) == 0
    assert any("output" in command for command in runner.commands)


def test_ambiguous_push_error_checks_remote_before_failing(tmp_path: Path):
    class AmbiguousRunner(FakeRunner):
        def run(self, step: str, command: list[str], log_path: Path) -> CommandResult:
            self.commands.append(command)
            if step == "kernel_push_once":
                raise AutomationCommandError("Expecting value: line 1 column 1 (char 0)")
            return CommandResult(
                returncode=0,
                stdout='status "KernelWorkerStatus.RUNNING"',
                stderr="",
                attempts=1,
            )

    runner = AmbiguousRunner([])
    handlers = Gate6AutomationHandlers(_config(tmp_path), command_runner=runner)

    updates = handlers.kernel_push_once(AutomationState(kernel_fingerprint="kernel-fp"))

    assert updates["kernel_status"] == "running"
    assert any("status" in command for command in runner.commands)
