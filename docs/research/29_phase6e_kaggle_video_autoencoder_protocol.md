# Phase 6E Kaggle Video Autoencoder Protocol

## Status

The repo now contains a Kaggle-compatible Conv3D autoencoder training and validation-scoring
package. No neural model has been trained on Kaggle yet, no checkpoint has been verified, and no
video-autoencoder AUROC or F1 result exists.

This phase is an optional learned baseline from the roadmap. It is not real LeWorldModel or JEPA
integration.

## Research Boundary

- Fit data: clips from sources labeled `Normal` and assigned to `train`.
- Validation data: every clip from sources assigned to `validation`.
- Test data: counted for audit only; not materialized or scored by the training runner.
- Grouping: existing `pair_id_heuristic` split.
- Required leakage condition: zero pair-suspect groups cross train, validation, or test.
- Anomaly score: per-clip Conv3D autoencoder reconstruction MSE.
- Model/config/threshold selection: validation only.
- Locked test: separate later action after one configuration is fixed.

## Implementation

- Optional dependency: `python -m pip install -e ".[gpu]"`
- Scorer/training module: `src/glitch_detection/video_autoencoder.py`
- Portable split helpers: `src/glitch_detection/neural_protocol.py`
- Kaggle runner: `scripts/run_kaggle_video_autoencoder.py`
- Checkpoints and generated outputs remain gitignored.
- `video_autoencoder` is registered through `src/glitch_detection/score_clips.py`.
- Registry scoring requires `VIDEO_AUTOENCODER_CHECKPOINT`; it never trains implicitly.

## Local Dry-Run Evidence

Command:

```powershell
python scripts\run_kaggle_video_autoencoder.py `
  --dry-run `
  --manifest data\processed\tempglitch_phase3b\manifest.csv `
  --split outputs\tempglitch_phase6d\seed_42\split.csv `
  --output-root outputs\tempglitch_phase6e\seed_42
```

Observed protocol audit on 2026-06-09:

- Train-normal: `31` sources, `1,724` clips
- Validation: `18` sources, `1,071` clips
- Test: `20` sources, `1,125` clips
- Cross-split pair-suspect groups: `0`
- Test materialized: `false`
- Test scored: `false`

This verifies data selection and portability logic only. It is not a training result.

## Local Runtime Smoke Evidence

A separate gitignored synthetic smoke run verified the PyTorch runtime path on 2026-06-09:

- Python: `3.12.13`
- PyTorch: `2.12.0`
- Device: CPU
- Training: one epoch on `10` synthetic clips
- Checkpoint save/load: completed
- Score export: `10` interface-compatible rows

This verifies that train, checkpoint, reload, and score code executes. It is not TempGlitch
training evidence and must not be reported as a research result.

## Kaggle Run

Upload the gitignored Phase 3B processed clip tree, combined manifest, and Phase 6D seed-42
`split.csv` as a private Kaggle dataset. The manifest contains machine-specific local paths, so
`--clips-root` must point to the uploaded processed clip root.

Dry-run first:

```bash
python -m pip install -e ".[gpu]"
python scripts/run_kaggle_video_autoencoder.py \
  --dry-run \
  --manifest /kaggle/input/glitch-world-model-phase6e/manifest.csv \
  --split /kaggle/input/glitch-world-model-phase6e/split.csv \
  --clips-root /kaggle/input/glitch-world-model-phase6e/tempglitch_phase3b \
  --output-root /kaggle/working/tempglitch_phase6e/seed_42 \
  --device cuda \
  --seed 42
```

Train and score validation:

```bash
python scripts/run_kaggle_video_autoencoder.py \
  --manifest /kaggle/input/glitch-world-model-phase6e/manifest.csv \
  --split /kaggle/input/glitch-world-model-phase6e/split.csv \
  --clips-root /kaggle/input/glitch-world-model-phase6e/tempglitch_phase3b \
  --output-root /kaggle/working/tempglitch_phase6e/seed_42 \
  --device cuda \
  --image-size 64 \
  --clip-length 16 \
  --batch-size 8 \
  --epochs 10 \
  --learning-rate 0.001 \
  --seed 42
```

## Generated Artifacts

Expected under `/kaggle/working/tempglitch_phase6e/seed_42/`:

- `protocol_audit.json`
- `train_normal_manifest.csv`
- `validation_manifest.csv`
- `video_autoencoder.pt`
- `training_metadata.json`
- `validation_scores.csv`
- `phase6e_summary.json`

Download these artifacts for audit, but do not commit checkpoint, generated manifests, scores,
or outputs.

The current local machine has no Kaggle CLI credential/token, so the Kaggle GPU job cannot be
submitted from this environment yet.

## Acceptance Gate Before Any Result Claim

- Kaggle dry-run reports zero cross-split groups and the expected partition counts.
- Training completes on a real GPU and records device, seed, config, and epoch losses.
- Validation scores contain one row per validation clip with no NaN or exception.
- One configuration and aggregation are selected from validation only.
- Test is materialized and scored only after that selection is locked.
- Metrics are generated from the locked test and documented before any paper-facing claim.
