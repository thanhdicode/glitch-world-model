# R5-XGame Resume Plan After Quota

## Decision

Resume from the downloaded partial `r5_xgame/` Kaggle output. Do not restart the full staged run.

## Why Resume Is Safe

- Preflight, leakage audit, materialize, baseline scoring, and all three `train_lewm` seeds are
  already complete.
- The frozen window manifest row count is known and fixed at `362,695`.
- Seed42 and seed43 score CSVs already match that exact manifest row count.
- Seed44 checkpoint artifacts already exist under `_lewm_seed44/`.
- The missing work begins at `lewm_score` for seed44 and continues through downstream finalize.

## Planned Resume Path

Use `cloud/wob_r5_xgame/run_kaggle_r5_xgame_resume_missing_seed44_and_finalize.sh`.

That launcher:

1. Finds a mounted `*/r5_xgame` partial output directory under `/kaggle/input`.
2. Copies it to `/kaggle/working/r5_xgame`.
3. Verifies the required files, stage markers, safe flags, and row counts.
4. Runs `lewm_score` only for seed44.
5. Writes `stage_lewm_score.json`.
6. Runs only `aggregate_episode`, `calibrate_thresholds`, `evaluate_binary`, `bootstrap_ci`,
   `package`, and `validate_package`.

## Explicit Non-Goals

- Do not rerun `materialize`.
- Do not rerun `baseline_score`.
- Do not rerun `train_lewm`.
- Do not change the frozen manifest or role counts.
- Do not open locked test.
- Do not claim metrics before final bundle validation.

## Fallback

No separate all-seed fallback launcher is required at this point because the runner now supports
safe `lewm_score` subset execution for `--seeds 44` while reusing verified seed42/seed43 outputs.
