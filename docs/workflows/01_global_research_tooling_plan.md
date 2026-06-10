# Global Research Tooling Plan

## A. Must-Have User-Level Tools

- Git for version control.
- GitHub CLI for PR and CI operations; currently missing.
- `uv` as the preferred environment and Python CLI manager.
- pre-commit installed through `uv tool install pre-commit`.
- Kaggle CLI credentials stored only at the user level, never in this repository.

## B. Strongly Recommended But Optional

- DVC, installed as a user-level CLI; repository adoption is still a planned migration.
- Pandoc for document conversion.
- Zotero with Better BibTeX for references.
- MiKTeX or TinyTeX plus `latexmk` for local paper builds.
- Docker Desktop for controlled environments.
- VS Code extensions for Python, LaTeX, Markdown, and GitHub Actions.

## C. Approval Required

Do not auto-install full TeX Live, CUDA Toolkit, Docker Desktop, global ML frameworks, or change
credential managers. These are large or security-sensitive changes.

## Reproducible Project Setup

Preferred:

```powershell
uv venv
uv pip install -e ".[dev]"
```

Fallback:

```powershell
python -m venv .venv
python -m pip install -e ".[dev]"
```
