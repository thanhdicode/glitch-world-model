# NEXT_ACTION.md

Last updated: 2026-06-23T16:06:28+00:00
Commit: `6993964547348659cb2f8882f0a84347f765e200`

## Current Priority
`R5-XGame` package intake reconciliation and the bounded `R6` documentation pass are complete.
The next gate is a bounded TempGlitch follow-up protocol decision that preserves the current
non-locked claim boundary and does not launch new training or open locked test.

## Next Gate
1. Freeze a bounded TempGlitch follow-up protocol that improves evidence quality without touching
   locked test.
2. Decide whether the next external benchmark lane should be TempGlitch follow-up,
   VideoGlitchBench access, or WOB/XGame expansion.
3. Keep every proposed comparison bounded to validated non-locked evidence and preserve the
   repaired `R5-XGame` tarball intake contract.
4. Carry forward the documented `R5-XGame` limitations: positive-heavy split, only 12
   normal-negative evaluation episodes, and no broad generalization claim.

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
- Keep the next protocol memo explicit about the 12 normal-negative / 60 buggy-positive
  `R5-XGame` evaluation scope.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family, `R5-XGame` intake is reconciled, and the
bounded `R6` analysis docs are complete. The remaining blocker is scientific scope:
`R5-XGame` still rests on a positive-heavy non-locked split with only 12 normal-negative
evaluation episodes, while `R5-WOB` remains positive-probe only. Without new, separately
validated evidence, cross-game generalization, final paper-grade benchmark claims, WOB binary
benchmark claims, and locked-test claims remain blocked. Locked test stays closed.
