# R5-XGame Scoring Implementation Note

## VERIFIED

The existing R5-WOB staged machinery provides useful patterns for stage markers, memory-safe Lance materialization, baseline scoring, LeWM scoring, aggregation, package validation, and output hashing.

## IMPLEMENTED BUT UNRUN

`scripts/run_r5_xgame_staged.py` now consumes all four roles, retrains seed42/43/44 on only the frozen 36 train-normal rows, calibrates only from the 12 calibration-normal rows, and evaluates only the 12/60 held-out binary set. The current R5-WOB runner still cannot be relabeled because its training/checkpoint provenance is incompatible.

## IMPLEMENTATION SURFACE

The staged surface includes `preflight`, `materialize`, `baseline_score`, `train_lewm`, `lewm_score`, `aggregate_episode`, `calibrate_thresholds`, `evaluate_binary`, `bootstrap_ci`, `package`, and `validate_package`. Each stage preserves false locked-test flags and records frozen manifest/config/checkpoint hashes.

No R5-XGame training, scoring, metric, or Kaggle output has been produced yet.
