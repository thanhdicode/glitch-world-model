# 121 - GlitchBench Claim Boundary

Date: 2026-06-25
Status: active

## Allowed Now

- The repo has a validator-backed local K2 input package for a bounded GlitchBench subset.
- The repo has a repaired K2 runner that validates read-only Kaggle input mounts without writing
  into the mounted package root.
- The repo has a scientific full-K2 execution path that requires and uses LeWM seed42/43/44
  artifacts, plus an explicit `--baseline-only` smoke-test mode for engineering checks only.
- The downloaded scientific K2 bundle now validates locally with SHA256-matched tarball intake,
  false locked-test flags, `12` train-normal clips, and `24` validation clips.
- The current executable GlitchBench path remains image-level, synthetic-normal, and
  `temporal_label_available=false`.
- The repo now has a normalized local Kaggle artifact package for LeWM seed42/43/44 inputs under
  `outputs/k2_lewm_seed_artifacts/`.

## Allowed Now That K2 Intake Is Validated

- bounded image-level benchmark metrics on the exact frozen K2 split
- uncertainty-qualified method ranking statements on that exact split
- bounded LeWM-vs-baseline comparison wording tied to the validated K2 artifact

## Required Limitations

- synthetic normal clips are explicit and must be named
- no temporal-localization claim
- no cross-game generalization claim
- no SOTA or broad superiority claim
- no claim may rely on `--baseline-only`; that mode is engineering-only
- K2 must be described as a bounded negative comparison for LeWM on this exact split
- ranking separation and threshold calibration must be discussed separately for the AUROC `1.0`
  non-LeWM rows

## Forbidden Until A Validated Artifact Says Otherwise

- any claim that baseline-only smoke outputs establish LeWM-vs-baseline evidence
- any SIGReg benefit statement
- any action-conditioning benefit statement
- any natural-normal gameplay claim from GlitchBench
- any locked-test result

## Current Boundary Sentence

Use wording like:

`The K2 GlitchBench path in this repo is a bounded image-level synthetic-normal benchmark surface;
the validated scientific bundle shows that the recorded non-LeWM rows rank above the recorded LeWM
rows on this exact split, but the result remains image-level, synthetic-normal, and unsuitable for
temporal-localization, generalization, or broad superiority language.`
