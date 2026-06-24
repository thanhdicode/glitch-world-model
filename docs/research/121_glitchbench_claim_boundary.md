# 121 - GlitchBench Claim Boundary

Date: 2026-06-24
Status: active

## Allowed Now

- The repo now has a validator-backed local P3 package for a bounded GlitchBench subset.
- The accessed GlitchBench artifact is image-level and is converted locally into repeated-frame
  clips for a train-normal protocol.
- Synthetic normal clips are used explicitly.
- No temporal span labels were observed in the accessed public viewer path.
- K2 remains pending and no GlitchBench metric claim exists yet.

## Allowed After K2 Only If The Downloaded Artifact Validates

- bounded image-level benchmark metrics on the exact K2 split
- method ranking statements qualified to the exact GlitchBench subset and uncertainty intervals
- comparison wording that preserves the synthetic-normal limitation and the image-level limitation

## Forbidden Until A Validated Artifact Says Otherwise

- cross-game generalization
- temporal localization
- broad superiority
- state of the art
- natural normal gameplay evidence
- SIGReg benefit
- action-conditioning benefit
- any locked-test result

## Current Boundary Sentence

Use wording like:

`The local P3 preparation package enables a bounded, leakage-aware GlitchBench subset evaluation,
but the benchmark remains image-level, uses synthetic normal clips, and does not support temporal
localization or broad generalization claims.`
