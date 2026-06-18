# NEXT_ACTION.md

Last updated: 2026-06-18T02:50:59+00:00
Commit: `8ab7e7879e2283ac57739d681a4244d477adfdd4`

## Current Priority
Prepare or run the seed42-only `WOB-P1` Kaggle training runner with the official datasets mounted
while keeping WOB evaluation and locked test closed.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Run `bash cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh` from a clean repository clone in
  Kaggle for seed42 only.
- Keep WOB evaluation closed and do not run seed43/44 yet.
- Keep locked-test materialization/scoring false.
- Keep World of Bugs as a controlled post-R5 expansion track and do not open it early.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family. Local `WOB-P0` remains blocked because the
attached root is incomplete, but the Kaggle-native `WOB-P0` bundle is now verified. The correct
next step is the seed42-only runner
`cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh`; this still does not justify opening locked
test, seed43/44, or WOB evaluation.
