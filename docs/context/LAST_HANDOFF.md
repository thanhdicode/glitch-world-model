# LAST_HANDOFF.md

Last completed task: WOB-P0 Kaggle evidence sync and WOB-P1 seed42 runner preparation
Commit: current task commit
Date: 2026-06-18

## What Changed

- Verified the downloaded Kaggle-native `WOB-P0` evidence bundle and confirmed:
  `READY_FOR_WOB_P1`, 120 selected rows, 120 resolved rows, 0 missing rows, 59 locked rows
  skipped, locked test closed, and no performance metrics.
- Added `scripts/verify_wob_p0_kaggle_evidence.py` so the downloaded WOB-P0 audit bundle can be
  rechecked locally without extracting raw symlinked episode payloads.
- Updated the claim registry, roadmap, WOB docs, and context status to distinguish:
  local `WOB-P0` still blocked, Kaggle-native `WOB-P0` passed, `WOB_STATUS=READY_FOR_WOB_P1`,
  `WOB_P1_TRAINING_STATUS=NOT_STARTED`.
- Added the seed42-only one-section Kaggle runner package under `cloud/wob_p1_seed42/`.
- Reused the existing real LeWM Kaggle trainer and WOB Lance conversion path instead of inventing
  a new training command.
- Added `scripts/validate_wob_seed42_artifacts.py` plus focused tests for bundle verification,
  P1 selection filtering, packaging hygiene, and the one-section Kaggle command.

## Checks Passed

- `python scripts/verify_wob_p0_kaggle_evidence.py --tarball C:\Users\ADMIN\Downloads\wob_p0_kaggle_audit_outputs.tar.gz --sha256 C:\Users\ADMIN\Downloads\wob_p0_kaggle_audit_outputs.tar.gz.sha256`
- `python -m pytest -q tests/test_verify_wob_p0_kaggle_evidence.py tests/test_wob_p1_seed42_runner.py tests/test_wob_kaggle_native_prepare.py tests/test_wob_p0_audit.py tests/test_wob_protocol.py tests/test_run_kaggle_lewm.py`
- Remaining full validation suite runs after this handoff update.

## Safety Status

- No local WOB training, WOB evaluation, locked-test action, or WOB seed43/44 launch was run in
  this task.
- No broad LeWM superiority, state-of-the-art, temporal-localization, SIGReg-benefit, WOB-result,
  cross-game, or locked-test claim was added.
- Only verification tooling, tests, safe Kaggle-runner scripts, and documentation/status surfaces
  were changed.
- Locked test remains closed, unmaterialized, and unscored.

## Gate Status After Task

- FIX-0 GPU capability guard: DONE.
- R3 seed42: local extract remains present, but fresh local archive provenance is separate from
  the later R5 evidence bundle.
- R4 seed43/44: artifact-backed rerun after local SHA256 verification and per-seed validator
  passes.
- R4 bundle: artifact-backed rerun after local SHA256 verification.
- R5: COMPLETED_NONLOCKED with provenance-bound episode-level outputs.
- WOB expansion: local `WOB-P0` is `BLOCKED_MISSING_INPUTS`, Kaggle-native `WOB-P0` is `PASSED`,
  `WOB_STATUS=READY_FOR_WOB_P1`, and `WOB-P1` remains not started.
- Locked test: UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED.

## Open Blockers

- WOB evaluation remains unopened pending a future explicit command after seed42 artifacts exist.
- The prepared `WOB-P1` runner still depends on the Kaggle runtime successfully installing the
  LeWM runtime packages and completing the first real-action seed42 training pass.

## Next Recommended Task

- Create a Kaggle notebook, attach the same two official WOB datasets, and run the one-section
  seed42 command from `cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh`. Download only
  `wob_seed42_artifacts.tar.gz` and its `.sha256`. Keep seed43/44, WOB evaluation, and locked
  test closed in the meantime.

## Files Likely Relevant Next

- `docs/research/70_wob_controlled_expansion_plan.md`
- `docs/research/71_wob_p0_dataset_materialization_audit.md`
- `scripts/verify_wob_p0_kaggle_evidence.py`
- `cloud/wob_p1_seed42/README.md`
- `cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh`
- `scripts/validate_wob_seed42_artifacts.py`
- `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`
