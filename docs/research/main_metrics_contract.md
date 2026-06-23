# R5-XGame Main Metrics Contract

Date: 2026-06-23

## Frozen Semantics

- Unit of analysis: episode, after pre-specified window-to-episode aggregation.
- Threshold: selected only from `calibration_normal` episode scores.
- Evaluation labels: `evaluation_normal_negative=0` and `evaluation_buggy_positive=1`.
- Report metrics only when both evaluation classes are present and the output bundle has passed
  local validation.
- Preserve seeds 42, 43, and 44 in the primary bundle summary; a bounded evidence note may cite
  the best recorded configuration only if it is explicitly labeled as the best observed
  non-locked validation row rather than a stable average.
- Report category breakdowns with support counts where metadata supports them.
- Bootstrap confidence intervals must resample episodes while retaining the frozen threshold and
  a documented deterministic seed.

The current repaired bundle satisfies the local-validation prerequisite with
`r5_xgame_output_validated` and `r5_xgame_tarball_validated`.

## Required Post-Validation Metrics

- AUROC
- AUPRC
- F1
- precision
- recall
- balanced accuracy
- FPR@95TPR

## Forbidden Uses

- Do not backfill `R5-WOB` into this contract.
- Do not report one-class metrics as binary-discrimination evidence.
- Do not summarize `R5-XGame` performance from remote status, partial logs, or unvalidated bundle
  contents.
