# ADR-002: Dataset Strategy

## Status

Accepted

## Decision

Use public benchmarks as the primary evidence. Use synthetic or custom data only as sanity checks, controlled case studies, or external validation.

## Context

The repo already includes synthetic and dynamics scripts. These are useful for development, but they are not enough for publishable claims. Public benchmarks provide stronger evidence and make results easier to compare.

## Reason

Public benchmark first:

- reduces overclaiming
- improves reproducibility
- supports comparison with existing work
- avoids confusing toy success with real gameplay robustness

Synthetic/custom data still matters for:

- testing pipeline behavior
- controlled temporal glitches
- demos
- debugging model failure modes

## Consequences

- Reports must label synthetic results clearly.
- Dataset downloads remain out of git.
- Dataset access, licenses, splits, and temporal labels must be documented before benchmark claims.
