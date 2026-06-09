# Phase 3B Scaled TempGlitch Failure Analysis

## 1. Objective

Phase 3B scales beyond the 30-video split slice to understand why the leakage-aware baselines remain weak. The analysis asks:

- which TempGlitch categories are easier or harder
- whether false positives are concentrated in specific normal-video categories
- whether the public binary per-video labels create noisy clip labels
- whether `mini_latent` shows category-specific signal despite weak global results
- whether validation thresholds are too aggressive

## 2. Dataset slice

- Dataset URL: <https://huggingface.co/datasets/asgaardlab/TempGlitch>
- Access date: `2026-06-08`
- Dataset revision: `1d46a63c31ebfe3b675b51a2231d547da372eff9`
- Categories: `Blinking`, `Frozen Animation`, `Shooting Error`, `Stuck in Place`, `Velocity Bug`
- Limit per category / label: `10`
- Total videos: `100`
- Total clips: `5,572`
- Split policy: per category and label, `6` train, `2` validation, `2` test
- Train / validation / test videos: `60 / 20 / 20`
- Positive clips by split: train `1,535`, validation `501`, test `573`
- Negative clips by split: train `1,847`, validation `593`, test `523`
- `clip_length`: `16`
- `stride`: `16`
- `size`: `128`
- Label limitation: binary per-video labels only; buggy videos are mapped to full-video positive intervals

## 3. Leakage controls

- Split by video/source, not clip.
- Threshold calibrated on validation only.
- Test evaluated with fixed validation-selected threshold.
- `feature_distance` fit on train-normal clips only.
- `mini_latent` fit on train-normal clips only.
- No test tuning was used.

## 4. Commands

```powershell
python scripts\run_tempglitch_split_experiments.py --experiment-name tempglitch_phase3b --categories Blinking "Frozen Animation" "Shooting Error" "Stuck in Place" "Velocity Bug" --limit-per-group 10 --clip-length 16 --stride 16 --size 128 --scorer frame_diff --scorer feature_distance --scorer mini_latent --analysis --top-errors 20
```

## 5. Generated artifacts

All artifacts below are gitignored:

- `data/raw/tempglitch_phase3b/`
- `data/processed/tempglitch_phase3b/manifest.csv`
- `data/processed/tempglitch_phase3b/labels.csv`
- `data/processed/tempglitch_phase3b/split.csv`
- `outputs/tempglitch_phase3b/{scorer}_test_metrics.json`
- `outputs/tempglitch_phase3b/{scorer}_category_metrics.json`
- `outputs/tempglitch_phase3b/{scorer}_source_metrics.json`
- `outputs/tempglitch_phase3b/{scorer}_false_positives.csv`
- `outputs/tempglitch_phase3b/{scorer}_false_negatives.csv`
- `outputs/tempglitch_phase3b/{scorer}_score_distribution.json`
- `outputs/tempglitch_phase3b/phase3b_summary.json`
- `outputs/tempglitch_phase3b/phase3b_comparison.md`

## 6. Main results

| Scorer | Test precision | Test recall | Test F1 | Test AUROC | Best category | Worst category |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `frame_diff` | `0.522810` | `1.000000` | `0.686639` | `0.410416` | `Shooting Error` | `Stuck in Place` |
| `feature_distance` | `0.525487` | `0.989529` | `0.686441` | `0.504053` | `Velocity Bug` | `Stuck in Place` |
| `mini_latent` | `0.522810` | `1.000000` | `0.686639` | `0.458728` | `Velocity Bug` | `Stuck in Place` |

## 7. Per-category results

By AUROC:

- `feature_distance` is strongest on `Blinking` (`0.593243`) and `Velocity Bug` (`0.669169`).
- `frame_diff` is strongest on `Shooting Error` (`0.511071`).
- `mini_latent` does not win any category by AUROC.
- `mini_latent` is closest to useful signal on `Velocity Bug` (`0.531094`) and `Shooting Error` (`0.490094`).
- All methods fail badly on `Stuck in Place`; best AUROC there is only `0.376283`.

By F1:

- F1 is dominated by high recall and class balance because thresholds are very permissive.
- `frame_diff` and `mini_latent` predict every test clip as positive, producing recall `1.0` and true negatives `0`.
- `feature_distance` produces only `11` true negatives across `523` negative test clips.

## 8. Failure analysis

Main false-positive patterns:

- `frame_diff` top false positives concentrate in `Velocity Bug`, `Blinking`, and `Shooting Error` normal clips.
- `feature_distance` top false positives concentrate in `Stuck in Place` and `Frozen Animation` normal clips.
- `mini_latent` top false positives are distributed across normal clips from `Frozen Animation`, `Stuck in Place`, `Velocity Bug`, `Blinking`, and `Shooting Error`.

Main false-negative patterns:

- `frame_diff` has no false negatives because it predicts all test clips positive.
- `mini_latent` has no false negatives for the same reason.
- `feature_distance` has `6` false negatives, mostly `Shooting Error` buggy clips.

Likely causes:

- Full-video labels make many visually normal clips inside buggy videos count as positive.
- Validation F1 calibration favors very low thresholds and high recall.
- Normal gameplay motion can score as anomalous under frame-difference and feature-distance baselines.
- Clip-level evaluation is mismatched to binary per-video public labels.

## 9. Research interpretation

- The latent-surprise hypothesis does not currently survive as a global performance claim.
- `mini_latent` shows limited category-specific signal on `Velocity Bug`, but not enough for superiority.
- The current method package is not enough for a full paper unless the paper is framed around reproducibility and failure analysis rather than model performance.
- A short paper is safer than a full-paper performance claim.
- The next exact experiment should be video-level aggregation because the public labels are per-video.

## 10. Paper strategy decision

Decision: B. Continue short-paper path with honest reproducibility / failure-analysis framing.

Rationale:

- The benchmark pipeline and leakage controls are now strong.
- The global results remain weak.
- The current evidence does not justify ablations before fixing the clip-label mismatch.
- A full-paper path would require stronger method evidence, video-level aggregation, ablations, and preferably temporal-span annotations.

## 11. Claims allowed / forbidden

Allowed:

- The repo executes a leakage-aware TempGlitch experiment on a 100-video public slice.
- Thresholds are calibrated on validation and applied unchanged to test.
- `feature_distance` has the best global AUROC in Phase 3B, but only near-random.
- `mini_latent` does not show global superiority.
- Binary per-video labels likely make clip-level evaluation noisy.

Forbidden:

- No state-of-the-art claim.
- No temporal localization claim.
- No real LeWM integration claim.
- No claim that `mini_latent` outperforms simple baselines globally.
- No claim that the current metrics are full-paper-ready.

## 12. Follow-up: Phase 6B Video-Level Aggregation

Phase 3B clip-level results do not support a performance claim. Because the public TempGlitch
labels are per-video, Phase 6B aggregates clip scores into source/video scores and calibrates
thresholds on validation videos before fixed-threshold test evaluation.

Phase 6B evaluated six aggregation methods for all three scorers. The best global test AUROC
was `0.54` from `feature_distance` with median aggregation. The best `mini_latent` AUROC was
`0.52` with `p90` or `p95` aggregation. These results remain near random and do not establish
global `mini_latent` superiority.

Broad ablations should not start on the basis of this result. Real LeWorldModel integration
also remains optional until the evaluation protocol is stable and a stronger method signal or
better supervision becomes available.
