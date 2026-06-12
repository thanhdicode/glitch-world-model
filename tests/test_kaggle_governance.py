from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_kaggle_governance_uses_standing_authorization_and_keeps_locked_test_separate():
    rules = (ROOT / "RULES.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    playbook = (ROOT / "PLAYBOOK.md").read_text(encoding="utf-8")
    workflow = (ROOT / "docs/workflows/kaggle_automation_policy.md").read_text(
        encoding="utf-8"
    )
    combined = "\n".join([rules, agents, playbook, workflow]).lower()

    assert "standing authorization" in combined
    assert "dataset upload and kernel push require separate" not in combined
    assert "fingerprint-bound approval" not in combined
    assert "locked test" in combined
    assert "separate direct user command" in combined
    assert "public" in workflow
    assert "delete" in workflow
    assert "not authorized" in workflow


def test_context_generator_emits_standing_authorization_policy():
    generator = (ROOT / "scripts/update_context_cache.py").read_text(encoding="utf-8")

    assert "standing Kaggle authorization" in generator
    assert "fingerprint-bound approval" not in generator
    assert "kaggle_automation_policy.md" in generator
