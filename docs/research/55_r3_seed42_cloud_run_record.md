# R3 Seed 42 Cloud Run Record

Date: 2026-06-13

Evidence class: cloud-execution-pending

## Current Status

The cloud provider-agnostic package is ready. No non-Kaggle GPU shell is available in this Codex
session, so R3 seed 42 has not been launched on T4 x2 yet.

## Selected Target

- Requested target: T4 x2
- Minimum runtime guard: compute capability `sm_70+`, VRAM at least 14 GB per detected GPU
- T4 capability: `sm_75`
- Runner mode: single-process LeWM training; no distributed training is claimed.

## Required Preflight

Before full training, the GPU machine must run:

```bash
bash cloud/r3_seed42/setup_runtime.sh
bash cloud/r3_seed42/preflight.sh
```

The preflight must write `preflight_passed.json` and `cloud_runtime_preflight.json`.

## Full Training Gate

Full R3 seed 42 training must not start unless `preflight_passed.json` exists. The required command
is:

```bash
bash cloud/r3_seed42/run_seed42_full.sh
```

## Validation Gate

R3 seed 42 is not passed until:

```bash
python scripts/validate_lewm_r3_seed_artifacts.py \
  --artifact-root "$LEWM_OUTPUT_ROOT" \
  --expected-seed 42 \
  --expected-target-updates 15000
```

passes on the completed artifact root.

## Safety State

- Locked test untouched.
- Seed 43/44 not launched.
- No validation-buggy fit, selection, or early stopping.
- No performance claim.
