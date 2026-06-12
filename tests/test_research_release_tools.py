import importlib.util
import shutil
import subprocess
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


def test_release_validator_accepts_required_files_and_safe_tracked_paths(tmp_path: Path):
    validator = load_script("validate_research_release")
    context = load_script("update_context_cache")
    for relative in validator.REQUIRED_PATHS:
        path = tmp_path / relative
        if Path(relative).suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            content = (
                "\n".join(f"## {index}. Section {index}" for index in range(31)) + "\n"
                if relative == "PLAYBOOK.md"
                else "present\n"
            )
            path.write_text(content, encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(tmp_path / "docs/context")
    context.update_context_cache(tmp_path, refresh_boot=True)

    errors = validator.validate_release(
        tmp_path,
        tracked_files=["README.md", "src/glitch_detection/example.py"],
    )

    assert errors == []


def test_release_validator_requires_agent_governance_files(tmp_path: Path):
    validator = load_script("validate_research_release")

    expected = {
        "AGENTS.md",
        "PLAYBOOK.md",
        "RULES.md",
        "CLAUDE.md",
        "CONVENTIONS.md",
        ".aider.conf.yml",
        ".github/copilot-instructions.md",
        ".codex/skills",
        "docs/workflows/agent_task_template.md",
        "docs/workflows/kaggle_automation_policy.md",
        "docs/workflows/locked_test_release.md",
        "docs/workflows/artifact_policy.md",
        "docs/workflows/experiment_tracking.md",
        "docs/workflows/paper_claim_rules.md",
        "docs/workflows/runtime_management.md",
        "docs/workflows/security_checks.md",
        "docs/context/BOOT.md",
        "docs/context/PROJECT_STATE.md",
        "docs/context/NEXT_ACTION.md",
        "docs/context/LAST_HANDOFF.md",
        "docs/context/REPO_MAP.md",
        "docs/context/TASK_ROUTER.md",
        "docs/context/CONTEXT_POLICY.md",
        "docs/context/README.md",
    }

    assert expected <= set(validator.REQUIRED_PATHS)


def test_release_validator_requires_complete_playbook_structure(tmp_path: Path):
    validator = load_script("validate_research_release")
    playbook = tmp_path / "PLAYBOOK.md"
    playbook.write_text(
        "\n".join(f"## {index}. Section {index}" for index in range(31)) + "\n",
        encoding="utf-8",
    )

    errors = validator.validate_playbook_structure(playbook)

    assert errors == []


def test_release_validator_rejects_missing_playbook_section(tmp_path: Path):
    validator = load_script("validate_research_release")
    playbook = tmp_path / "PLAYBOOK.md"
    playbook.write_text(
        "\n".join(f"## {index}. Section {index}" for index in range(30)) + "\n",
        encoding="utf-8",
    )

    errors = validator.validate_playbook_structure(playbook)

    assert errors == ["PLAYBOOK.md missing required section: 30"]


@pytest.mark.parametrize(
    "tracked_path",
    [
        "checkpoints/model.pt",
        "models/model.pth",
        "runs/model.ckpt",
        "kaggle.json",
        ".env",
        "secrets/access_token.txt",
        "outputs/report.json",
        "data/raw/video.mp4",
        "data/processed/manifest.csv",
        "private_key.pem",
    ],
)
def test_release_validator_rejects_prohibited_tracked_paths(tmp_path: Path, tracked_path: str):
    validator = load_script("validate_research_release")

    errors = validator.validate_tracked_files([tracked_path])

    assert errors
    assert tracked_path in errors[0]


def test_release_validator_strict_check_detects_dirty_worktree(tmp_path: Path):
    validator = load_script("validate_research_release")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    errors = validator.working_tree_errors(tmp_path)

    assert errors == ["git working tree is not clean"]


def test_claim_registry_parser_reports_claim_ids_and_valid_statuses(tmp_path: Path):
    checker = load_script("check_claim_registry")
    registry = tmp_path / "claims.md"
    registry.write_text(
        "| ID | Claim | Type | Evidence | Status | Section | Notes |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        "| C-001 | A supported claim. | method | artifact.md | verified | Method | note |\n"
        "| C-002 | Planned experiment. | experiment | none | future-work | Future | note |\n",
        encoding="utf-8",
    )

    claims = checker.parse_claim_registry(registry)
    errors, warnings = checker.validate_claims(claims)

    assert [claim.claim_id for claim in claims] == ["C-001", "C-002"]
    assert errors == []
    assert warnings == []


def test_claim_registry_rejects_duplicate_ids_and_invalid_status(tmp_path: Path):
    checker = load_script("check_claim_registry")
    registry = tmp_path / "claims.md"
    registry.write_text(
        "| C-001 | First. | method | evidence.md | verified | Method | note |\n"
        "| C-001 | Second. | method | evidence.md | unsupported | Method | note |\n",
        encoding="utf-8",
    )

    errors, _warnings = checker.validate_claims(checker.parse_claim_registry(registry))

    assert any("duplicate claim ID: C-001" in error for error in errors)
    assert any("invalid status 'unsupported'" in error for error in errors)


def test_claim_registry_warns_when_verified_claim_has_no_evidence(tmp_path: Path):
    checker = load_script("check_claim_registry")
    registry = tmp_path / "claims.md"
    registry.write_text(
        "| C-001 | Claim. | experiment | none | verified | Results | note |\n",
        encoding="utf-8",
    )

    errors, warnings = checker.validate_claims(checker.parse_claim_registry(registry))

    assert errors == []
    assert warnings == ["C-001: verified claim has no evidence source"]


def test_paper_table_generator_writes_documented_phase6_tables(tmp_path: Path):
    generator = load_script("make_paper_tables")

    written = generator.write_tables(tmp_path)

    assert {path.name for path in written} == {
        "phase6d_results.tex",
        "phase6e_validation_metrics.tex",
        "phase6e_validation_metrics.md",
    }
    assert "0.573170" in (tmp_path / "phase6d_results.tex").read_text(encoding="utf-8")
    phase6e = (tmp_path / "phase6e_validation_metrics.md").read_text(encoding="utf-8")
    assert "0.403865" in phase6e
    assert "Validation only" in phase6e
