# Phase 3/4 TempGlitch Split Baseline Results

## 1. Objective

Phase 3/4 moves beyond the two-video Phase 2 smoke test by evaluating a larger TempGlitch slice with a leakage-aware video-level split. The experiment compares:

- `frame_diff`
- `feature_distance`
- `mini_latent`

The experiment remains preliminary. TempGlitch's public artifact exposes binary per-video labels, not verified temporal spans.

## 2. Dataset slice

- Dataset URL: <https://huggingface.co/datasets/asgaardlab/TempGlitch>
- Access date: `2026-06-08`
- Dataset revision: `1d46a63c31ebfe3b675b51a2231d547da372eff9`
- Categories:
  - `Blinking`
  - `Frozen Animation`
  - `Shooting Error`
  - `Stuck in Place`
  - `Velocity Bug`
- Videos per category / label: `3`
- Total videos: `30`
- Total clips: `1,650`
- Split policy: for each category and label, one video each for train, validation, and test
- Split seed: `42`
- Train / validation / test videos: `10 / 10 / 10`
- `clip_length`: `16`
- `stride`: `16`
- `size`: `128`
- Label limitation: binary per-video labels only; buggy videos are mapped to full-video positive intervals

## 3. Leakage controls

- Split unit is video / source, not clip.
- No source appears in more than one split.
- Thresholds are selected on validation scores and labels.
- Test metrics use the fixed validation-selected threshold.
- `feature_distance` fits its normal centroid on train-normal clips only.
- `mini_latent` fits PCA and transition parameters on train-normal clips only.
- `frame_diff` has no fitted parameters.
- `feature_distance` and `mini_latent` each fit on `255` train-normal clips.

## 4. Commands

```powershell
python scripts\run_tempglitch_split_experiments.py --categories Blinking "Frozen Animation" "Shooting Error" "Stuck in Place" "Velocity Bug" --limit-per-group 3 --clip-length 16 --stride 16 --size 128 --scorer frame_diff --scorer feature_distance --scorer mini_latent
```

## 5. Artifacts generated

All artifacts below are gitignored:

- `data/raw/tempglitch_phase3/metadata.csv`
- `data/processed/tempglitch_phase3/manifest.csv`
- `data/processed/tempglitch_phase3/labels.csv`
- `data/processed/tempglitch_phase3/split.csv`
- `data/processed/tempglitch_phase3/{train,validation,test}_manifest.csv`
- `data/processed/tempglitch_phase3/{train,validation,test}_labels.csv`
- `outputs/tempglitch_phase3/{scorer}_val_scores.csv`
- `outputs/tempglitch_phase3/{scorer}_test_scores.csv`
- `outputs/tempglitch_phase3/{scorer}_calibration.json`
- `outputs/tempglitch_phase3/{scorer}_test_metrics.json`
- `outputs/tempglitch_phase3/phase3_comparison.md`
- `outputs/tempglitch_phase3/phase3_summary.json`

## 6. Results

| Scorer | Val threshold | Test precision | Test recall | Test F1 | Test AUROC | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `frame_diff` | `0.0013542` | `0.468571` | `0.984000` | `0.634839` | `0.588631` | Highest test AUROC; validation threshold produced zero test true negatives |
| `feature_distance` | `0.06626666` | `0.472868` | `0.976000` | `0.637076` | Highest test F1 by a small margin; fit on train normals only |
| `mini_latent` | `0.01788175` | `0.469582` | `0.988000` | `0.636598` | Did not outperform either simple baseline on test AUROC; fit on train normals only |

Test split:

- clips: `529`
- positive clips: `250`
- negative clips: `279`

Positive clips by split:

- train: `290`
- validation: `289`
- test: `250`

## 7. Interpretation

- `frame_diff` performs best by AUROC (`0.588631`).
- `feature_distance` performs best by F1 (`0.637076`), but the margin over `mini_latent` and `frame_diff` is small.
- `mini_latent` does not beat `frame_diff` or `feature_distance` on this slice in a way that supports a superiority claim.
- All methods show weak discrimination and high false-positive rates at validation-selected F1 thresholds.
- This strengthens the reproducibility and leakage-control package, but not the latent-surprise performance claim.
- The full-paper path remains risky. A short-paper framing remains safer unless scaling, ablations, and failure analysis establish a stronger result.

## 8. Limitations

- Labels are per-video, not temporal spans.
- The dataset slice is still small at `30` videos.
- The split is repo-defined, not an official TempGlitch split.
- Thresholds optimize validation F1 and may not transfer robustly.
- No real LeWorldModel integration exists.
- No state-of-the-art claim is supported.
- No temporal localization claim is supported.

## 9. Next step

Recommended next: Phase 3B, scale the TempGlitch experiments and add per-category / failure analysis. The current weak AUROC and false-positive behavior should be understood before running broad ablations.
