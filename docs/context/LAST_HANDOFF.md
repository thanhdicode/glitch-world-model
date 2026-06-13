# LAST_HANDOFF.md

Last completed task: R3 seed 42 provider-agnostic cloud runner prepared
Commit: pending
Date: 2026-06-13

## What Changed

- Kept Kaggle stopped for R3 after two consecutive unsupported P100 assignments.
- Added a provider-agnostic R3 seed 42 cloud runner under `cloud/r3_seed42/`.
- Added `scripts/validate_cloud_gpu_runtime.py` to write `cloud_runtime_preflight.json` and require
  CUDA `sm_70+` plus at least 14 GB VRAM.
- Added `scripts/validate_lewm_r3_seed_artifacts.py` as the post-run R3 seed 42 validation gate.
- Added progress logging every 100 update-based LeWM optimizer updates.
- Added honest paper placeholders and cloud execution records for T4 x2 or stronger GPU execution.

## Checks Passed

- Pending final focused checks before commit:
  - `python -m pytest tests/test_lewm_kaggle.py tests/test_lewm_training.py tests/test_run_kaggle_lewm.py tests/test_lewm_research_mvp_config.py -q`
  - `python scripts/validate_research_release.py --ci`
  - `python scripts/check_claim_registry.py`
  - `python scripts/validate_context_cache.py`

## Safety Status

- Kaggle remains blocked for R3; no new Kaggle retry was launched after the P100 stop decision.
- No non-Kaggle GPU shell was available in this Codex session, so T4 x2 execution is prepared but
  not launched.
- No successful R3 seed 42 training result was produced.
- Locked test remains closed, unmaterialized, and unscored.
- Seed 43/44 were not launched.
- No data, output, checkpoint, or credential is tracked.

## Gate Status After Task

- Roadmap v3 R1 engineering GPU profile remains complete.
- R2 main-run schedule exists, but R3 seed 42 is not passed.
- The active R3 blocker is direct shell/provider access to a compatible GPU VM. The selected target
  is T4 x2, which satisfies the `sm_70+` guard if provisioned with a CUDA-compatible PyTorch build.

## Open Blockers

- Provide a RunPod/Colab/A100/H100/T4 shell with the Lance datasets mounted at `LEWM_DATA_ROOT`.
- Seed 43/44 remain blocked until seed 42 produces valid non-locked R3 artifacts.

## Next Recommended Task

- On the T4 x2 machine, run `bash cloud/r3_seed42/setup_runtime.sh`, then
  `bash cloud/r3_seed42/preflight.sh`; launch `bash cloud/r3_seed42/run_seed42_full.sh` only if
  `preflight_passed.json` is written.

## Files Likely Relevant Next

- `cloud/r3_seed42/README.md`
- `scripts/validate_cloud_gpu_runtime.py`
- `scripts/validate_lewm_r3_seed_artifacts.py`
- `src/glitch_detection/lewm_training.py`
- `docs/research/54_r3_seed42_alternative_gpu_execution_plan.md`
- `docs/research/55_r3_seed42_cloud_run_record.md`
- `docs/research/53_r3_seed42_live_run_record.md`
