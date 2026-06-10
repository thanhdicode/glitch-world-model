# Experiment Release Gates

## Validation Gate

- Record dataset revision, grouping, fitting split, seed, config, and metrics.
- Confirm zero cross-split groups.
- Freeze one selected configuration using validation evidence only.
- Save the decision and allowed claim scope.

## Locked-Test Gate

Locked test remains untouched until the validation gate is complete and the user explicitly
authorizes release. Score exactly the frozen configuration once. Any post-test tuning invalidates
the locked-test framing and must be disclosed.

## Release Gate

- Required artifacts and docs exist.
- Claim registry is valid.
- No prohibited tracked files exist.
- Tests, Ruff, formatting, and release validation pass.
- Limitations and negative results are documented.
