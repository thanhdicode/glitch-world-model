# NEXT_ACTION.md

Last updated: 2026-06-13T05:21:01+00:00
Commit: `e3ba66b0ddec63899e883d0aad9ccde2f785d7f7`

## Current Priority
Implement and validate Roadmap v3 Stages R0-R1: the exact 500-update research MVP GPU profile.

## Success Criteria
- Preserve the Gate 7-9 pilot and the new 36/14/22 research source fingerprints.
- Make the profile package idempotent and validate all required metadata, logs, reload state,
  retry evidence, and artifact hashes.
- Measure throughput and VRAM for 500 updates without treating the profile as performance evidence.
- Freeze normal-only checkpoint selection, three seeds, and episode-level evaluation.
- Keep locked-test materialization/scoring false.

## Current Known Blocker
The broader non-locked source is ready, but GPU throughput, memory, and convergence behavior have
not been measured. The exact update-based profile harness and its strict artifacts must pass before
freezing the main-run batch size, evaluation interval, and wall-clock budget. This does not justify
opening locked test.
