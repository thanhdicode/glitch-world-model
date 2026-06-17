# R3/R4 Strong-GPU Seed Runner

This package runs the non-locked R3/R4 LeWM seed training path on a normal Linux GPU VM such as
RunPod, Lambda, Vast, Colab Pro, or a private A100/H100/T4 machine. The reusable runner defaults
to seed 42 and can also be used for R4 seeds after R3 seed42 has been validated.

Kaggle is intentionally not used for R3 because it assigned unsupported Tesla P100 `sm_60` GPUs
twice in a row. The current PyTorch container requires `sm_70+`; abort if the runtime guard fails.

## Required Environment

Set these paths on the GPU machine:

```bash
export LEWM_REPO_ROOT=/workspace/glitch-world-model
export LEWM_DATA_ROOT=/workspace/lewm_data
export LEWM_OUTPUT_ROOT=/workspace/lewm_outputs/r3_seed42
```

Expected Lance inputs:

```text
$LEWM_DATA_ROOT/tempglitch_train_normal_all_local.lance
$LEWM_DATA_ROOT/tempglitch_validation_normal_all_local.lance
```

No validation-buggy path and no locked-test path are used.

## Run

```bash
cd "$LEWM_REPO_ROOT"
bash cloud/r3_seed42/setup_runtime.sh
bash cloud/r3_seed42/preflight.sh
bash cloud/r3_seed42/run_seed42_full.sh
python scripts/validate_lewm_r3_seed_artifacts.py \
  --artifact-root "$LEWM_OUTPUT_ROOT" \
  --expected-seed 42 \
  --expected-target-updates 15000
```

The full run must only start after `preflight_passed.json` exists.

For the reusable entrypoint, seed 42 is the default:

```bash
bash cloud/r3_seed42/run_seed_full.sh
```

For R4 seed 43 or 44, set `LEWM_SEED` and use a seed-specific output root:

```bash
export LEWM_SEED=43
export LEWM_OUTPUT_ROOT=/workspace/lewm_outputs/r3_seed43
bash cloud/r3_seed42/preflight.sh
bash cloud/r3_seed42/run_seed_full.sh
```

Repeat with `LEWM_SEED=44` only under the frozen protocol and only after seed 42 has passed.
No validation-buggy path and no locked-test path are used.
