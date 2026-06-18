# NEXT_ACTION.md

Last updated: 2026-06-18T08:12:56+00:00
Commit: `5b05ea7768df7e7117ec38ba69d16b3fca3e5a8c`

## Current Priority
Run the seed42-only `WOB-P1` non-locked evaluation-readiness gate while keeping WOB evaluation,
seed43/44, and locked test closed.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Preserve the verified WOB-P1 seed42 training artifact hash
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
- Freeze a seed42 non-locked WOB evaluation manifest, reporting path, and claim boundary before
  any evaluation execution.
- Keep WOB evaluation closed and do not run seed43/44 yet.
- Keep locked-test materialization/scoring false.
- Keep World of Bugs as a controlled post-R5 expansion track and do not open it early.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family. Local `WOB-P0` remains blocked because the
attached root is incomplete, the Kaggle-native `WOB-P0` bundle is verified, and the WOB-P1 seed42
training artifact is validator-passed. The correct next step is seed42 WOB evaluation readiness;
this still does not justify opening locked test, seed43/44, or WOB evaluation.
