# R5-WOB Results Analysis

Date: 2026-06-23

## Verified

- Artifact intake status: `VALID_OUTPUT_BUNDLE`.
- The validated extraction and receipt remain outside Git-tracked paths.
- The Kaggle log reports staged completion for preflight, Lance materialization, baseline scoring,
  three LeWM seeds, aggregation, and package validation.
- The frozen manifest contains 48 `train_normal`, 12 `calibration_normal`, and 60
  `evaluation_buggy_positive` episodes, with zero `evaluation_normal_negative` episodes.
- The bundle therefore proves pipeline execution and class-conditional signal presence under a
  normal-calibrated threshold.

## What R5-WOB Means

`R5-WOB` is a positive-probe / proof-of-execution bundle.

It supports:

- execution success
- provenance-bound artifact validation
- signal-presence discussion
- seed-aware qualitative comparison inside the positive-probe setting

It does not support:

- AUROC as a valid binary-benchmark claim
- FPR@95TPR
- binary discrimination
- superiority
- state of the art
- cross-game generalization
- temporal localization
- action-conditioning benefit
- SIGReg benefit

## Safe Claim Boundary

Use this wording when summarizing the result:

`A provenance-bound non-locked positive-probe evaluation demonstrating pipeline execution and
class-conditional signal presence under a normal-calibrated threshold, but not yet a complete
binary benchmark.`
