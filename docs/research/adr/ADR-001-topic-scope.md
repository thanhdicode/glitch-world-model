# ADR-001: Topic Scope

## Status

Accepted

## Decision

Choose video game glitch/bug detection as the main paper direction.

## Context

The repository already contains a baseline pipeline for gameplay clips and glitch labels. The research hypothesis is naturally temporal: abnormal game behavior can be expressed as unexpected state transitions rather than only unusual still images.

## Reason

This direction is the strongest fit with:

- LeWorldModel and JEPA-style latent prediction
- temporal gameplay dynamics
- automated game testing and QA
- feasible demos using synthetic and public data
- the existing MVP pipeline

## Consequences

- The project should prioritize glitch/bug datasets and gameplay video benchmarks.
- Static image benchmarks remain useful but should not define the core claim.
- Future model work should preserve the current clip scoring interface.
