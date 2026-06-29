# Phase B Run Preparation Report

Date: 2026-06-23

## Current State

- Branch/commit at sync: `main` / `d94655f`.
- Real `R5-XGame` scoring pipeline: implemented.
- Old `R5-WOB` checkpoints: blocked from reuse by incompatible training provenance.
- Kaggle package: executed previously; final K-B intake is now validator-backed from the
  user-downloaded bundle.
- Scientific evidence: now supported by a locally validated downloaded bundle.

## Verified Preparation

- Manifest roles: 36 train-normal, 12 calibration-normal, 12 normal negatives, 60 buggy positives.
- Leakage audit: zero episode/pair/source conflicts and no test rows.
- Output contract and validator exist.
- Final K-B tarball SHA256 is
  `e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`.

## Allowed Statement

The leakage-audited `R5-XGame` split, staged runner, Kaggle package, and local validator produced
a validated non-locked bundle after final local K-B intake.

## Forbidden Statement

Do not convert the packaging repair or the best validated row into any broad `R5-XGame`
generalization, superiority, action-conditioning, SIGReg, temporal-localization, or locked-test
claim.
