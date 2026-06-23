# NEXT_ACTION.md

Last updated: 2026-06-23T12:10:27+00:00
Commit: `d94655f2c26d9d3aff5a0122e82f2324a81b48ff`

## Current Priority
R5-XGame package intake is complete. The next gate is `R6 Scientific Evidence Upgrade`, using only
the validated `R5-XGame` bundle and without launching new training or opening locked test.

## R6 Scientific Evidence Upgrade
1. Perform false-positive / false-negative analysis on the frozen R5-XGame episode outputs.
2. Produce a per-category breakdown if the validated labels and metadata support it.
3. Audit the bounded baseline-vs-LeWM comparison and record exact support counts.
4. Prepare scorer, aggregation, and threshold ablation analysis from the validated outputs only.
5. Write a limitation table covering the positive-heavy split and the fact that only 12
   normal-negative evaluation episodes exist.
6. Draft a decision memo for the next external benchmark lane: TempGlitch follow-up versus
   VideoGlitchBench / WOB expansion.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Preserve the verified WOB-P1 seed42 training artifact hash
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
- Preserve the verified WOB-P1 seed43 training artifact hash
  `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88`.
- Preserve the verified WOB-P1 seed44 training artifact hash
  `c5b3178cdb75a0c1f9bcca78eba8beaaf21ffa703917a3f42c476563849fd041`.
- Preserve the repaired R5-XGame tarball SHA256
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`.
- Preserve validator statuses `r5_xgame_output_validated` and `r5_xgame_tarball_validated`.
- Do not relaunch Kaggle or rerun LeWM training unless a required raw artifact is truly missing.
- Keep locked-test materialization/scoring false.
- Make no broad R5-XGame/WOB performance, cross-game, action-conditioning, or SIGReg-benefit
  claim beyond the exact qualified non-locked bundles.
- Keep every R6 output explicit about the 12 normal-negative / 60 buggy-positive evaluation scope.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family, and R5-WOB is validated as positive-probe
evidence only. `R5-XGame` now has a validated bundle, but that evidence remains bounded to a
positive-heavy non-locked split with only 12 normal-negative evaluation episodes. Without new,
separately validated evidence, cross-game generalization, final paper-grade benchmark claims, WOB
binary benchmark claims, and locked-test claims remain blocked. Locked test stays closed.
