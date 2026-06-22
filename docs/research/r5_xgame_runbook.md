# R5-XGame Runbook

## Preflight

```powershell
python scripts/freeze_r5_xgame_split.py
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --input-root /kaggle/input --output-dir /kaggle/working/r5_xgame --dry-run
```

These commands validate metadata only. They do not materialize data, score episodes, or open locked test.

## Current Readiness

The local dry run reports `SAFE_TO_RUN_KAGGLE=false` when Kaggle WOB tar archives are absent. The staged Kaggle runner is implemented but unexecuted; launch only from a Kaggle notebook with the required WOB normal/test datasets mounted.

## Required Inputs

- Kaggle-mounted WOB normal/test source archives resolving every frozen non-locked row.
- No old R5-WOB seed artifacts or checkpoints.

## Output Contract

The live package emits the filenames listed by `scripts/run_r5_xgame_staged.py`, stage markers, `r5_xgame_outputs.tar.gz`, and `r5_xgame_outputs.tar.gz.sha256`. Validate the downloaded bundle before any claim update.

## Safety

Never mount, materialize, or score the 59 WOB `test` rows. Do not claim R5-XGame performance until the Kaggle output bundle passes local intake validation.
