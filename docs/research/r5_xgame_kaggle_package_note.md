# R5-XGame Kaggle Package Note

## PACKAGE EXECUTED AND REPAIRED FOR INTAKE

The staged live package now exists: include repository source, `configs/wob_protocol/r5_xgame_split.csv`, split validator, leakage audit, `scripts/run_r5_xgame_staged.py`, `scripts/validate_r5_xgame_output_bundle.py`, and `cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh`. Exclude `attached_assets`, outputs, caches, checkpoints, and all locked/test data.

## CURRENT VALIDATED STATE

The R5-XGame Kaggle computation already completed before this documentation sync. The downloaded
bundle initially failed tarball intake because `stage_package.json` was written after the archive
snapshot. Packaging was repaired so the tarball now contains the required stage marker, the live
output directory validates as `r5_xgame_output_validated`, and the repaired tarball/sidecar
validates as `r5_xgame_tarball_validated`.

Repaired tarball SHA256:
`65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`

This was a packaging/intake fix only. No new Kaggle run or LeWM retraining was launched.

## Package Commands

```powershell
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --input-root /kaggle/input --output-dir /kaggle/working/r5_xgame --stage all
python scripts/validate_r5_xgame_output_bundle.py --tarball <download-dir>\r5_xgame_outputs.tar.gz --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256
```
