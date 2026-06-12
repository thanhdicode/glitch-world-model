# NEXT_ACTION.md

Last updated: 2026-06-12T06:48:03+00:00
Commit: `f22e1be92fed098752069616deb7ed2b26b8fcc1`

## Current Priority
Preserve the Gate 7-9 pilot and broaden non-locked buggy validation coverage before Gate 10.

## Success Criteria
- Preserve the canonical manifest and Gate 7-9 artifact hashes.
- Keep threshold fitting grouped, normal-only, and validation-only.
- Add multiple non-locked buggy episodes before making a broader detection claim.
- Keep locked-test materialization/scoring false.

## Current Known Blocker
The Gate 7-9 pilot has only one non-locked buggy episode. LeWM max aggregation reached finite
window-level AUROC/AUPRC, but the grouped normal-P95 threshold yielded zero recall and F1 for
every LeWM aggregation. This evidence is diagnostic and does not justify opening locked test.
