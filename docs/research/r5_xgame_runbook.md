# R5-XGame Runbook

## Preflight

```powershell
python scripts/freeze_r5_xgame_split.py
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --smoke
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --dry-run
```

These commands validate metadata only. They do not materialize data, score episodes, or open locked test.

## Current Readiness

The dry run reports `SAFE_TO_RUN_KAGGLE=false`. Do not launch Kaggle from the current branch.

## Required Future Inputs

- Kaggle-mounted WOB normal/test source archives resolving every frozen non-locked row.
- Fresh seed42/43/44 checkpoints trained normal-only on the frozen 36-row `train_normal` role.
- A staged scorer implementation that consumes the R5-XGame roles; `run_r5_xgame_staged.py` is currently a validator/smoke wrapper, not a scorer.

## Future Output Contract

The live package must emit the filenames listed by `scripts/run_r5_xgame_staged.py`, stage markers, a success tarball, and a SHA256 sidecar. Validate the downloaded bundle before any claim update.

## Safety

Never mount, materialize, or score the 59 WOB `test` rows. Do not run Kaggle until the scorer package and fresh training artifacts have been reviewed and the user explicitly requests the live run.
