# WOB-P1 Seed44 Training Artifact Verification

Date: 2026-06-19

Status: `WOB_P1_SEED44_TRAINING_ARTIFACT_VALIDATED`

## 1. Scope

This note records verification of the downloaded `WOB-P1` seed44 training artifact only.

It does not record a WOB evaluation result, a WOB detection metric, a cross-game result, an
action-conditioning benefit, or any locked-test result.

## 2. Verified Artifact

| Item | Value |
| --- | --- |
| Artifact bundle | `wob_seed44_artifacts.tar.gz` |
| SHA256 | `c5b3178cdb75a0c1f9bcca78eba8beaaf21ffa703917a3f42c476563849fd041` |
| Sidecar target recorded by Kaggle | `/kaggle/working/wob_seed44_artifacts.tar.gz` |
| Archive member count | `40` |
| Raw WOB tar files bundled | `0` regular files |
| Validator status | `wob_seed44_validated` |

The sidecar hash matched the locally computed artifact hash. The validator read the bundle without
extracting raw datasets into the repository.

## 3. Training Metadata

| Field | Value |
| --- | --- |
| Seed | `44` |
| Device | `cuda` |
| Action dimension | `4` |
| Target optimizer updates | `15000` |
| Updates completed | `5500` |
| Best update | `3000` |
| Best validation-normal loss | `0.6209993996026697` |
| Early stop | `true` |
| Early-stop reason | `early_stopping_patience` |
| Validation evaluations | `11` |
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

The artifact supports only the narrow statement that WOB-P1 seed44 training produced a
validator-passed artifact while excluding validation-buggy rows from fit/selection and leaving
locked test closed.

## 5. Kaggle Log Note

The verified successful run used commit `433556725f47ed9a9f5b65cf5563276b50bf6a5b`, detected the
official Kaggle WOB roots, completed train-only execution, passed the in-run validator, and wrote
the success tarball whose hash is recorded above.

This success supersedes the earlier seed44 failure-bundle incident documented in
[80_wob_p1_seed44_kaggle_input_detection_failure.md](80_wob_p1_seed44_kaggle_input_detection_failure.md).

## 6. Allowed And Forbidden Claims

Allowed:

- WOB-P1 seed44 produced a SHA256-verified, validator-passed training artifact.
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

All three planned WOB-P1 training artifacts (seed42, seed43, seed44) are now locally
SHA256-verified and validator-passed.

The next empirical gate is the frozen non-locked `R5-WOB` identical-episode evaluation path, which
remains closed until a separate explicit human command authorizes WOB evaluation.
