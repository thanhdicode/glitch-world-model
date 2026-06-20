# WOB-P1 Seed44 Kaggle Input-Detection Failure

Date: 2026-06-19

Status: `WOB_P1_SEED44_KAGGLE_INPUT_DETECTION_FAILURE`

## 1. Scope

This note records the failed first seed44 Kaggle training attempt on commit
`8c6c0a58bc0d205dab745ecb00e3483afe3cb999`.

It does not record a valid WOB training artifact, a WOB evaluation result, a WOB detection
metric, a cross-game result, an action-conditioning benefit, or any locked-test result.

## 2. What Happened

The downloaded `wob_seed44_artifacts.tar.gz` matched its SHA256 sidecar, but the tarball was a
small failure bundle rather than a valid training artifact.

Local validator result:

- `FAIL`
- reason: missing required tarball members such as `training_metadata.json`,
  `checkpoint_weights.pt`, `weights.pt`, `best_weights.pt`, `loss_history.json`, and
  `validation_history.json`

## 3. Kaggle Failure Classification

Primary class:

- `KAGGLE_INPUT_DETECTION_FAILURE`

Observed root cause from the Kaggle log:

- `detect_kaggle_roots` could not uniquely resolve the mounted WOB dataset roots containing
  `NORMAL-TRAIN` and `TEST`
- downstream stages then ran without a valid `detected_inputs.json`, so the selected 60 normal
  rows were unresolved and no Lance datasets or training checkpoint artifacts were produced

This is not a model-training failure and not a locked-test issue.

## 4. Safety Status

- `locked_test_materialized = false`
- `locked_test_scored = false`
- `evaluation_run = false`
- no WOB evaluation was opened
- no WOB performance claim is supported

## 5. Repository Follow-Up

The repository is patched after this failure to:

1. accept `world-of-bugs-train` as a valid Kaggle normal-input dataset slug during root detection
2. keep exact-match detection for the known nested Kaggle dataset layout
3. stop immediately if `detected_inputs.json` is missing instead of continuing into a bogus
   finalization path

## 6. Next Gate

Rerun the seed44 Kaggle robust training cell on the patched commit, then download and locally
verify the new `wob_seed44_artifacts.tar.gz` plus `.sha256` sidecar before opening `R5-WOB`.
