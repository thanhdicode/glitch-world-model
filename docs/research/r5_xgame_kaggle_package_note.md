# R5-XGame Kaggle Package Note

## READY FOR HUMAN KAGGLE OPERATION

The staged live package now exists: include repository source, `configs/wob_protocol/r5_xgame_split.csv`, split validator, leakage audit, `scripts/run_r5_xgame_staged.py`, `scripts/validate_r5_xgame_output_bundle.py`, and `cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh`. Exclude `attached_assets`, outputs, caches, checkpoints, and all locked/test data.

## NOT YET EXECUTED

No R5-XGame Kaggle run has been executed or locally validated yet. The local dry-run is expected to report missing inputs unless Kaggle-style WOB tar roots are mounted. Metrics remain unavailable until a downloaded tarball and SHA256 sidecar pass the output-bundle validator.

## Package Commands

```powershell
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --input-root /kaggle/input --output-dir /kaggle/working/r5_xgame --stage all
python scripts/validate_r5_xgame_output_bundle.py --tarball <download-dir>\r5_xgame_outputs.tar.gz --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256
```
