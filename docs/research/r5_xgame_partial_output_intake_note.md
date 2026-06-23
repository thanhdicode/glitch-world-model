# R5-XGame Partial Output Intake Note

## Intake Summary

The downloaded partial `r5_xgame/` output is sufficient to prove that the Kaggle run progressed
through training and stopped during `lewm_score`, not during `materialize`, `baseline_score`, or
`train_lewm`.

Verified from the local partial bundle and staged log:

- `stage_preflight.json` exists and completed.
- `r5_xgame_leakage_audit.json` exists and passed.
- `stage_materialize.json` exists and completed.
- `stage_baseline_score.json` exists and completed.
- `stage_train_lewm.json` exists and completed with seed42, seed43, and seed44 artifacts present.
- `r5_xgame_window_manifest.csv` has `362,695` data rows.
- `r5_xgame_lewm_scores_seed42.csv` has `362,695` data rows.
- `r5_xgame_lewm_scores_seed43.csv` has `362,695` data rows.
- `r5_xgame_lewm_scores_seed44.csv` is missing.
- `stage_lewm_score.json` is missing.
- Downstream stage markers and packaged outputs are missing.

## Diagnosis

The run reached `=== R5-XGame stage: lewm_score ===` and then stopped without a Python traceback.
This matches a quota or wall-time interruption during window scoring. The checkpoint training work
is already complete, and seed42/seed43 score CSVs are already complete against the frozen
`362,695`-row window manifest.

## Operational Conclusion

The next safe step is a resume/finalize run that:

1. Reuses the existing partial `r5_xgame/` output.
2. Verifies seed42 and seed43 score files still match the frozen manifest.
3. Scores only the missing seed44 CSV.
4. Creates `stage_lewm_score.json`.
5. Runs only downstream finalize stages.

No full rerun is needed unless the mounted partial output fails the new resume validation checks.

## Claim Boundary

This partial bundle is operational evidence only. It does **not** justify any R5-XGame metrics or
performance claim until the completed bundle passes local package validation.
