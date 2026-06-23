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

Phase B / `R5-XGame` is the active mandatory scientific gate.

- The external Kaggle execution is treated as in progress.
- No metric is scientific evidence until the tarball, SHA256 sidecar, and log are downloaded and
  validated locally.

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

Until intake passes, do not claim:

- `R5-XGame` performance
- cross-game generalization
- superiority
- action-conditioning benefit
- SIGReg benefit
- temporal localization
- locked-test performance
