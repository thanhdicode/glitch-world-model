# Evaluation Protocol

## VERIFIED

R5-WOB keeps `validation_buggy_used_for_fit_select=false` and keeps the locked test unmaterialized and unscored.

## Required Roles

- `train_normal`: normal-only fitting data.
- `calibration_normal`: normal data used only to set a frozen threshold.
- `evaluation_normal_negative`: held-out normal negatives for final binary evaluation.
- `evaluation_buggy_positive`: held-out buggy positives for final binary evaluation.
- `locked_test`: excluded unless separately authorized by a direct user command.

## BLOCKED

R5-WOB has calibration-normal and buggy-positive episodes but no `evaluation_normal_negative` role. Calibration rows cannot be silently reused as evaluation negatives.

## PLANNED

R5-XGame requires source/pair/episode-disjoint roles, both evaluation classes, a threshold selected only from calibration-normal episodes, and episode-level AUROC, AUPRC, F1, precision, recall, FPR@95TPR, balanced accuracy where applicable, category breakdowns, and bootstrap intervals.
