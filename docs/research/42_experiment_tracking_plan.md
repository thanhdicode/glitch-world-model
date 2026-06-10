# Experiment Tracking Plan

## Recommended Approach

Use MLflow locally first because it can record parameters, metrics, tags, and artifact references
without requiring a hosted account. W&B remains an optional team-facing alternative.

## Required Run Metadata

- Git commit and dirty-state flag
- dataset revision and split fingerprint
- scorer/model identity and whether it is a proxy
- seed, configuration, fitting partition, and grouping method
- validation decision and locked-test gate status
- metrics, limitations, and claim-registry IDs

## Storage Policy

Local MLflow stores, W&B caches, raw artifacts, scores, and checkpoints remain gitignored.
GitHub receives small reviewed summaries and protocols. A future Zenodo release may archive a
curated, legally redistributable snapshot.

## Release Rule

An experiment tracker record is evidence support, not proof by itself. Claims still require
protocol audit, artifact validation, and claim-registry review.
