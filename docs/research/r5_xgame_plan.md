# R5-XGame Plan

Date: 2026-06-23

## Purpose

Convert the project from positive-probe evidence into valid non-locked binary-discrimination
evidence without opening locked test.

## Frozen Protocol

- `train_normal`: 36
- `calibration_normal`: 12
- `evaluation_normal_negative`: 12
- `evaluation_buggy_positive`: 60

## Verified Preparation

- The split is frozen and leakage-audited.
- The staged runner exists and trains fresh seed42/43/44 artifacts on the frozen 36-row training
  partition.
- Threshold calibration is limited to the 12 calibration-normal rows.
- The Kaggle launcher and output-bundle validator exist.

## Active Status

Phase B / `R5-XGame` is now an intake-validated non-locked binary evidence family.

- The required Kaggle execution already completed before this documentation sync.
- The downloaded live output directory and final K-B tarball/sidecar now pass local intake
  validation.
- The repair was packaging-only and did not relaunch Kaggle or retrain LeWM.

## Current Validated Summary

- Validator statuses: `r5_xgame_output_validated` and `r5_xgame_tarball_validated`
- Repaired tarball SHA256:
  `e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`
- Best recorded configuration:
  seed44 `lewm_mse_max` with `top2_mean`
- Best recorded metrics:
  AUROC `0.909722`, AUPRC `0.981384`, F1 `0.792079`, precision `0.975610`, recall `0.666667`,
  balanced accuracy `0.791667`
- Limitation:
  12 normal-negative episodes versus 60 buggy-positive episodes, non-locked validation only, not a
  generalization proof.

## Required Metrics After Intake

- AUROC
- AUPRC
- F1
- precision
- recall
- balanced accuracy
- FPR@95TPR
- bootstrap confidence intervals
- per-seed reporting
- category breakdowns where available

## Blocked Claims

Even after intake passes, do not claim:

- `R5-XGame` performance
- cross-game generalization
- superiority
- action-conditioning benefit
- SIGReg benefit
- temporal localization
- locked-test performance
