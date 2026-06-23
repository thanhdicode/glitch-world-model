# Evaluation Protocol

Date: 2026-06-23

## Phase A Meaning

`R5-WOB` is a validated positive-probe protocol only.

- It preserves `validation_buggy_used_for_fit_select=false`.
- It keeps locked test unmaterialized and unscored.
- It does not include `evaluation_normal_negative`.
- Calibration rows must not be silently reused as evaluation negatives.

## Required Roles For Valid Binary Evaluation

- `train_normal`: normal-only fitting data
- `calibration_normal`: normal data used only to set a frozen threshold
- `evaluation_normal_negative`: held-out normal negatives for final binary evaluation
- `evaluation_buggy_positive`: held-out buggy positives for final binary evaluation
- `locked_test`: excluded unless separately authorized by a direct user command

## Phase B Contract

`R5-XGame` is the bounded binary-discrimination evidence family for the current WOB/XGame lane.

It must:

- keep roles source/pair/episode-disjoint;
- keep all `test` / locked rows excluded;
- calibrate thresholds from `calibration_normal` only;
- evaluate only on `evaluation_normal_negative` plus `evaluation_buggy_positive`;
- report episode-level metrics only after output-bundle intake validation succeeds.

The current repaired bundle satisfies the intake requirement with
`r5_xgame_output_validated` and `r5_xgame_tarball_validated`, but the resulting evidence remains
bounded to a non-locked 12-negative / 60-positive split.

## Metrics After Validation

- AUROC
- AUPRC
- F1
- precision
- recall
- balanced accuracy
- FPR@95TPR
- bootstrap confidence intervals
- per-seed reporting
- category breakdowns where supported
