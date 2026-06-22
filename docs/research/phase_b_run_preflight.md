# Phase B-RUN Preflight

## VERIFIED

- Branch at preflight: `main`, commit `88f4211`.
- The frozen manifest validates with 36 train-normal, 12 calibration-normal, 12 evaluation-normal-negative, and 60 evaluation-buggy-positive rows.
- Leakage audit reports zero cross-role episode, pair, and source conflicts; no test or locked-test row is present.
- R5-XGame binary metric tests pass and reject one-class evaluation.

## IMPLEMENTATION STATUS

`scripts/run_r5_xgame_staged.py` is a metadata validator and dry-run readiness reporter only. It does not materialize Lance data, train seeds, score windows, aggregate episodes, bootstrap intervals, package artifacts, or invoke Kaggle.

## SAFETY

Old R5-WOB checkpoints are blocked from reuse because their old 48-row training pool includes the 12 frozen R5-XGame normal negatives.
