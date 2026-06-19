# NEXT_ACTION.md

Last updated: 2026-06-19T06:38:44+00:00
Commit: `6015659212973c8b7248a497ae332a505b5b1be2`

## Current Priority
Use the prepared WOB seed43/44 robust Kaggle training runners under Ambitious Plan A. The seed42
non-locked WOB evaluation-readiness gate is frozen, seed43 local artifact verification is now
complete, and the next execution step is the human Kaggle seed44 run. Keep the locked test closed
throughout.

## Sequenced Steps
1. Run the human Kaggle seed44 robust training cell on the exact pushed commit SHA.
2. Download and locally verify the uploaded seed44 artifact bundle plus `.sha256` sidecar.
3. Run the R5-WOB non-locked identical-episode evaluation on the frozen manifest.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Preserve the verified WOB-P1 seed42 training artifact hash
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
- Preserve the verified WOB-P1 seed43 training artifact hash
  `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88`.
- Keep the seed42 non-locked WOB evaluation manifest, reporting paths, and claim boundary frozen
  before any evaluation execution.
- Use the prepared seed43/44 robust Kaggle runners without modifying the frozen WOB protocol.
- Do not run WOB evaluation yet.
- Keep locked-test materialization/scoring false.
- Make no WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until the
  corresponding evaluation or ablation artifacts exist.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family and the WOB evaluation-readiness gate is
frozen. Local `WOB-P0` remains blocked because the attached root is incomplete, while the
Kaggle-native `WOB-P0` bundle, the WOB-P1 seed42/seed43 training artifacts, and the seed44 runner
are validator-backed. The next experimental step needs human Kaggle GPU execution for seed44; it
still does not justify opening the locked test or running WOB evaluation before its inputs are
ready.
