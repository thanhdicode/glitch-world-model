# R5-XGame Resume Missing Seed44 Runbook

## Purpose

Resume a quota-interrupted Kaggle R5-XGame run when the partial output already contains:

- completed preflight, materialize, baseline scoring, and `train_lewm`
- complete seed42 and seed43 score CSVs
- missing seed44 score CSV
- missing downstream finalize outputs

## Required Mounted Input Layout

Attach the downloaded partial output as a Kaggle dataset so that a directory named `r5_xgame`
appears somewhere under `/kaggle/input`.

The leaf directory must contain:

- `stage_preflight.json`
- `stage_materialize.json`
- `stage_baseline_score.json`
- `stage_train_lewm.json`
- `r5_xgame_window_manifest.csv`
- `r5_xgame_baseline_scores.csv`
- `r5_xgame_lewm_scores_seed42.csv`
- `r5_xgame_lewm_scores_seed43.csv`
- `_lewm_seed42/`
- `_lewm_seed43/`
- `_lewm_seed44/`
- `_lewm_seed44/best_weights.pt`
- `_lewm_seed44/config.json`

The resume validator also requires:

- `stage_train_lewm.json` status is `train_lewm_complete`
- `validation_buggy_used_for_fit_select` is `false`
- `locked_test_materialized` is `false`
- `locked_test_scored` is `false`
- seed42 row count matches `r5_xgame_window_manifest.csv`
- seed43 row count matches `r5_xgame_window_manifest.csv`

## Kaggle Cell

```bash
cd /kaggle/working/glitch-world-model
bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_resume_missing_seed44_and_finalize.sh
```

## What The Resume Launcher Does

1. Installs the isolated LeWM runtime and verifies imports before any scoring.
2. Locates the mounted partial `r5_xgame/` directory under `/kaggle/input`.
3. Copies that directory into `/kaggle/working/r5_xgame`.
4. Refuses unsafe partial inputs before scoring starts.
5. Runs `lewm_score` only for seed44.
6. Writes `stage_lewm_score.json` only after all three seed score CSVs validate against the frozen
   window manifest.
7. Runs only downstream finalize stages:
   `aggregate_episode`, `calibrate_thresholds`, `evaluate_binary`, `bootstrap_ci`, `package`,
   `validate_package`.

## Expected Outputs

Download these files after success:

- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz`
- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz.sha256`
- `/kaggle/working/r5_xgame_resume_missing_seed44.log`

## Failure Modes

- Missing mounted `r5_xgame/` directory: attach the partial output dataset correctly.
- Missing `stage_train_lewm.json`: the mounted dataset is not the required partial output.
- Seed42 or seed43 row mismatch: treat the partial bundle as unsafe and do not resume from it.
- Missing `_lewm_seed44/best_weights.pt` or `_lewm_seed44/config.json`: the mounted partial output
  is incomplete for resume.
- Missing `stage_lewm_score.json` after scoring: treat packaging as invalid and stop before claims.

## Claim Boundary

This workflow only completes the frozen validation-only bundle. Do not make R5-XGame metric claims
until the final packaged output passes local intake validation.
