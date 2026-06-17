# LAST_HANDOFF.md

Last completed task: WOB-P0 dataset/materialization audit plus metadata-only manifest-preview freeze
Commit: current task commit
Date: 2026-06-18

## What Changed

- Added dedicated `WOB-P0` tooling:
  - `scripts/run_wob_p0_materialization_audit.py`
  - `src/glitch_detection/wob_p0_audit.py`
  - `tests/test_wob_p0_audit.py`
- Executed the WOB-P0 audit in dry-run, non-locked-only mode with manifest-preview writing
  enabled.
- Froze a metadata-only non-locked manifest preview with SHA256
  `fffbd08be4c5ade02487784b762805ecbfb1d89f962988986ee075854807e54f`.
- Added `docs/research/71_wob_p0_dataset_materialization_audit.md` to record the exact blocker:
  the local attached WOB root satisfies 10 of 120 non-locked rows expected by the frozen split.
- Updated the WOB planning/context docs so they no longer describe WOB as merely `READY_TO_PLAN`.

## Checks Passed

- `python scripts/update_context_cache.py --refresh-boot`
- `python -m pytest -q tests/test_wob_p0_audit.py tests/test_wob_protocol.py tests/test_dataset_protocols.py`
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
- Only audit tooling, tests, and documentation/planning surfaces were changed.
- Locked test remains closed, unmaterialized, and unscored.

## Gate Status After Task

- FIX-0 GPU capability guard: DONE.
- R3 seed42: local extract remains present, but fresh local archive provenance is separate from
  the later R5 evidence bundle.
- R4 seed43/44: artifact-backed rerun after local SHA256 verification and per-seed validator
  passes.
- R4 bundle: artifact-backed rerun after local SHA256 verification.
- R5: COMPLETED_NONLOCKED with provenance-bound episode-level outputs.
- WOB expansion: `BLOCKED_MISSING_INPUTS / WOB-P0_COMPLETE`; report 71 documents the exact local
  materialization gap.
- Locked test: UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED.

## Open Blockers

- WOB remains unopened for training/evaluation pending the missing non-locked tar inputs, a clean
  rerun of `WOB-P0`, an explicit execution command, and a compute budget/runtime decision.
- Seed42 local archive provenance remains separate from the local extracted artifact root used in
  R5, so keep any seed42 wording traceable to the extracted-root hashes already recorded.

## Next Recommended Task

- Provide the missing non-locked WOB tar tree, rerun `WOB-P0`, and only then consider a separate
  `WOB-P1` execution command. Keep WOB and locked test closed in the meantime.

## Files Likely Relevant Next

- `docs/research/70_wob_controlled_expansion_plan.md`
- `docs/research/71_wob_p0_dataset_materialization_audit.md`
- `docs/research/69_r5_tempglitch_identical_episode_results.md`
- `scripts/run_wob_p0_materialization_audit.py`
- `src/glitch_detection/wob_p0_audit.py`
- `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`
