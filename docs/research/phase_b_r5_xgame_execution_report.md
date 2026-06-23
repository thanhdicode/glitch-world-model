# Phase B R5-XGame Execution Report

Date: 2026-06-23

## Status

- Branch/commit at doc sync: `main` / `b6e2b90`.
- Real manifest frozen: yes, 120 non-locked metadata rows.
- Role counts: train-normal 36, calibration-normal 12, evaluation-normal-negative 12,
  evaluation-buggy-positive 60.
- Leakage audit: passed with zero episode, pair, or source conflicts.
- Runner/validator status: implemented.
- External execution status: active / running on Kaggle.
- Scientific evidence status: pending local output-bundle validation.

## What This Report Allows

- A real, leakage-audited four-role `R5-XGame` protocol exists.
- The repository has a concrete Phase B execution path.
- The active external run may be tracked as operations status only.

## What This Report Forbids

- Any `R5-XGame` performance claim before intake passes.
- Any cross-game generalization, superiority, action-conditioning, SIGReg, temporal-localization,
  or locked-test claim.

## Exact Next Intake Step

Download:

- `r5_xgame_outputs.tar.gz`
- `r5_xgame_outputs.tar.gz.sha256`
- `r5_xgame_staged.log`

Then run:

```powershell
python scripts/validate_r5_xgame_output_bundle.py `
  --tarball <download-dir>\r5_xgame_outputs.tar.gz `
  --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256 `
  --frozen-manifest configs\wob_protocol\r5_xgame_split.csv
```
