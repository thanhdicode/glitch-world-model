# LAST_HANDOFF.md

Last completed task: GPU compute-capability failure bucket and fail-fast launch guards added
Commit: pending
Date: 2026-06-17

## What Changed

- Added `gpu_compute_capability` to `src/glitch_detection/failure_triage.py` for P100/`sm_60` /
  `no kernel image` / unsupported PyTorch CUDA-arch failures.
- Kept `gpu_compute_capability` on `stop_and_fix`; only `cuda_oom` still advances the approved
  `8 -> 6 -> 4 -> 2` ladder.
- Added regression coverage in `tests/test_failure_triage.py` for compute-capability,
  `cuda_oom`, and transient-timeout routing.
- Added a direct `sm_70+` fail-fast guard to `scripts/run_kaggle_lewm.py` so direct launches stop
  before entering training on unsupported GPUs.
- Added the same `sm_70+` fail-fast guard to the rendered kernel in
  `src/glitch_detection/lewm_gpu_profile_kaggle.py`, including GPU name and `sm_xy` in the error.
- Appended the new failure bucket to `docs/workflows/failure_modes_registry.md`.

## Checks Passed

- `python -m pytest -q tests -k "failure or gpu or kaggle or cloud"`
- `python -m pytest -q`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/check_claim_registry.py`
- Pending final repository validators before completion:
  - `python scripts/validate_research_release.py --ci`
  - `python scripts/doctor.py`
  - `python scripts/validate_context_cache.py`

## Safety Status

- Kaggle live remains untouched in this task; no relaunch was attempted.
- The compute-capability failure is now explicitly treated as infrastructure/runtime
  incompatibility, not OOM, not model failure, and not data failure.
- Locked test remains closed, unmaterialized, and unscored.
- Seed 43/44 were not launched.
- No data, output, checkpoint, or credential is tracked.

## Gate Status After Task

- Roadmap v3 R1 engineering GPU profile remains complete.
- R2 main-run schedule remains frozen.
- R3 seed 42 is still not passed; this task only hardens classification and fail-fast runtime
  guards around the known P100 incompatibility.

## Open Blockers

- Provide a cloud shell on T4 or newer with the Lance datasets mounted at `LEWM_DATA_ROOT`.
- Seed 43/44 remain blocked until seed 42 produces valid non-locked R3 artifacts.

## Next Recommended Task

- Run R3 seed 42 on a cloud T4+ target. On that machine, execute
  `bash cloud/r3_seed42/setup_runtime.sh`, then `bash cloud/r3_seed42/preflight.sh`; launch
  `bash cloud/r3_seed42/run_seed42_full.sh` only if `preflight_passed.json` is written.

## Files Likely Relevant Next

- `src/glitch_detection/failure_triage.py`
- `scripts/run_kaggle_lewm.py`
- `src/glitch_detection/lewm_gpu_profile_kaggle.py`
- `scripts/validate_cloud_gpu_runtime.py`
- `cloud/r3_seed42/preflight.sh`
- `cloud/r3_seed42/run_seed42_full.sh`
- `docs/research/54_r3_seed42_alternative_gpu_execution_plan.md`
