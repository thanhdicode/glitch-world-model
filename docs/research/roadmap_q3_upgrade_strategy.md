# Roadmap Q3 Upgrade Strategy

Date: 2026-06-23
Status: canonical strategy companion to `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`

## Objective

Synchronize the repo around a single Q3-safe strategy while Phase B is running:

- Phase A closed with limitations
- Phase B active and not yet claim-ready
- Phase C/D/E prep-only until Phase B intake succeeds

## Current Scientific Interpretation

- `R5-WOB` is completed and validated as a non-locked positive-probe / proof-of-execution bundle.
- `R5-WOB` demonstrates pipeline execution and class-conditional signal presence only.
- `R5-WOB` is not a valid binary benchmark because it has zero evaluation normal-negative episodes.
- `R5-XGame` is the mandatory next gate because it introduces held-out normal negatives and valid
  binary evaluation roles.

## Upgrade Logic

### Phase A

- Freeze evidence inventory.
- Keep the positive-probe limitation explicit.

### Phase B

- Wait for the Kaggle tarball, SHA256 sidecar, and log.
- Accept evidence only after local validation.

### Phase C

- Prepare TempGlitch contract-check/smoke work first.
- Treat VideoGlitchBench as a stretch public-access verification lane.

### Phase D

- Design baselines and ablations.
- Do not report Phase D conclusions before Phase B validation.

### Phase E

- Prepare paper scaffolding only.
- Block final abstract, conclusion, and main claims until metrics exist.

## Reviewer-Defense Angle

The strongest defensible contribution is not "we built the best glitch detector." It is:

`we built a leakage-aware empirical evaluation path for latent-surprise methods and are advancing
from proof-of-execution to proof-of-discrimination under explicit claim controls`
