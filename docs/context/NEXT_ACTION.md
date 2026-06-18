# NEXT_ACTION.md

Last updated: 2026-06-18T01:50:12+00:00
Commit: `7da3f7ba6000cfd5c3d962fbd25f4e7981155d9a`

## Current Priority
Run the one-section Kaggle-native `WOB-P0` notebook entrypoint with the official datasets mounted
while keeping WOB training/evaluation and locked test closed.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating Kaggle-native
  `WOB-P0` as the intended next execution surface.
- Run `bash cloud/wob_kaggle_native/run_kaggle_wob_p0_all.sh` from a clean repository clone in
  Kaggle.
- Keep any WOB work at audit/preparation scope until a separate explicit execution command is
  given for training.
- Keep locked-test materialization/scoring false.
- Keep World of Bugs as a controlled post-R5 expansion track and do not open it early.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family. Local `WOB-P0` remains blocked because the
attached root is incomplete, but this does not justify a local 63 GiB acquisition. The correct
next step is the Kaggle-native `WOB-P0` audit via
`cloud/wob_kaggle_native/run_kaggle_wob_p0_all.sh`; this still does not justify opening locked
test or starting `WOB-P1`.
