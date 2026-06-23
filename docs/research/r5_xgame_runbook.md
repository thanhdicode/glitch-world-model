# R5-XGame Runbook

Date: 2026-06-23

## Status

Phase B / `R5-XGame` is the active scientific gate. Treat the Kaggle run as an external operation
that is not evidence until local intake validation succeeds.

## Preflight Reference Commands

```powershell
python scripts/freeze_r5_xgame_split.py
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --input-root /kaggle/input --output-dir /kaggle/working/r5_xgame --dry-run
```

These are metadata/readiness commands only. They do not create claim-ready metrics.

## Required Inputs

- Kaggle-mounted WOB normal/test source archives resolving every frozen non-locked row
- no old `R5-WOB` seed artifacts or checkpoints
- no locked-test rows

## Required Download Set

- `r5_xgame_outputs.tar.gz`
- `r5_xgame_outputs.tar.gz.sha256`
- `r5_xgame_staged.log`

## Intake Rule

Do not summarize or claim `R5-XGame` metrics until:

1. the three files above are downloaded; and
2. `scripts/validate_r5_xgame_output_bundle.py` passes locally.

## Safety

- Never mount, materialize, or score the 59 WOB `test` rows.
- Never reuse old `R5-WOB` training artifacts for `R5-XGame`.
- Treat remote status, notebook completion, or partial logs as operational signals only, not
  scientific evidence.
