# Phase B Run Preparation Report

Date: 2026-06-23

## Current State

- Branch/commit at sync: `main` / `d94655f`.
- Real `R5-XGame` scoring pipeline: implemented.
- Old `R5-WOB` checkpoints: blocked from reuse by incompatible training provenance.
- Kaggle package: executed previously, then repaired at the packaging/intake layer only.
- Scientific evidence: now supported by a locally validated downloaded bundle.

## Verified Preparation

- Manifest roles: 36 train-normal, 12 calibration-normal, 12 normal negatives, 60 buggy positives.
- Leakage audit: zero episode/pair/source conflicts and no test rows.
- Output contract and validator exist.
- Repaired tarball SHA256 is
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`.

## Allowed Statement

The leakage-audited `R5-XGame` split, staged runner, Kaggle package, and local validator produced
a validated non-locked bundle after a packaging-only tarball repair.

## Forbidden Statement

Do not convert the packaging repair or the best validated row into any broad `R5-XGame`
generalization, superiority, action-conditioning, SIGReg, temporal-localization, or locked-test
claim.
