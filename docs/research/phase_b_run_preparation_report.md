# Phase B-RUN Preparation Report

## Current State

- Branch/commit: `main` / `88f4211` at preflight.
- Real R5-XGame scoring: not implemented.
- Old R5-WOB checkpoints: blocked from reuse by incompatible training provenance.
- Kaggle package: specification ready; live package/run not ready.

## Exact Current Command

```powershell
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --dry-run
```

It validates the manifest and reports the expected output contract, but returns `SAFE_TO_RUN_KAGGLE=false` until live requirements exist.

## Validation

- Manifest roles: 36 train-normal, 12 calibration-normal, 12 normal negatives, 60 buggy positives.
- Leakage audit: zero episode/pair/source conflicts; no test rows.
- Targeted protocol and metric tests: passed.

## Claims

- Allowed: the leakage-audited R5-XGame metadata split and fail-closed live-run readiness reporting exist.
- Forbidden: all R5-XGame performance, generalization, superiority, action-conditioning, and locked-test claims.
