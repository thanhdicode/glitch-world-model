# DVC And Hydra Migration Plan

This is a plan, not a completed migration.

## Why DVC

DVC can version dataset manifests, pipeline dependencies, model artifacts, and reproducible stage
relationships without putting large payloads in Git. Adoption should begin with a non-locked,
small preprocessing stage and an approved remote-storage policy.

## Why Hydra

Hydra can make future LeWM audit and integration configurations explicit, composable, and
multirun-capable. It is useful for separating data, model, scorer, split, and runtime settings.

## Staged Migration

1. Audit current script arguments and stable CSV interfaces.
2. Introduce Hydra wrappers without changing existing CLI behavior.
3. Pilot DVC on a small non-sensitive preprocessing artifact.
4. Select and document a DVC remote; never commit credentials.
5. Add pipeline stages only after identical outputs are verified.
6. Keep locked-test stages disabled until their release gate opens.

DVC is installed on the audited user environment. A metadata-only `dvc.yaml` draft exposes the
research release validator as a stage; it has no data outputs and no remote. Data/model stages
remain blocked until a storage remote and first-stage ownership decision are approved.
