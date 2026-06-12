from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.update_context_cache import (
    CONTEXT_DIR,
    context_validation_errors,
    python_symbols,
    update_context_cache,
)


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def _write_minimal_repo(root: Path) -> None:
    for directory in ("src/glitch_detection", "scripts", "tests", "docs/research"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "PLAYBOOK.md").write_text("# PLAYBOOK\n", encoding="utf-8")
    (root / "RULES.md").write_text("# RULES\n", encoding="utf-8")
    (root / "docs/research/16_claim_registry.md").write_text("# Claims\n", encoding="utf-8")
    (root / "src/glitch_detection/example.py").write_text(
        '"""Example module."""\nclass Example:\n    pass\n\ndef run():\n    return 1\n',
        encoding="utf-8",
    )
    (root / "scripts/example_cli.py").write_text(
        '"""Example CLI."""\ndef main():\n    return 0\n',
        encoding="utf-8",
    )
    (root / "tests/test_example.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    (root / "outputs/ignored.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "outputs/ignored.py").write_text("def hidden():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)


def test_update_context_cache_creates_required_files(tmp_path: Path):
    _init_repo(tmp_path)
    _write_minimal_repo(tmp_path)

    changed = update_context_cache(tmp_path, refresh_boot=True)

    assert changed
    for name in (
        "BOOT.md",
        "PROJECT_STATE.md",
        "NEXT_ACTION.md",
        "LAST_HANDOFF.md",
        "REPO_MAP.md",
        "TASK_ROUTER.md",
        "CONTEXT_POLICY.md",
        "README.md",
    ):
        assert (tmp_path / CONTEXT_DIR / name).is_file()
    assert context_validation_errors(tmp_path) == []


def test_validate_context_cache_catches_missing_file(tmp_path: Path):
    _init_repo(tmp_path)
    _write_minimal_repo(tmp_path)
    update_context_cache(tmp_path, refresh_boot=True)
    (tmp_path / CONTEXT_DIR / "BOOT.md").unlink()

    assert "missing context file: docs/context/BOOT.md" in context_validation_errors(tmp_path)


def test_boot_line_limit_and_gate5_router(tmp_path: Path):
    _init_repo(tmp_path)
    _write_minimal_repo(tmp_path)
    update_context_cache(tmp_path, refresh_boot=True)

    boot_lines = (tmp_path / CONTEXT_DIR / "BOOT.md").read_text(encoding="utf-8").splitlines()
    router = (tmp_path / CONTEXT_DIR / "TASK_ROUTER.md").read_text(encoding="utf-8")

    assert len(boot_lines) <= 200
    assert "Gate 5 Kaggle" in router


def test_generated_context_records_gate7_to_gate9_pilot_without_opening_gate10(
    tmp_path: Path,
):
    _init_repo(tmp_path)
    _write_minimal_repo(tmp_path)
    update_context_cache(tmp_path, refresh_boot=True)

    boot = (tmp_path / CONTEXT_DIR / "BOOT.md").read_text(encoding="utf-8")
    state = (tmp_path / CONTEXT_DIR / "PROJECT_STATE.md").read_text(encoding="utf-8")

    assert "Gates 7-9 completed" in boot
    assert "| 7 | passed" in state
    assert "| 8 | passed" in state
    assert "| 9 | passed pilot" in state
    assert "| 10 | closed" in state
    assert "Locked test is closed" in boot


def test_repo_map_includes_key_modules_and_ignores_outputs(tmp_path: Path):
    _init_repo(tmp_path)
    _write_minimal_repo(tmp_path)
    update_context_cache(tmp_path, refresh_boot=True)

    repo_map = (tmp_path / CONTEXT_DIR / "REPO_MAP.md").read_text(encoding="utf-8")

    assert "src/glitch_detection/example.py" in repo_map
    assert "Example, run" in repo_map
    assert "outputs/ignored.py" not in repo_map


def test_existing_handoff_is_not_overwritten(tmp_path: Path):
    _init_repo(tmp_path)
    _write_minimal_repo(tmp_path)
    handoff = tmp_path / CONTEXT_DIR / "LAST_HANDOFF.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text(
        "# LAST_HANDOFF.md\n\n"
        "Last completed task: custom\n"
        "Commit: `manual`\n"
        "Date: manual\n\n"
        "## What Changed\nmanual\n\n"
        "## Checks Passed\nmanual\n\n"
        "## Safety Status\nmanual\n\n"
        "## Gate Status After Task\nmanual\n\n"
        "## Open Blockers\nmanual\n\n"
        "## Next Recommended Task\nmanual\n\n"
        "## Files Likely Relevant Next\nmanual\n",
        encoding="utf-8",
    )

    update_context_cache(tmp_path, refresh_boot=True)

    assert "Last completed task: custom" in handoff.read_text(encoding="utf-8")


def test_python_symbols_reads_top_level_symbols(tmp_path: Path):
    path = tmp_path / "module.py"
    path.write_text("class Alpha:\n    pass\n\ndef beta():\n    pass\n", encoding="utf-8")

    assert python_symbols(path) == ["Alpha", "beta"]
