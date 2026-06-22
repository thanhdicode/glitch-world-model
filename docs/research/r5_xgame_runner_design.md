# R5-XGame Runner Design

## Reused Engineering

The implementation will adapt R5-WOB stage-marker hashing, streaming Lance materialization,
metadata-only window-manifest construction, train-normal-fitted baselines, SHA256 provenance, and
failure-package conventions. `LeWMTrainConfig` and `train_lewm` provide a real fresh-training API.

## Required Changes

- Materialize four disjoint roles: 36 `train_normal`, 12 `calibration_normal`, 12
  `evaluation_normal_negative`, and 60 `evaluation_buggy_positive`.
- Train seed42/43/44 from scratch on only the frozen train role. Reject every old R5-WOB artifact
  path and record new training hashes.
- Fit each threshold solely on calibration-normal episode scores, then evaluate only the 72 held-out
  binary episodes.
- Produce binary metrics, per-seed/category rows, episode bootstrap intervals, stage markers,
  provenance, and a hash-verified package.

## Forbidden Reuse

Old R5-WOB checkpoints, its positive-only evaluation assumption, its 72-row calibration/buggy
manifest, all test rows, and any validation-buggy fitting are forbidden. No current script may be
called a live scorer until this separate four-role orchestration and validator exist.
