# NEXT_ACTION.md

Last updated: 2026-06-13T09:45:00+00:00
Commit: `ff372c9ec50edbd517024e92ef058cafadfd4abc`

## Current Priority
Recover/persist R4 artifacts before R5. Do not rerun training unless artifact recovery fails.

## Success Criteria
- Preserve the Gate 7-9 pilot and the new 36/14/22 research source fingerprints.
- Preserve the validated 500-update GPU profile evidence and use it only for engineering resource
  planning.
- Recover the actual `r3_seed43_artifacts.tar.gz`, `r3_seed44_artifacts.tar.gz`, and
  `r4_seed43_44_artifacts_bundle.tar.gz` files from Kaggle output or another immutable handoff.
- Hash-verify recovered archives against the live-log SHA256 values before upgrading R4 to
  artifact-backed status.
- Recover or re-verify `r3_seed42_artifacts.tar.gz` locally before calling seed42 locally
  artifact-backed in current repo state.
- Run only non-locked recovery/validation work until a separate locked-test decision is explicitly
  made.
- Keep locked-test materialization/scoring false.

## Current Known Blocker
R4 seed43/44 have live-log validation summaries, but the actual archives were not found locally in
this audit. R5 episode-level evaluation must wait for artifact recovery or an explicit, documented
decision to rerun training after recovery fails. This does not justify opening locked test.
