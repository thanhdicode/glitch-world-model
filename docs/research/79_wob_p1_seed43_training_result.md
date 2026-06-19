# WOB-P1 Seed43 Training Artifact Verification

Date: 2026-06-19

Status: `WOB_P1_SEED43_TRAINING_ARTIFACT_VALIDATED`

## 1. Scope

This note records verification of the downloaded `WOB-P1` seed43 training artifact only.

It does not record a WOB evaluation result, a WOB detection metric, a cross-game result, an
action-conditioning benefit, or any locked-test result.

## 2. Verified Artifact

| Item | Value |
| --- | --- |
| Artifact bundle | `wob_seed43_artifacts.tar.gz` |
| SHA256 | `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88` |
| Sidecar target recorded by Kaggle | `/kaggle/working/wob_seed43_artifacts.tar.gz` |
| Archive member count | `39` |
| Raw WOB tar files bundled | `0` regular files |
| Validator status | `wob_seed43_validated` |

The sidecar hash matched the locally computed artifact hash. The validator read the bundle without
extracting raw datasets into the repository.

## 3. Training Metadata

| Field | Value |
| --- | --- |
| Seed | `43` |
| Device | `cuda` |
| Action dimension | `4` |
| Target optimizer updates | `15000` |
| Updates completed | `4500` |
| Best update | `2000` |
| Best validation-normal loss | `0.6211924654035366` |
| Early stop | `true` |
| Early-stop reason | `early_stopping_patience` |
| Validation evaluations | `9` |
| Checkpoint reload | weights and optimizer verified |

This is training-artifact evidence under the WOB train-normal / validation-normal protocol. It is
not detection-performance evidence.

## 4. Protocol Flags

| Flag | Value |
| --- | --- |
| `train_normal_count` | `48` |
| `validation_normal_count` | `12` |
| `validation_buggy_excluded_count` | `60` |
| `locked_rows_skipped` | `59` |
| `validation_buggy_used_for_fit_select` | `false` |
| `locked_test_materialized` | `false` |
| `locked_test_scored` | `false` |
| `evaluation_run` | `false` |

The artifact supports only the narrow statement that WOB-P1 seed43 training produced a
validator-passed artifact while excluding validation-buggy rows from fit/selection and leaving
locked test closed.

## 5. Kaggle Log Note

The Kaggle log showed an early `ModuleNotFoundError: No module named 'cloud'` while launching the
standalone robust-preflight script, but the run then completed training, passed the in-run
validator, finalized the artifact bundle, removed the stale failure-debug tarball, and produced the
verified success tarball above.

The repository runner is patched after this verification so the robust preflight is invoked as a
module before the seed44 run.

## 6. Allowed And Forbidden Claims

Allowed:

- WOB-P1 seed43 produced a SHA256-verified, validator-passed training artifact.
- The run used train-normal optimization and validation-normal checkpoint selection under the
  recorded protocol counts.
- Validation-buggy rows were excluded from fit/selection.
- Locked test remained unmaterialized and unscored.

Forbidden:

- WOB detection performance.
- Cross-game generalization.
- Action-conditioning benefit.
- Superiority or state of the art.
- Locked-test result.
- WOB evaluation result.

## 7. Next Gate

The next gate is to run the seed44 Kaggle robust training cell, then download and locally verify
the resulting seed44 artifact bundle before opening any WOB evaluation step.
