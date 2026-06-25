# LAST_HANDOFF.md

Last completed task: K2 GlitchBench scientific bundle intake, bounded results registration, and
P4/K3 handoff preparation
Commit: latest branch commit for this task (see `git log -1`)
Date: 2026-06-25T00:00:00Z

## What Changed

- Added `scripts/ingest_k2_glitchbench_benchmark.py`, a dedicated local intake helper for the
  downloaded scientific K2 bundle.
- Added `tests/test_ingest_k2_glitchbench_benchmark.py` to cover nested bundle discovery, tarball
  SHA256 sidecar verification, and summary generation.
- Extracted and intake-validated the downloaded K2 bundle in local ignored intake locations
  retained outside Git.
- Registered the validated K2 scientific receipt, bounded result surface, and threshold-calibration
  limitation in:
  - `docs/research/120_kaggle_k2_glitchbench_runbook.md`
  - `docs/research/121_glitchbench_claim_boundary.md`
  - `docs/research/122_k2_glitchbench_results.md`
  - `docs/research/16_claim_registry.md`
  - `docs/research/70_paper_claim_map.md`
- Added `docs/research/123_kaggle_k3_ablation_runbook.md` so the next roadmap gate is explicit and
  reproducible.
- Replaced the pending GlitchBench paper table with a bounded K2 results table and updated the
  paper claim/limitation tables.
- Updated the context cache so the repo now points to P4/K3 rather than another K2 rerun.

## Checks Passed

- focused K2 intake tests
- K2 scientific bundle intake helper on the downloaded tarball and SHA256 sidecar
- K2 tarball SHA256 sidecar verification
- full repository verification suite still pending until this task's final code/docs diff is
  checked at completion

## Safety Status

- GlitchBench remains image-level and synthetic-normal.
- K2 supports a bounded negative comparison for LeWM on this exact split only.
- The K2 AUROC `1.0` non-LeWM rows still require threshold-calibration caution under the shared
  train-normal `p95` rule.
- No temporal-localization, cross-game generalization, SOTA, SIGReg benefit, action-conditioning
  benefit, or locked-test claim was added.
- No locked-test access, materialization, or scoring occurred in this task.

## Gate Status After Task

- P3/K2 is now complete at the local intake level.
- The next external action is Kaggle K3 for controlled SIGReg and action-conditioning ablations.
- P5 remains blocked until K3 validates.
- Gate 10 remains closed.

## Open Blockers

- K3 still requires a user-operated Kaggle launch plus local post-run intake.
- No mechanistic claim may enter the paper until K3 validates.
- GlitchBench cannot support temporal-localization claims on the current public path.

## Next Recommended Task

- Run the K3 dry-run and scientific ablation launch from
  `docs/research/123_kaggle_k3_ablation_runbook.md`, then validate the downloaded controlled-pair
  artifact locally before any SIGReg or action-conditioning claim enters the registry.

## Files Likely Relevant Next

- `scripts/run_r6_sigreg_ablation.py`
- `scripts/validate_r6_ablations.py`
- `docs/research/123_kaggle_k3_ablation_runbook.md`
- `docs/research/16_claim_registry.md`
- `docs/context/NEXT_ACTION.md`
