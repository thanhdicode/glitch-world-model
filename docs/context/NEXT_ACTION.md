# NEXT_ACTION.md

Last updated: 2026-06-17T14:03:13+00:00
Commit: `ab179b49f503823e7f3dc05264cbeb7026200ffa`

## Current Priority
Prepare Roadmap v3 Stage R5: identical-episode non-locked evaluation. Do not execute it until
explicitly instructed.

## Success Criteria
- Preserve the Gate 7-9 pilot and the new 36/14/22 research source fingerprints.
- Use the artifact-backed R4 rerun seed43/44 checkpoints and the frozen non-locked protocol as the
  starting point for R5 planning.
- Freeze the exact evaluation inputs, commands, and provenance expectations before any R5 run.
- Identify the baseline and evaluation scripts needed for identical-episode comparison.
- Keep R5 evaluation non-locked and validation-only until a later frozen decision says otherwise.
- Keep locked-test materialization/scoring false.

## Current Known Blocker
R4 rerun seed43/44 are now artifact-backed, but R5 identical-episode evaluation has not yet been
executed and no episode-level LeWM detection metrics exist. The exact non-locked evaluation
manifest, score outputs, and reporting flow must be frozen before any R5 run. This does not
justify opening locked test.
