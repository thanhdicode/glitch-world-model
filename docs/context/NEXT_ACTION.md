# NEXT_ACTION.md

Last updated: 2026-06-20T10:26:26+00:00
Commit: `30c4ffbbd800c4e6858512c305bcd1b4175960c1`

## Current Priority
Use the frozen WOB evaluation-readiness path under Ambitious Plan A. The seed42 non-locked WOB
evaluation-readiness gate is frozen, seed42/seed43/seed44 local artifact verification is
complete, and the repository-side `R5-WOB` pipeline is now prepared. Keep the locked test closed
throughout.

## Sequenced Steps
1. Preserve the frozen seed42 non-locked WOB evaluation manifest and reporting path unchanged.
2. Keep seed42/seed43/seed44 training-artifact hashes bound to the current claim scope.
3. Run the prepared Kaggle `R5-WOB` path rather than attempting invalid local replay.

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
  during evaluation execution.
- Use Kaggle-mounted official WOB inputs for real `R5-WOB` execution because the current local
  machine lacks the full raw tar coverage required for a valid run.
- Keep locked-test materialization/scoring false.
- Make no WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until the
  corresponding evaluation or ablation artifacts exist.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family and the WOB evaluation-readiness gate is
frozen. The Kaggle-native `WOB-P0` bundle and the WOB-P1 seed42/seed43/seed44 training artifacts
are validator-backed, and the `R5-WOB` runner/validator bundle is prepared. The current blocker is
environmental: the local workstation still lacks the full raw WOB tar coverage required for a
valid real run, so execution must move to Kaggle and still does not justify opening the locked
test.
