# Phase 6E Kaggle Video Autoencoder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible Kaggle-compatible Conv3D autoencoder training and validation-scoring
package without touching locked test data.

**Architecture:** Keep PyTorch behind a lazy optional dependency in a focused scorer module.
Use a separate experiment runner to derive train-normal and validation records from the existing
grouped split, rebase local clip paths for Kaggle, train once, and score validation only.

**Tech Stack:** Python 3.10+, PyTorch, Pillow, existing CSV interfaces, pytest, ruff.

---

### Task 1: Portable Split Preparation

**Files:**
- Create: `src/glitch_detection/neural_protocol.py`
- Test: `tests/test_neural_protocol.py`

- [ ] Write failing tests showing that records rebase to
  `<clips-root>/<source>/clips/<clip_id>`, train-normal selection excludes buggy and non-train
  sources, validation selection is split-only, and cross-split groups are rejected.
- [ ] Run `python -m pytest tests/test_neural_protocol.py -q` and verify failure because the
  module does not exist.
- [ ] Implement `rebase_clip_records` and `prepare_neural_partitions` using existing
  `ClipRecord`, `read_split_csv`, and `validate_no_group_leakage` contracts.
- [ ] Run `python -m pytest tests/test_neural_protocol.py -q` and verify all focused tests pass.

### Task 2: Optional Video Autoencoder Scorer

**Files:**
- Create: `src/glitch_detection/video_autoencoder.py`
- Modify: `src/glitch_detection/score_clips.py`
- Modify: `pyproject.toml`
- Test: `tests/test_video_autoencoder.py`
- Test: `tests/test_score_clips.py`

- [ ] Write failing tests for scorer registration, checkpoint resolution, configuration
  validation, and clear dependency failure when PyTorch is unavailable.
- [ ] Run the focused tests and verify they fail because the scorer is absent.
- [ ] Implement lazy PyTorch import, configuration validation, fixed-length RGB clip loading,
  compact Conv3D model construction, train/checkpoint metadata, checkpoint loading, and
  interface-compatible scoring.
- [ ] Add the `gpu` optional dependency and register `video_autoencoder` without changing the
  scorer function signature.
- [ ] Run focused tests and verify they pass without PyTorch installed.

### Task 3: Kaggle Training Runner

**Files:**
- Create: `scripts/run_kaggle_video_autoencoder.py`
- Test: `tests/test_kaggle_video_autoencoder_runner.py`

- [ ] Write failing tests for dry-run metadata and leakage rejection.
- [ ] Run the focused tests and verify failure because the runner does not exist.
- [ ] Implement a CLI that reads manifest and grouped split, optionally rebases clip paths,
  writes generated partition manifests, dry-runs protocol validation, and otherwise trains then
  scores validation only.
- [ ] Run focused tests and verify they pass.

### Task 4: Research Documentation

**Files:**
- Create: `docs/research/29_phase6e_kaggle_video_autoencoder_protocol.md`
- Modify: `README.md`
- Modify: `docs/research/08_reproducibility_checklist.md`
- Modify: `docs/research/16_claim_registry.md`

- [ ] Document Kaggle setup, dry-run, real training command, generated artifacts, and locked-test
  boundary.
- [ ] State explicitly that no model has been trained and no result exists until a Kaggle run
  completes.
- [ ] Add a pending claim entry for the neural baseline.

### Task 5: Verification And Delivery

**Files:**
- Inspect: all changed files

- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m ruff format --check .`.
- [ ] Run the Kaggle runner in dry-run mode against the local Phase 6D seed-42 inputs.
- [ ] Audit `git status` and ensure no data, outputs, checkpoint, or cache artifact is staged.
- [ ] Commit and push the completed phase.

