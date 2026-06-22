# R5-XGame Leakage Audit

## VERIFIED

`scripts/audit_r5_xgame_split.py` passed against the frozen manifest. The machine-readable audit is written to ignored path `outputs/r5_xgame_leakage_audit.json`.

- Cross-role episode conflicts: 0
- Cross-role pair conflicts: 0
- Cross-role source conflicts: 0
- Locked/test rows: 0
- Buggy train or calibration rows: 0
- Empty required roles: 0
- `locked_test_materialized=false`
- `locked_test_scored=false`
- `validation_buggy_used_for_fit_select=false`

## LIMITATION

Source paths are individual WOB episode archives, not independent game IDs. The audit proves metadata-level source/pair/episode separation, not game-level generalization.
