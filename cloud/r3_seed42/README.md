# R3 Seed 42 Strong-GPU Runner

This package runs the non-locked R3 seed 42 LeWM training path on a normal Linux GPU VM such as
RunPod, Lambda, Vast, Colab Pro, or a private A100/H100/T4 machine.

Kaggle is intentionally not used for R3 because it assigned unsupported Tesla P100 `sm_60` GPUs
twice in a row. The current PyTorch container requires `sm_70+`.

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
