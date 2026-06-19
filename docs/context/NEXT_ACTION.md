# NEXT_ACTION.md

Last updated: 2026-06-19T15:35:03+00:00
Commit: `ba024d8b1fd41f7782b644d3461bce260984083a`

## Current Priority
Use the frozen WOB evaluation-readiness path under Ambitious Plan A. The seed42 non-locked WOB
evaluation-readiness gate is frozen, and seed42/seed43/seed44 local artifact verification is now
complete. Keep the locked test closed throughout.

## Sequenced Steps
1. Preserve the frozen seed42 non-locked WOB evaluation manifest and reporting path unchanged.
2. Keep seed42/seed43/seed44 training-artifact hashes bound to the current claim scope.
3. Wait for a separate explicit human command before opening the non-locked `R5-WOB` evaluation.

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
- Keep the seed42 non-locked WOB evaluation manifest, reporting paths, and claim boundary frozen
  before any evaluation execution.
- Do not run WOB evaluation yet; require a separate explicit human command before opening
  non-locked `R5-WOB`.
- Keep locked-test materialization/scoring false.
- Make no WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until the
  corresponding evaluation or ablation artifacts exist.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family and the WOB evaluation-readiness gate is
frozen. Local `WOB-P0` remains blocked because the attached root is incomplete, while the
Kaggle-native `WOB-P0` bundle and the WOB-P1 seed42/seed43/seed44 training artifacts are
validator-backed. The next empirical step is the frozen non-locked `R5-WOB` path, but it remains
closed until explicitly authorized and still does not justify opening the locked test.
