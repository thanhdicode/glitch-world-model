# R5-XGame Scoring Implementation Note

## VERIFIED

The existing R5-WOB staged machinery provides useful patterns for stage markers, memory-safe Lance materialization, baseline scoring, LeWM scoring, aggregation, package validation, and output hashing.

## BLOCKED

There is no real R5-XGame scoring runner yet. Adapting R5-WOB safely requires a new runner that consumes all four roles, retrains seed42/43/44 on only the frozen 36 train-normal rows, calibrates only from the 12 calibration-normal rows, and evaluates only the 12/60 held-out binary set. The current R5-WOB runner cannot be relabeled because its training/checkpoint provenance is incompatible.

## REQUIRED IMPLEMENTATION

Implement staged `preflight`, normal-only training for each seed, materialization, baseline scoring, LeWM scoring, binary episode aggregation, validation, and packaging. Each stage must preserve false locked-test flags and record the frozen manifest/config/checkpoint hashes.
