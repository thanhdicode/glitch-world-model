# Research-Grade Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the repository into a reusable, research-grade ML lab without touching locked
test, running training, uploading data, or implementing LeWM.

**Architecture:** Keep governance and operating procedures in `docs/workflows/`, scientific
planning in `docs/research/`, executable release checks in small standalone Python scripts, and
paper-facing summaries in `paper/`. CI and pre-commit call the same repository-local validators
used by developers.

**Tech Stack:** Python 3.10+, pytest, Ruff, pre-commit, GitHub Actions, LaTeX, Markdown.

---

### Task 1: Environment Audit And Governance

**Files:**
- Create: `docs/workflows/00_environment_audit.md`
- Create: `docs/workflows/01_global_research_tooling_plan.md`
- Modify: `AGENTS.md`
- Create: `docs/workflows/codex_task_protocol.md`
- Create: `docs/workflows/research_claim_protocol.md`
- Create: `docs/workflows/experiment_release_gates.md`
- Create: `docs/workflows/paper_writing_protocol.md`
- Create: `docs/workflows/kaggle_gpu_protocol.md`
- Create: `docs/workflows/lewm_integration_protocol.md`

- [ ] Record the verified Windows, Python, Git, tool, test, and Ruff audit.
- [ ] Document global versus project-level installation decisions.
- [ ] Add scientific honesty, locked-test, Kaggle, LeWM, Git, and final-response rules.
- [ ] Review every governance document against the prohibited-action list.

### Task 2: Release Validators Using TDD

**Files:**
- Create: `tests/test_research_release_tools.py`
- Create: `scripts/validate_research_release.py`
- Create: `scripts/check_claim_registry.py`
- Create: `scripts/make_paper_tables.py`

- [ ] Write failing tests for tracked-file policy, required release files, claim parsing, duplicate
  claims, invalid statuses, and documented table generation.
- [ ] Run `python -m pytest tests/test_research_release_tools.py -q` and confirm expected failures.
- [ ] Implement the smallest validator and table-generator APIs that satisfy the tests.
- [ ] Run focused tests and refactor while green.

### Task 3: Project Tooling And CI

**Files:**
- Modify: `.pre-commit-config.yaml`
- Modify: `.github/workflows/ci.yml`
- Create: `.github/workflows/paper.yml`
- Modify: `pyproject.toml`

- [ ] Configure non-mutating Ruff and repository hygiene hooks.
- [ ] Make CI run tests, Ruff, formatting, and research release validation.
- [ ] Add a lightweight paper workflow with LaTeX compilation when available and file checks
  otherwise.
- [ ] Keep Torch and GPU dependencies optional.

### Task 4: Paper Scaffold And Documented Tables

**Files:**
- Create: `paper/main.tex`
- Create: `paper/references.bib`
- Create: `paper/README.md`
- Create: `paper/figures/README.md`
- Generate: `paper/tables/phase6d_results.tex`
- Generate: `paper/tables/phase6e_validation_metrics.tex`
- Generate: `paper/tables/phase6e_validation_metrics.md`

- [ ] Write cautious FISAT-ready paper sections and explicit anti-overclaim language.
- [ ] Add comments marking future LeWM result locations.
- [ ] Generate paper tables from documented Phase 6D and Phase 6E summaries.
- [ ] Validate required paper files without requiring local LaTeX.

### Task 5: Migration And Reusable Project Templates

**Files:**
- Create: `docs/research/40_research_tooling_stack.md`
- Create: `docs/research/41_dvc_hydra_migration_plan.md`
- Create: `docs/research/42_experiment_tracking_plan.md`
- Create: `configs/research_lab.yaml`
- Create: `configs/lewm_phase7.yaml`
- Create: `docs/workflows/research_project_template.md`
- Create: `docs/workflows/new_research_project_bootstrap.md`

- [ ] Document DVC, Hydra, and MLflow boundaries without performing a full migration.
- [ ] Add configuration drafts that do not run LeWM or training.
- [ ] Add a reusable lab structure, governance template, and Codex prompt.

### Task 6: README, Verification, And Commit

**Files:**
- Modify: `README.md`

- [ ] Document project dev installation, pre-commit, release validation, paper checks, current
  Phase 6E status, and locked-test warning.
- [ ] Run full pytest, Ruff lint, Ruff format, release validator, claim checker, pre-commit, and
  paper check.
- [ ] Run `git diff --check` and audit tracked files for prohibited artifacts.
- [ ] Commit only source, docs, config, scripts, tests, and paper scaffold with the requested
  commit message.
