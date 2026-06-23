# Phase B R5-XGame Execution Report

Date: 2026-06-23

## Status

- Branch/commit at doc sync: `main` / `d94655f`.
- Real manifest frozen: yes, 120 non-locked metadata rows.
- Role counts: train-normal 36, calibration-normal 12, evaluation-normal-negative 12,
  evaluation-buggy-positive 60.
- Leakage audit: passed with zero episode, pair, or source conflicts.
- Runner/validator status: implemented.
- External execution status: compute already completed before this doc sync.
- Scientific evidence status: validated locally for both the live output directory and the repaired
  tarball/sidecar bundle.
- Repaired tarball SHA256:
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`.
- Packaging note: this was a tarball-intake repair only; no retraining or new Kaggle run was
  launched.

## What This Report Allows

- A real, leakage-audited four-role `R5-XGame` protocol exists.
- The repository has a concrete Phase B execution path.
- The validated bundle may be used for bounded non-locked result summaries.

## What This Report Forbids

- Any use of the packaging repair as if it were a new scientific run.
- Any cross-game generalization, superiority, action-conditioning, SIGReg, temporal-localization,
  or locked-test claim.

## Validated Intake Receipt

- Live output directory validator status:
  `r5_xgame_output_validated`
- Tarball/sidecar validator status:
  `r5_xgame_tarball_validated`
- Best recorded bounded result:
  AUROC `0.909722`, AUPRC `0.981384`, F1 `0.792079`, precision `0.975610`, recall `0.666667`,
  balanced accuracy `0.791667`

Recheck command if a downloaded copy must be revalidated:

```powershell
python scripts/validate_r5_xgame_output_bundle.py `
  --tarball <download-dir>\r5_xgame_outputs.tar.gz `
  --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256 `
  --frozen-manifest configs\wob_protocol\r5_xgame_split.csv
```
