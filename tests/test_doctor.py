from pathlib import Path

from scripts.doctor import collect_report, core_requirements_satisfied


def test_doctor_core_requirements_are_available():
    repo_root = Path(__file__).resolve().parents[1]
    report = collect_report(repo_root)

    assert core_requirements_satisfied(report)
    assert report["required_paths"]["README.md"]
    assert report["required_paths"]["AGENTS.md"]
