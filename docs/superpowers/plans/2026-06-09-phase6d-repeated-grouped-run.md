# Phase 6D Repeated Grouped Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run five fresh pair-suspect grouped TempGlitch refit/selection/locked-test experiments
and produce a reproducible repeated summary.

**Architecture:** Add focused repeated-evaluation orchestration helpers that reuse the existing
manifest, scorer, video aggregation, model selection, and bootstrap interfaces. The CLI writes
only gitignored seed-level and repeated-summary artifacts; committed docs record methodology and
claim-safe results.

**Tech Stack:** Python 3.10+, NumPy, Pillow, pytest, ruff.

---

### Task 1: Protocol-Safe Scorer Fitting

**Files:**
- Create: `src/glitch_detection/repeated_eval.py`
- Test: `tests/test_repeated_eval.py`

- [ ] Write failing tests proving fitted scorers use only train-normal records and fit metadata
  excludes validation/test sources.
- [ ] Run `python -m pytest tests/test_repeated_eval.py -q` and confirm failure.
- [ ] Implement fitted scorer and validation scoring helpers.
- [ ] Run `python -m pytest tests/test_repeated_eval.py -q` and confirm pass.

### Task 2: Validation Selection And Locked Test

**Files:**
- Modify: `src/glitch_detection/repeated_eval.py`
- Modify: `tests/test_repeated_eval.py`

- [ ] Write failing tests proving every validation candidate is available before selection and
  only the selected scorer is evaluated on test.
- [ ] Run the targeted tests and confirm failure.
- [ ] Implement validation candidate construction and locked-test evaluation with grouped CI.
- [ ] Run the targeted tests and confirm pass.

### Task 3: Repeated Runner And Reports

**Files:**
- Modify: `scripts/run_tempglitch_repeated_grouped_splits.py`
- Modify: `tests/test_repeated_grouped_runner.py`

- [ ] Write failing tests for dry-run/full-run output schema, zero leakage, and repeated summary.
- [ ] Run the targeted tests and confirm failure.
- [ ] Implement dry-run/full-run orchestration and JSON/Markdown writers.
- [ ] Run the targeted tests and confirm pass.

### Task 4: Execute And Document

**Files:**
- Create: `docs/research/28_phase6d_repeated_grouped_results.md`
- Modify: `README.md`
- Modify: `docs/research/15_reproducibility_checklist.md`
- Modify: `docs/research/16_claim_registry.md`

- [ ] Run the dry-run command and inspect every seed leakage report.
- [ ] Run the full five-seed command if local inputs are complete.
- [ ] Record exact results and limitations without copying generated outputs into Git.
- [ ] Run `python -m pytest`, `python -m ruff check .`, and `python -m ruff format --check .`.
- [ ] Audit staged files, commit, and push.
