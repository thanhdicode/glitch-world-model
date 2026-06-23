# Roadmap Q3 Upgrade Strategy

Date: 2026-06-23
Status: canonical strategy companion to `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`

## Objective

Synchronize the repo around a single Q3-safe strategy after the Phase B intake gate closed:

- Phase A closed with limitations
- Phase B intake-complete with bounded claim-ready wording
- Phase C/D/E remain bounded until additional matched evidence exists

## Current Scientific Interpretation

- `R5-WOB` is completed and validated as a non-locked positive-probe / proof-of-execution bundle.
- `R5-WOB` demonstrates pipeline execution and class-conditional signal presence only.
- `R5-WOB` is not a valid binary benchmark because it has zero evaluation normal-negative episodes.
- `R5-XGame` has now completed as a validated non-locked binary evidence bundle with held-out
  normal negatives and valid binary evaluation roles.
- The repaired `R5-XGame` tarball SHA256 is
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`, and the repair was
  packaging-only rather than a new run.

## Upgrade Logic

### Phase A

- Freeze evidence inventory.
- Keep the positive-probe limitation explicit.

### Phase B

- Preserve the validated tarball/sidecar receipt and the frozen split boundary.
- Do not relaunch training for packaging-only issues.

### Phase C

- Prepare TempGlitch contract-check/smoke work first.
- Treat VideoGlitchBench as a stretch public-access verification lane.

### Phase D

- Design baselines and ablations.
- Do not report broad Phase D conclusions without separately validated downstream evidence.

### Phase E

- Prepare paper scaffolding only.
- Block final abstract, conclusion, and main claims until metrics exist.

## Reviewer-Defense Angle

The strongest defensible contribution is not "we built the best glitch detector." It is:

`we built a leakage-aware empirical evaluation path for latent-surprise methods and advanced from
proof-of-execution to a bounded non-locked proof-of-discrimination under explicit claim controls`
