# NEXT_ACTION.md

Last updated: 2026-06-12T07:25:09+00:00
Commit: `c5e7ca997e6355e002afb1c3356d3789deb3efe0`

## Current Priority
Run the research MVP GPU profile, then freeze a feasible multi-seed training schedule.

## Success Criteria
- Preserve the Gate 7-9 pilot and the new 36/14/22 research source fingerprints.
- Measure throughput and VRAM for 500 updates without treating the profile as performance evidence.
- Freeze normal-only checkpoint selection, three seeds, and episode-level evaluation.
- Keep locked-test materialization/scoring false.

## Current Known Blocker
The broader non-locked source is ready, but GPU throughput, memory, and convergence behavior have
not been measured. The 500-update profile must complete before freezing the main-run batch size,
evaluation interval, and wall-clock budget. This does not justify opening locked test.
