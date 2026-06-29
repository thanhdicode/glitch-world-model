# R5-XGame Kaggle Package Note

## PACKAGE EXECUTED AND VALIDATED FOR K-B INTAKE

The staged live package now exists: include repository source, `configs/wob_protocol/r5_xgame_split.csv`, split validator, leakage audit, `scripts/run_r5_xgame_staged.py`, `scripts/validate_r5_xgame_output_bundle.py`, and `cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh`. Exclude `attached_assets`, outputs, caches, checkpoints, and all locked/test data.

## CURRENT VALIDATED STATE

The R5-XGame Kaggle computation already completed before this documentation sync. The downloaded
bundle initially failed tarball intake because `stage_package.json` was written after the archive
snapshot. The final user-downloaded K-B bundle now contains the required stage marker, the live
output directory validates as `r5_xgame_output_validated`, and the tarball/sidecar validates as
`r5_xgame_tarball_validated`.

Final K-B tarball SHA256:
`e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`

This was a packaging/intake fix only. No new Kaggle run or LeWM retraining was launched.

## Package Commands

```powershell
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --input-root /kaggle/input --output-dir /kaggle/working/r5_xgame --stage all
python scripts/validate_r5_xgame_output_bundle.py --tarball <download-dir>\r5_xgame_outputs.tar.gz --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256
```
