# Phase 6E Kaggle Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a secure, resumable Kaggle state-machine orchestrator with fingerprint-bound
one-time approvals, conservative retries, and dry-run verification.

**Architecture:** Put reusable state, approval, security, fingerprint, command, package, and
artifact logic in `src/glitch_detection/kaggle_automation.py`. Keep
`scripts/run_phase6e_kaggle_automation.py` as a thin CLI. Inject command execution so tests never
perform live Kaggle side effects.

**Tech Stack:** Python standard library, existing Phase 6E scripts/interfaces, pytest, ruff.

---

### Task 1: State, Fingerprint, Approval, Security

**Files:**
- Create: `src/glitch_detection/kaggle_automation.py`
- Create: `tests/test_kaggle_automation_foundation.py`

- [ ] Write failing tests for atomic state backup, fingerprint fields, one-time approvals,
  approval invalidation, forbidden paths, and redaction.
- [ ] Verify focused tests fail because the module does not exist.
- [ ] Implement minimal foundation components.
- [ ] Verify focused tests pass.

### Task 2: Retry And Artifact Validation

**Files:**
- Modify: `src/glitch_detection/kaggle_automation.py`
- Create: `tests/test_kaggle_automation_validation.py`

- [ ] Write failing tests for transient-only retry, GPU quota blocking, dataset/kernel package
  validation, and artifact validation reports.
- [ ] Verify focused tests fail.
- [ ] Implement minimal validation and retry components.
- [ ] Verify focused tests pass.

### Task 3: Orchestrator And CLI

**Files:**
- Modify: `src/glitch_detection/kaggle_automation.py`
- Create: `scripts/run_phase6e_kaggle_automation.py`
- Create: `tests/test_kaggle_automation_orchestrator.py`

- [ ] Write failing tests for dry-run transitions, approval blocking, resume, and same-fingerprint
  kernel push suppression.
- [ ] Verify focused tests fail.
- [ ] Implement orchestrator and thin CLI with no live action during dry-run.
- [ ] Verify focused tests pass.

### Task 4: Documentation And Verification

**Files:**
- Modify: `kaggle/phase6e_video_autoencoder/README.md`
- Modify: `docs/research/29_phase6e_kaggle_video_autoencoder_protocol.md`
- Modify: `README.md`

- [ ] Document dry-run, approval commands, state/log paths, resume behavior, and live-run warning.
- [ ] Run orchestrator dry-run.
- [ ] Run full pytest and ruff checks.
- [ ] Audit staged files, commit, and push.
