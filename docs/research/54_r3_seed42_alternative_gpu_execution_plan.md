# R3 Seed 42 Alternative GPU Execution Plan

Date: 2026-06-13

Evidence class: execution-plan-only

## Reason

Kaggle is blocked for R3 because it assigned unsupported Tesla P100 `sm_60` GPUs twice in a row.
The current PyTorch runtime requires `sm_70+`, and the CUDA guard correctly stops before training.

## Target GPU

The user selected T4 x2 as the next execution target. T4 is compute capability `sm_75` and meets
the `sm_70+` guard. A single T4 is sufficient for the current single-process runner; T4 x2 is
acceptable as a provider configuration, but this runner does not use distributed data parallelism.

Preferred stronger alternatives remain H100, A100 80GB, L40S, RTX 4090, or A10.

## Cloud Package

The provider-agnostic runner lives under `cloud/r3_seed42/` and expects:

```bash
export LEWM_REPO_ROOT=/workspace/glitch-world-model
export LEWM_DATA_ROOT=/workspace/lewm_data
export LEWM_OUTPUT_ROOT=/workspace/lewm_outputs/r3_seed42
```

Expected inputs:

```text
$LEWM_DATA_ROOT/tempglitch_train_normal_all_local.lance
$LEWM_DATA_ROOT/tempglitch_validation_normal_all_local.lance
```

No validation-buggy or locked-test path is used.

## Execution Commands

```bash
git clone https://github.com/thanhdicode/glitch-world-model.git /workspace/glitch-world-model
cd /workspace/glitch-world-model
git checkout main
git pull --ff-only

export LEWM_REPO_ROOT=/workspace/glitch-world-model
export LEWM_DATA_ROOT=/workspace/lewm_data
export LEWM_OUTPUT_ROOT=/workspace/lewm_outputs/r3_seed42

bash cloud/r3_seed42/setup_runtime.sh
bash cloud/r3_seed42/preflight.sh
bash cloud/r3_seed42/run_seed42_full.sh

python scripts/validate_lewm_r3_seed_artifacts.py \
  --artifact-root "$LEWM_OUTPUT_ROOT" \
  --expected-seed 42 \
  --expected-target-updates 15000
```

## Stop Rules

- If `preflight_failed.json` is written, do not launch full training.
- If CUDA OOM occurs, record it and decide whether to use a larger GPU or explicitly approve a
  batch-size change.
- If loss becomes non-finite, stop and classify root cause.
- Do not launch seed 43/44 until seed 42 validates.
- Do not touch locked test.

## Claim Boundary

This plan does not support a scientific performance claim. R3 seed 42 is not passed until the
post-run validator passes on real cloud artifacts.
