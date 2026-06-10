# Phase 6E Kaggle Launch Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing Phase 6E Conv3D learned baseline directly launchable on Kaggle and
make downloaded GPU artifacts auditable without touching locked test.

**Architecture:** Add one preparation script that validates and copies/symlinks the processed
clip tree into a Kaggle-upload folder, and one ingestion script that validates CUDA training
artifacts and optionally evaluates validation scores only. Keep all generated datasets,
checkpoints, scores, and reports under existing gitignored output paths.

**Tech Stack:** Python standard library, existing CSV/JSON interfaces, pytest, ruff.

---

### Task 1: Dataset Preparation Script

**Files:**
- Create: `scripts/prepare_phase6e_kaggle_dataset.py`
- Test: `tests/test_prepare_phase6e_kaggle_dataset.py`

- [ ] Write failing tests for dry-run validation and copy-mode output layout.
- [ ] Verify tests fail because the preparation module does not exist.
- [ ] Implement manifest/split/clip validation, size estimation, dry-run, copy, and symlink modes.
- [ ] Verify focused tests pass.

### Task 2: Artifact Ingestion Script

**Files:**
- Create: `scripts/ingest_phase6e_kaggle_artifacts.py`
- Test: `tests/test_ingest_phase6e_kaggle_artifacts.py`

- [ ] Write failing tests for missing files, CPU rejection, NaN rejection, test-scored rejection,
  and valid CUDA artifact summary.
- [ ] Verify tests fail because the ingestion module does not exist.
- [ ] Implement strict schema/protocol validation, Markdown/JSON reports, and optional
  validation-only metrics.
- [ ] Verify focused tests pass.

### Task 3: Kaggle Launch Documentation

**Files:**
- Create: `kaggle/phase6e_video_autoencoder/README.md`
- Create: `kaggle/phase6e_video_autoencoder/phase6e_kaggle_cells.md`
- Create: `kaggle/phase6e_video_autoencoder/dataset-metadata.template.json`
- Create: `kaggle/phase6e_video_autoencoder/DO_NOT_COMMIT_ARTIFACTS.md`
- Create: `docs/research/30_phase6e_kaggle_run_log_template.md`
- Modify: `README.md`

- [ ] Document private dataset preparation, notebook settings, five copy-paste cells, outputs,
  download/ingest workflow, and prohibited claims.
- [ ] Add a run-log template that records environment, protocol counts, artifacts, and claim
  status.
- [ ] Link the launch package and run-log template from the root README.

### Task 4: Verification And Delivery

**Files:**
- Inspect: all changed files

- [ ] Run focused tests.
- [ ] Run `python scripts/prepare_phase6e_kaggle_dataset.py --dry-run`.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m ruff format --check .`.
- [ ] Audit staged files for generated data, outputs, checkpoints, and secrets.
- [ ] Commit and push the completed launch package.
