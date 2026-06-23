# Phase B Live Scorer Implementation Report

Date: 2026-06-23

## Summary

- Real staged `R5-XGame` orchestration is implemented in `scripts/run_r5_xgame_staged.py`.
- Fresh seed42/43/44 training is wired through the real `LeWMTrainConfig` / `train_lewm` path with
  the frozen 36-row `train_normal` partition.
- Threshold calibration is restricted to the 12 `calibration_normal` rows.
- Old `R5-WOB` checkpoint or seed-artifact mounts are rejected.
- The Kaggle launcher and local output validator are present.

## Operational State

- Phase B compute has already completed.
- The repaired downloaded bundle now passes local validation for both the live output directory and
  the tarball/sidecar pair.
- The packaging repair only made the downloaded tarball intake-valid; it did not relaunch Kaggle
  or retrain LeWM.

## Claim Boundary

Allowed now:

- code/package readiness for a non-locked `R5-XGame` binary-discrimination run
- bounded reporting from the validated non-locked bundle

Still forbidden:

- broad `R5-XGame` performance claims outside the frozen non-locked split
- superiority or state-of-the-art claims
- cross-game generalization claims
- action-conditioning or SIGReg benefit claims
- temporal-localization claims
- locked-test claims
