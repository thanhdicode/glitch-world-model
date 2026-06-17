# LAST_HANDOFF.md

Last completed task: R4 rerun artifact verification and R5 planning refresh
Commit: pending
Date: 2026-06-17

## What Changed

- Added ignore coverage for `artifacts/downloads/` and `artifacts/verified/`.
- Copied the six human-downloaded R4 rerun files into the ignored local path
  `artifacts/downloads/r4_rerun_2026_06_17/`.
- Verified the local SHA256 values for `r3_seed43_artifacts.tar.gz`,
  `r3_seed44_artifacts.tar.gz`, and `r4_seed43_44_artifacts_bundle.tar.gz` and confirmed that the
  `.sha256` sidecars matched.
- Extracted the seed43/44 archives into `artifacts/verified/r4_rerun_2026_06_17/` and ran
  `scripts/validate_lewm_r3_seed_artifacts.py` successfully for both seeds.
- Updated the context-cache generator, context docs, claim registry, R3/R4 status record,
  README, AGENTS, PLAYBOOK, paper scaffold, and added the R5 identical-episode evaluation plan.

## Checks Passed

- `python scripts/validate_lewm_r3_seed_artifacts.py --artifact-root artifacts/verified/r4_rerun_2026_06_17/r3_seed43 --expected-seed 43 --expected-target-updates 15000`
- `python scripts/validate_lewm_r3_seed_artifacts.py --artifact-root artifacts/verified/r4_rerun_2026_06_17/r3_seed44 --expected-seed 44 --expected-target-updates 15000`
- `python -m pytest -q`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/check_claim_registry.py`
- `python scripts/validate_context_cache.py`
- `python scripts/doctor.py`
- `python scripts/validate_research_release.py --ci`
- `pre-commit run --all-files`
- `git diff --check`

## Safety Status

- No cloud/Kaggle training was launched.
- No R5 execution was launched.
- No locked-test materialization or scoring was attempted.
- No detection-performance, AUROC, AUPRC, superiority, temporal-localization, SIGReg-benefit,
  WOB, or locked-test claim was added.
- The downloaded archives and extracted artifact roots remain inside ignored local folders only.
- Locked test remains closed, unmaterialized, and unscored.

## Gate Status After Task

- FIX-0 GPU capability guard: DONE.
- R3 seed42: local extract remains present, but fresh local archive provenance is separate from
  this R4 rerun confirmation.
- R4 seed43/44: artifact-backed rerun after local SHA256 verification and per-seed validator
  passes.
- R4 bundle: artifact-backed rerun after local SHA256 verification.
- R5: NOT_STARTED.
- WOB expansion: NOT_STARTED.
- Locked test: UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED.

## Open Blockers

- R5 identical-episode evaluation has not yet generated any non-locked LeWM detection metrics.
- The exact R5 identical-episode command sequence and provenance bundle still need to be frozen
  before execution.
- Seed42 local archive provenance remains separate from this R4 rerun confirmation.

## Next Recommended Task

- Prepare and, only with an explicit command, execute the non-locked R5 identical-episode
  evaluation.

## Files Likely Relevant Next

- `docs/research/68_r5_identical_episode_eval_plan.md`
- `docs/research/67_r3_r4_multiseed_status.md`
- `scripts/run_gate7_lance_scoring.py`
- `scripts/run_gate8_baselines_from_lance.py`
- `scripts/run_gate7_lewm_evaluation.py`
