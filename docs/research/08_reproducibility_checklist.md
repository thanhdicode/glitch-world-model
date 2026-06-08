# Reproducibility Checklist

Use this checklist before reporting any experiment.

## Environment

- [ ] Record Python version.
- [ ] Record OS and hardware if relevant.
- [ ] Install dependencies from a documented command.
- [ ] Lock dependency versions when moving beyond MVP.
- [ ] Record whether `opencv-python` is required.

## Data

- [ ] Record dataset name, source URL, and access date.
- [ ] Record dataset version, split, and any subset parameters.
- [ ] Keep raw data out of git.
- [ ] Keep checkpoints out of git.
- [ ] Record label schema and temporal label interpretation.
- [ ] Separate public benchmark results from synthetic sanity checks.

## Randomness

- [ ] Record random seeds for generated datasets.
- [ ] Record train/validation/test split seeds.
- [ ] Record model initialization seeds for learned baselines.

## Commands and outputs

- [ ] Log the exact preprocessing command.
- [ ] Log the exact scoring command.
- [ ] Log the exact evaluation command.
- [ ] Save `manifest.csv`.
- [ ] Save `scores.csv`.
- [ ] Save `metrics.json`.
- [ ] Generate a Markdown report when possible.
- [ ] Record the Git commit hash.

## Safety

- [ ] Confirm no `data/` files are committed.
- [ ] Confirm no `outputs/` artifacts are committed unless they are intentional tiny examples.
- [ ] Confirm no `.test-tmp/` files are committed.
- [ ] Confirm no checkpoints, videos, or cache folders are committed.

## Tests

- [ ] Run `python -m pytest` when dependencies are available.
- [ ] If tests are skipped, document the missing dependencies.
- [ ] Add or update focused tests for new scorer behavior.

## Future tooling

- [ ] Consider DVC for dataset versioning.
- [ ] Consider W&B or MLflow for experiment tracking.
- [ ] Keep the lightweight CSV/JSON reports as the source-of-truth interface.
