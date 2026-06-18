# WOB-P1 Seed42 Training Artifact Verification

Date: 2026-06-18

Status: `WOB_P1_SEED42_TRAINING_ARTIFACT_VALIDATED`

## 1. Scope

This note records verification of the downloaded `WOB-P1` seed42 training artifact only.

It does not record a WOB evaluation result, a WOB detection metric, a cross-game result, an
action-conditioning benefit, or any locked-test result.

## 2. Verified Artifact

| Item | Value |
| --- | --- |
| Artifact bundle | `wob_seed42_artifacts.tar.gz` |
| SHA256 | `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03` |
| Sidecar target recorded by Kaggle | `/kaggle/working/wob_seed42_artifacts.tar.gz` |
| Archive member count | `40` |
| Raw WOB tar files bundled | `0` regular files |
| Validator status | `wob_seed42_validated` |

The sidecar hash matched the locally computed artifact hash. The validator read the bundle without
extracting raw datasets into the repository.

## 3. Training Metadata

| Field | Value |
| --- | --- |
| Seed | `42` |
| Device | `cuda` |
| Action dimension | `4` |
| Target optimizer updates | `15000` |
| Updates completed | `4000` |
| Best update | `1500` |
| Best validation-normal loss | `0.6093359693480057` |
| Early stop | `true` |
| Early-stop reason | `early_stopping_patience` |
| Validation evaluations | `8` |
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

The artifact supports only the narrow statement that WOB-P1 seed42 training produced a
validator-passed artifact while excluding validation-buggy rows from fit/selection and leaving
locked test closed.

## 5. Debug Tarball Classification

The accompanying `wob_seed42_failure_debug.tar.gz` is classified as
`STALE_DEBUG_FALSE_POSITIVE`.

Evidence:

- The failure-debug preflight report failed CUDA because it referenced the non-existent
  `torch._C._CudaDeviceProperties.total_mem` attribute.
- The same debug package recorded the official Kaggle WOB roots under nested dataset paths.
- The validated success artifact later recorded successful CUDA training, a passed validator, and
  the same locked-test false flags.

The robust runner has been patched so a successful finalization can remove a stale failure-debug
package instead of leaving a misleading failure archive beside a valid success bundle.

## 6. Allowed And Forbidden Claims

Allowed:

- WOB-P1 seed42 produced a SHA256-verified, validator-passed training artifact.
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

The empirical WOB-P1 seed42 track is now at an evaluation-readiness gate, not an evaluation result.
The next gate is to freeze a non-locked WOB evaluation manifest and reporting path, then require a
separate explicit human command before running any WOB evaluation or opening seed43/44.
