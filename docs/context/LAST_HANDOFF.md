# LAST_HANDOFF.md

Last completed task: K1 learned-baseline artifact intake, validation, and claim-bound result update
Commit: latest `main` commit for this task (see `git log -1`)
Date: 2026-06-24T12:05:00Z

## What Changed

- Validated the downloaded K1 learned-baseline Kaggle tarball and SHA256 sidecar, then extracted
  the bundle for local intake.
- Updated `scripts/validate_learned_baselines.py` so downloaded Kaggle bundles with embedded
  `/kaggle/input/...` provenance can be revalidated locally without relaxing any leakage or
  locked-test checks.
- Added `tests/test_learned_baselines_runner.py` coverage for the local-path remapping validator
  behavior.
- Added `scripts/ingest_k1_learned_baselines.py` to compute bounded follow-up metrics for
  `video_autoencoder`, `cnn_lstm`, and `video_transformer` on the exact currently cited
  TempGlitch follow-up support and to summarize paired deltas against LeWM and the simple
  baselines.
- Added K1 protocol, runbook, results, claim-map, and paper-table updates with bounded wording
  only.

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

- K1 intake is validator-backed with false locked-test materialized/scored flags.
- No locked-test access, materialization, or scoring occurred in this task.
- The new learned-baseline results are bounded to the exact non-locked TempGlitch follow-up
  support and do not justify broad superiority, SOTA, cross-game, SIGReg-benefit, action-benefit,
  or temporal-localization claims.
- No data/output/checkpoint/cache/credential commit is intended.

## Gate Status After Task

- Gates 1-8 passed; Gate 9 remains a bounded non-locked pilot/follow-up evidence lane.
- Gate 10 remains closed.
- K1 is now complete as a downloaded, locally validated learned-baseline evidence bundle with
  paper-facing bounded result updates.
- Locked test remains closed.

## Open Blockers

- Phase P3-P5 evidence is still missing: public benchmark scoring, controlled SIGReg/action
  ablation, and temporal-localization scope/results.
- The current TempGlitch follow-up code defaults and the currently cited validated support are not
  yet fully harmonized; preserve the existing validated support until a separate follow-up freeze
  update is completed.
- Official-kit compile remains a later P7 packaging blocker.

## Next Recommended Task

- Prepare the Phase P3 GlitchBench local package, validator, and claim boundary, then stop before
  the user-operated Kaggle K2 benchmark run.

## Files Likely Relevant Next

- `scripts/ingest_k1_learned_baselines.py`
- `scripts/validate_learned_baselines.py`
- `docs/research/118_k1_learned_baseline_results.md`
- `docs/research/16_claim_registry.md`
- `paper/tables/k1_learned_baselines.tex`
