# LAST_HANDOFF.md

Last completed task: P3 GlitchBench local package preparation plus P4 controlled-ablation local tooling
Commit: latest `main` commit for this task (see `git log -1`)
Date: 2026-06-24T17:20:00Z

## What Changed

- Added a fail-closed `glitchbench_protocol` module covering label mapping, image-level limits,
  grouped split validation, and explicit synthetic-normal handling.
- Upgraded `scripts/download_glitchbench_subset.py` from a lightweight demo downloader into a
  structured subset-ingestion path that materializes paired synthetic-normal and buggy clips.
- Added `scripts/freeze_glitchbench_split.py`, `scripts/build_k2_glitchbench_kaggle_dataset.py`,
  `scripts/validate_glitchbench_bundle.py`, and `scripts/run_kaggle_glitchbench_benchmark.py`.
- Built and locally validated a real K2 input zip for the bounded GlitchBench subset.
- Added local controlled-pair SIGReg/action ablation tooling via
  `scripts/run_r6_sigreg_ablation.py`, extended `scripts/validate_r6_ablations.py`, and updated
  `src/glitch_detection/lewm_training.py` so zero-action training is a real variant rather than a
  metadata placeholder.
- Added protocol/runbook/claim-boundary docs, a pending paper table slot, and focused tests for
  the new P3/P4 local surfaces.

## Checks Passed

- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/validate_research_release.py --ci`
- `python scripts/check_claim_registry.py`
- `python scripts/doctor.py`
- `python scripts/validate_context_cache.py`
- `git diff --check`

## Safety Status

- The local GlitchBench package is validator-backed with false locked-test materialized/scored
  flags.
- GlitchBench remains image-level and uses synthetic normal clips explicitly.
- No GlitchBench metric claim was added because K2 has not run.
- No SIGReg or action-conditioning effect claim was added because K3 has not run.
- No locked-test access, materialization, or scoring occurred in this task.

## Gate Status After Task

- P3 local preparation is complete and K2 is ready for a user-operated Kaggle run.
- P4 local controlled-ablation tooling is ready, but K3 evidence is still pending.
- Gate 10 remains closed.
- Locked test remains closed.

## Open Blockers

- K2 still requires a user-operated Kaggle launch and local post-run validation.
- K3 still requires a user-operated Kaggle ablation run and local post-run validation.
- GlitchBench cannot support temporal-localization claims on the current public path.
- Official-kit compile remains a later P7 packaging blocker.

## Next Recommended Task

- Upload the prepared K2 GlitchBench zip to Kaggle, attach the required LeWM seed-artifact dataset
  if needed, run K2, and validate the downloaded bundle locally before any GlitchBench metric
  enters the claim registry.

## Files Likely Relevant Next

- `scripts/build_k2_glitchbench_kaggle_dataset.py`
- `scripts/validate_glitchbench_bundle.py`
- `scripts/run_kaggle_glitchbench_benchmark.py`
- `docs/research/120_kaggle_k2_glitchbench_runbook.md`
- `scripts/run_r6_sigreg_ablation.py`
