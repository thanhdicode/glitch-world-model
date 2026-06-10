# New Research Project Bootstrap

1. Create the folder structure in `research_project_template.md`.
2. Initialize Git and add an artifact-focused `.gitignore`.
3. Write AGENTS.md before experiments.
4. Add a claim registry and define accepted statuses.
5. Define dataset, validation, locked-test, and publication release gates.
6. Create a minimal `pyproject.toml` with separate `dev`, `research`, and GPU extras.
7. Add pytest, Ruff, pre-commit, and lightweight CI.
8. Add release and claim validators.
9. Create a cautious paper scaffold with table provenance.
10. Run baseline verification and record the environment audit.

Preferred setup:

```powershell
uv venv
uv pip install -e ".[dev]"
pre-commit install
python -m pytest
python -m ruff check .
python scripts/validate_research_release.py --ci
```

Do not begin with GPU training or locked-test evaluation. Establish interfaces, governance, and a
small reproducible baseline first.
