# ADR-003: LeWM Integration Strategy

## Status

Superseded by `ADR-004-mandatory-lewm-main-method.md`.

## Decision

This was the original staged decision. It is retained for history only. The current strategy
makes a verified real LeWM integration mandatory before the paper may use LeWM-based claims.

## Context

The current `lewm_latent.py` file is intentionally guarded and does not load a real LeWorldModel checkpoint. The scorer registry already reserves the name `lewm_latent`, so integration can happen later without changing the pipeline shape.

## Reason

This staged approach reduces risk:

- avoids premature coupling to `external/le-wm`
- keeps current tests and CLI interfaces stable
- gives baselines a clear role before expensive model work
- allows dataset and benchmark strategy to mature first

## Consequences

- Do not implement real LeWM scoring in documentation/scaffolding tasks.
- Future LeWM work must write the same `scores.csv` schema.
- Any checkpoint or model data must stay out of git.
- LeWM results should be compared against `frame_diff`, `feature_distance`, and `mini_latent`.
