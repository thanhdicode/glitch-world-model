# NEXT_ACTION.md

Last updated: 2026-06-17T17:44:16+00:00
Commit: `f40b7caece82e196c848947011fc973a04eb33d7`

## Current Priority
Provide the missing non-locked WOB tar inputs and rerun the completed `WOB-P0` audit path while
keeping WOB and locked test closed.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` until the full non-locked WOB tar tree
  is available locally.
- Re-run `python scripts/run_wob_p0_materialization_audit.py --wob-root <full-nonlocked-root> --output-dir outputs/wob_p0_materialization_audit --dry-run --allow-materialization-check --no-locked --write-manifest-preview` after the missing inputs are staged.
- Keep any WOB work at planning/materialization-audit scope until a separate explicit execution
  command is given.
- Keep locked-test materialization/scoring false.
- Keep World of Bugs as a controlled post-R5 expansion track and do not open it early.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family, and `WOB-P0` is complete as an audit, but
the current local attached WOB root is missing 110 of 120 non-locked tar rows expected by the
frozen split metadata. This does not justify opening locked test or starting `WOB-P1`.
