# Phase 6E Kaggle Video Autoencoder Design

## Goal

Add the first gradient-trained neural baseline without weakening the existing TempGlitch
evaluation protocol. The phase produces a Kaggle-compatible Conv3D autoencoder training and
validation-scoring package. It does not claim a trained model or benchmark result until a real
Kaggle run produces the checkpoint and metrics.

## Scope

- Add an optional PyTorch dependency group.
- Add a `video_autoencoder` scorer that preserves the existing `manifest.csv` to `scores.csv`
  interface.
- Add a Kaggle-oriented runner that derives train-normal and validation records from a
  pair-suspect grouped split.
- Support rebasing absolute local `clip_dir` values onto a Kaggle dataset root.
- Save checkpoint and training metadata only under gitignored paths.
- Document the exact Kaggle command and the locked-test boundary.

Out of scope:

- Training LeWorldModel from scratch.
- Adding `video_autoencoder` to the Phase 6D repeated locked-test selector before a checkpoint
  and validation decision exist.
- Reporting GPU runtime, AUROC, F1, or superiority without generated evidence.

## Architecture

`src/glitch_detection/video_autoencoder.py` owns the optional PyTorch boundary. Importing the
package remains possible without PyTorch; train and score operations raise a clear dependency
error when PyTorch is absent. The module loads fixed-length RGB clips, builds a compact Conv3D
autoencoder, trains with reconstruction MSE, saves a portable checkpoint, and writes anomaly
scores as per-clip reconstruction error.

`scripts/run_kaggle_video_autoencoder.py` is the experiment entrypoint. It reads the existing
combined manifest and grouped `split.csv`, verifies zero pair-suspect leakage, selects only
`train` plus `Normal` sources for fitting, scores only validation records, and writes generated
manifests, metadata, checkpoint, and validation scores below one output root.

The scorer registry exposes `video_autoencoder` for compatibility. Registry scoring requires
`VIDEO_AUTOENCODER_CHECKPOINT`; it never trains implicitly.

## Data Flow

1. Read `manifest.csv` and grouped `split.csv`.
2. Validate that no pair-suspect group crosses splits.
3. Rebase each `clip_dir` to `<clips-root>/<source>/clips/<clip_id>` when `--clips-root` is set.
4. Build train-normal and validation record lists.
5. Train the Conv3D autoencoder only on train-normal records.
6. Save checkpoint and `training_metadata.json`.
7. Score validation records and write interface-compatible `validation_scores.csv`.
8. Leave test untouched until a validation-selected configuration is locked.

## Failure Handling

- Missing PyTorch: fail with an install command for `.[gpu]`.
- Missing manifest, split, frame directory, or checkpoint: fail before training or scoring.
- Split leakage or no train-normal records: fail before model fitting.
- Invalid image size, clip length, epoch count, or batch size: fail with a clear value error.

## Testing

CPU unit tests avoid requiring PyTorch. They cover path rebasing, train-normal/validation
partitioning, leakage rejection, scorer registration, and the clear missing-PyTorch/checkpoint
guard. A real Kaggle smoke run is a separate acceptance gate because the local environment does
not currently have PyTorch.

## Acceptance Criteria

- Existing tests remain green without PyTorch.
- New focused tests prove data partitioning and portability behavior.
- `video_autoencoder` is pluggable but cannot silently train or use test labels.
- The Kaggle runner has a dry-run mode that verifies inputs and emits no checkpoint.
- Documentation states that training and metrics remain pending until a real Kaggle run.

