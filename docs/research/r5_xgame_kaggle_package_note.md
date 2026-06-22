# R5-XGame Kaggle Package Note

## READY

The package specification is ready: include repository source, `configs/wob_protocol/r5_xgame_split.csv`, split validator, leakage audit, and dry-run readiness command. Exclude `attached_assets`, outputs, caches, checkpoints, and all locked/test data.

## NOT READY FOR LIVE EXECUTION

No Kaggle package may launch yet because the real R5-XGame training/scoring implementation and fresh 36-row training artifacts do not exist. The dry-run deliberately reports `SAFE_TO_RUN_KAGGLE=false`.

## Future Package Commands

```powershell
python scripts/audit_r5_xgame_split.py --manifest configs/wob_protocol/r5_xgame_split.csv --output outputs/r5_xgame_leakage_audit.json
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --dry-run
```
