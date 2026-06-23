# R5-XGame Runbook

Date: 2026-06-23

## Status

Phase B / `R5-XGame` compute has completed, and the current downloaded bundle now passes local
intake validation. Treat only locally validated bundles as evidence.

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

## Current Validated Receipt

- Live output directory validator status:
  `r5_xgame_output_validated`
- Tarball/sidecar validator status:
  `r5_xgame_tarball_validated`
- Repaired tarball SHA256:
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`
- Packaging-only repair:
  `stage_package.json` is now snapshotted before tarball sealing; no retraining was launched.
- Intake reconciliation:
  validator checks now treat the checked-in frozen manifest as authoritative by normalized CSV
  content, not raw LF/CRLF bytes. Legacy tarball/hash fields inside older downloaded
  `stage_package.json` files are informational only.

## Intake Rule For Any Future Bundle

Do not summarize or claim `R5-XGame` metrics until:

1. the three files above are downloaded; and
2. `scripts/validate_r5_xgame_output_bundle.py` passes locally.

## Safety

- Never mount, materialize, or score the 59 WOB `test` rows.
- Never reuse old `R5-WOB` training artifacts for `R5-XGame`.
- Treat remote status, notebook completion, partial logs, or packaging-only repairs as operational
  signals only unless a locally validated bundle still supports the cited claim.
