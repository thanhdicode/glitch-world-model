# R5-WOB Non-Locked Evaluation Pipeline

Date: 2026-06-19

Status: `BLOCKED_NEEDS_HUMAN_KAGGLE_R5_WOB`

## Scope

This document records the repository-side preparation for the frozen, non-locked `R5-WOB`
identical-episode evaluation path. It does not report empirical WOB results. It does not open
locked test. It does not support any WOB performance claim.

## Verified Inputs

- Frozen readiness metadata: `configs/wob_protocol/wob_expansion_readiness.json`
- Frozen evaluation manifest: `configs/wob_protocol/wob_expansion_eval_manifest.csv`
- Verified WOB-P1 training artifacts:
  - seed42 tarball SHA256 `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`
  - seed43 tarball SHA256 `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88`
  - seed44 tarball SHA256 `c5b3178cdb75a0c1f9bcca78eba8beaaf21ffa703917a3f42c476563849fd041`

## Prepared Repository Surface

- `scripts/run_r5_wob_identical_episode_evaluation.py`
- `scripts/validate_r5_wob_evaluation.py`
- `scripts/run_r5_wob_stage.py`
- `scripts/validate_r5_wob_stage_outputs.py`
- `scripts/assemble_r5_wob_from_stages.py`
- `src/glitch_detection/r5_wob_eval.py`
- `src/glitch_detection/r5_wob_staged.py`
- `cloud/wob_r5_eval/run_kaggle_r5_wob_eval.sh`
- `cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh`
- `cloud/wob_r5_eval/README.md`
- Focused tests for the runner, validator, and Kaggle shell entrypoint

## What The Runner Enforces

- uses the frozen 72-row evaluation manifest only
- keeps all 59 locked rows excluded
- keeps train rows excluded from evaluation scoring
- keeps `validation_buggy_used_for_fit_select = false`
- keeps `locked_test_materialized = false`
- keeps `locked_test_scored = false`
- requires all three verified LeWM seed artifacts plus `frame_diff` and train-normal-fitted
  `feature_distance`
- emits manifest, score, metrics, provenance, and report files only if the real evaluation runs

## Local Dry-Run Result

The local dry-run was executed against the current workstation's attached WOB root plus the
downloaded seed42/seed43/seed44 artifact tarballs. The dry-run completed successfully and verified
all three seed artifacts, but it also confirmed that the local workstation still does not have the
full raw WOB coverage needed for real execution:

- train coverage: `48` required, `5` resolved, `43` missing
- eval coverage: `72` required, `5` resolved, `67` missing

Because the raw WOB tar coverage is incomplete locally, a real `R5-WOB` execution on this machine
would be invalid. The correct next execution surface is Kaggle, where the official mounted WOB
inputs are available.

## Current Status

`R5-WOB` is now prepared at the pipeline level but remains empirically unrun in this repository
state. The accurate status label is:

- `BLOCKED_NEEDS_HUMAN_KAGGLE_R5_WOB`

The repository now also includes a staged retry path for Kaggle runs so the next attempt can
resume from successful phases and retain structured failure diagnostics.

## Exact Next Action

Run the staged Kaggle notebook cell described in `cloud/wob_r5_eval/README.md` on the chosen
retry commit so the official WOB normal/test inputs and the verified seed42/seed43/seed44
training artifacts are all mounted together.

## Claim Boundary

Safe claim:

- the repository provides a reproducible non-locked `R5-WOB` runner/validator bundle and has
  verified that local replay is blocked by incomplete raw WOB coverage

Unsafe claims:

- any WOB AUROC, AUPRC, F1, FPR@95TPR, or qualitative detection-performance statement
- any cross-game comparison
- any action-conditioning benefit statement
- any locked-test statement beyond the required false flags
