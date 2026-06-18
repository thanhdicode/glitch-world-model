# LAST_HANDOFF.md

Last completed task: WOB Kaggle-native pipeline preparation
Commit: current task commit
Date: 2026-06-18

## What Changed

- Stopped and cleaned the accidental local full-download direction for WOB after confirming it was
  not the intended workflow.
- Removed partial local acquisition artifacts from the temporary WOB probe/full-download roots
  after recording their size and purpose.
- Replaced the unsafe local acquisition helper with `scripts/check_wob_kaggle_listing.py`, which
  verifies the official Kaggle listings without downloading 63 GiB locally.
- Added a Kaggle-native WOB root-preparation tool and cloud package under
  `cloud/wob_kaggle_native/`.
- Verified that all 120 non-locked rows exist in the authoritative Kaggle listings and that the
  intended next step is a Kaggle-native `WOB-P0` audit, not local full acquisition.
- Updated status docs, roadmap text, claim registry, and onboarding docs to reflect:
  local `WOB-P0` blocked, Kaggle-native `WOB-P0` ready, `WOB-P1` still not started.

## Checks Passed

- `python scripts/check_wob_kaggle_listing.py`
- `python -m pytest -q tests/test_wob_p0_audit.py tests/test_wob_protocol.py tests/test_wob_kaggle_native_prepare.py tests/test_check_wob_kaggle_listing.py`
- `python scripts/update_context_cache.py --refresh-boot`
- `python -m pytest -q`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/check_claim_registry.py`
- `python scripts/doctor.py`
- `python scripts/validate_research_release.py --ci`
- Remaining final git/pre-commit checks run after this handoff update.

## Safety Status

- No cloud/Kaggle training, WOB training, WOB evaluation, R6 ablation, or locked-test action was
  launched in this task.
- No broad LeWM superiority, state-of-the-art, temporal-localization, SIGReg-benefit, WOB-result,
  cross-game, or locked-test claim was added.
- Only audit/check tooling, tests, cloud-prep scripts, and documentation/planning surfaces were
  changed.
- Locked test remains closed, unmaterialized, and unscored.

## Gate Status After Task

- FIX-0 GPU capability guard: DONE.
- R3 seed42: local extract remains present, but fresh local archive provenance is separate from
  the later R5 evidence bundle.
- R4 seed43/44: artifact-backed rerun after local SHA256 verification and per-seed validator
  passes.
- R4 bundle: artifact-backed rerun after local SHA256 verification.
- R5: COMPLETED_NONLOCKED with provenance-bound episode-level outputs.
- WOB expansion: local `WOB-P0` is `BLOCKED_MISSING_INPUTS`, Kaggle-native `WOB-P0` is ready to
  run, and `WOB-P1` remains not started.
- Locked test: UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED.

## Open Blockers

- WOB remains unopened for training/evaluation pending a Kaggle-native `WOB-P0` execution result,
  an explicit execution command, and a compute budget/runtime decision.
- Seed42 local archive provenance remains separate from the local extracted artifact root used in
  R5, so keep any seed42 wording traceable to the extracted-root hashes already recorded.

## Next Recommended Task

- Create a Kaggle notebook, attach the official WOB datasets, run the Kaggle-native `WOB-P0`
  audit package, and only then consider a separate `WOB-P1` execution command. Keep WOB and
  locked test closed in the meantime.

## Files Likely Relevant Next

- `docs/research/70_wob_controlled_expansion_plan.md`
- `docs/research/71_wob_p0_dataset_materialization_audit.md`
- `scripts/check_wob_kaggle_listing.py`
- `cloud/wob_kaggle_native/README.md`
- `cloud/wob_kaggle_native/prepare_wob_root.py`
- `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`
