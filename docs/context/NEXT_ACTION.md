# NEXT_ACTION.md

Last updated: 2026-06-18T00:52:31+00:00
Commit: `c3082c69cbe16fbebdec9f9280e39a256efc392c`

## Current Priority
Run the Kaggle-native `WOB-P0` audit path in a Kaggle notebook with the official datasets mounted
while keeping WOB training/evaluation and locked test closed.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating Kaggle-native
  `WOB-P0` as the intended next execution surface.
- Run the Kaggle-native sequence:
  `bash cloud/wob_kaggle_native/setup_runtime.sh`,
  `bash cloud/wob_kaggle_native/preflight.sh`,
  `bash cloud/wob_kaggle_native/prepare_wob_root.sh`,
  `bash cloud/wob_kaggle_native/run_wob_p0_audit.sh`.
- Keep any WOB work at audit/preparation scope until a separate explicit execution command is
  given for training.
- Keep locked-test materialization/scoring false.
- Keep World of Bugs as a controlled post-R5 expansion track and do not open it early.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family. Local `WOB-P0` remains blocked because the
attached root is incomplete, but this does not justify a local 63 GiB acquisition. The correct
next step is the Kaggle-native `WOB-P0` audit; this still does not justify opening locked test or
starting `WOB-P1`.
