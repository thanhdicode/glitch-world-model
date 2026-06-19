# WOB Controlled Expansion — Evaluation-Readiness Gate

This directory holds the controlled World of Bugs (WOB) expansion entry gate for Ambitious Plan A.

## What this gate is

The WOB seed42 non-locked **evaluation-readiness gate** is a **local CPU metadata-freeze**. It
does **not** require a GPU, a Kaggle run, or the downloaded artifact tarball. All inputs are
already tracked in the repository:

- `configs/wob_protocol/split.csv` — the frozen protocol split
  (48 train-normal, 12 validation-normal, 60 validation-buggy, 59 locked/test rows).
- The two recorded, verified upstream artifact hashes (WOB-P0 Kaggle audit; WOB-P1 seed42
  training artifact).

The gate freezes, before any evaluation runs:

- `configs/wob_protocol/wob_expansion_eval_manifest.csv` — the 72 non-locked validation rows
  (12 `calibration_normal` + 60 `evaluation_buggy`), each tagged with its `evaluation_role`. The
  59 `split=test` locked rows and the 48 train rows are excluded.
- `configs/wob_protocol/wob_expansion_readiness.json` — the freeze record: eval-manifest path and
  SHA256, role split, recorded artifact hashes, the seed42 selected-checkpoint expectations, the
  frozen R5-WOB reporting paths, and the frozen claim boundary plus forbidden-claims list. All
  leakage flags are hard-set false (`validation_buggy_used_for_fit_select`,
  `locked_test_materialized`, `locked_test_scored`, `evaluation_run`).

Locked status is decided **only** by `split == "test"`. The buggy validation rows carry upstream
`source` paths under `TEST/`; this directory naming is never treated as locked.

## How to run (local, default)

```bash
python scripts/prepare_wob_expansion_readiness.py
python scripts/validate_wob_expansion_readiness.py   # prints wob_expansion_readiness_passed
```

Or run the wrapper:

```bash
bash cloud/wob_expansion/run_kaggle_wob_expansion_readiness.sh
```

## Forbidden claims at this gate

This gate supports **no** WOB result claim. Until the R5-WOB evaluation artifacts exist, do not
claim:

- WOB detection performance (AUROC/AUPRC/F1);
- cross-game generalization (needs R5-XGAME);
- action-conditioning benefit (needs the WOB real-action vs zero-action ablation);
- SIGReg benefit (needs the R6 SIGReg ablation);
- any locked-test result, materialization, or scoring.

## Next stage (not part of this gate)

WOB seed43/44 real-action train-normal-only training on Kaggle GPU (human-run, after a separate
GPU-budget confirmation), then the R5-WOB non-locked identical-episode evaluation on the frozen
manifest. The locked test remains closed.
