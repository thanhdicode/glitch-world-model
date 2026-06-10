# Environment Audit

Audit date: June 10, 2026.

## Host

- OS: Microsoft Windows 11 Home Single Language, version `10.0.26200`, 64-bit
- Shell: PowerShell
- Python: `3.14.4`
- Pip: `26.0.1`
- Git: `2.51.2.windows.1`
- Branch / audited commit: `main` / `2b5cd282a12bf84f98e84045ebde5becdc8360d9`
- Python version was observed, not changed.

## Global And User-Level Tools

| Tool | Audit result | Recommendation |
| --- | --- | --- |
| Git | available, `2.51.2.windows.1` | global |
| GitHub CLI (`gh`) | missing | global, install when GitHub CLI workflows are needed |
| uv | available, `0.11.7` | preferred global Python environment/tool manager |
| pipx | missing | optional because uv is available |
| pre-commit | installed with `uv tool`, `4.6.0` | global/user-level |
| DVC | installed with `uv tool`, `3.67.1` | global/user-level CLI; adoption remains gated |
| Kaggle Python package | available, `2.2.1`; executable not on PATH | credential stays outside repo |
| Pandoc | missing | optional global install |
| latexmk / LaTeX | missing | optional global install requiring approval |

## Repository Baseline

- `python -m pytest`: `135 passed`
- `python -m ruff check .`: passed
- `python -m ruff format --check .`: `85 files already formatted`
- Working tree was clean at audit start.

## Research-Lab Upgrade Verification

- `python -m pytest`: `151 passed`
- `python -m ruff check .`: passed
- `python -m ruff format --check .`: `89 files already formatted`
- `python scripts/validate_research_release.py --ci`: passed
- `python scripts/check_claim_registry.py`: passed with `38` unique claim IDs
- `pre-commit run --all-files`: passed
- `dvc dag` and `dvc repro --dry`: passed for the metadata-only release-validation stage
- `latexmk`: missing; local paper compilation skipped and optional installation still requires
  approval

## Installation Boundary

Use global/user-level installs for reusable CLIs such as Git, `uv`, pre-commit, and DVC. Keep
Python libraries, CI rules, scripts, paper files, and configuration project-level. Do not install
full TeX, CUDA Toolkit, Docker Desktop, or large ML frameworks globally without approval.
