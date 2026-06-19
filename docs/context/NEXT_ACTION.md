# NEXT_ACTION.md

Last updated: 2026-06-19T04:37:58+00:00
Commit: `32717340369d1d5e49f05859e95f0f33bb22f0ba`

## Current Priority
Use the prepared WOB seed43/44 robust Kaggle training runners under Ambitious Plan A. The seed42
non-locked WOB evaluation-readiness gate is frozen, and the next execution step is the human
Kaggle seed43 run, then local artifact verification, then seed44. Keep the locked test closed
throughout.

## Sequenced Steps
1. Run the human Kaggle seed43 robust training cell on the exact pushed commit SHA.
2. Download and locally verify the uploaded seed43 artifact bundle plus `.sha256` sidecar.
3. Run the human Kaggle seed44 robust training cell only after seed43 verifies cleanly.
4. Run the R5-WOB non-locked identical-episode evaluation on the frozen manifest.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Preserve the verified WOB-P1 seed42 training artifact hash
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
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
Kaggle-native `WOB-P0` bundle, the WOB-P1 seed42 training artifact, and the seed43/44 runner
prep are all validator-backed. The next experimental step needs human Kaggle GPU execution for
seed43 first; it still does not justify opening the locked test or running WOB evaluation before
its inputs are ready.
