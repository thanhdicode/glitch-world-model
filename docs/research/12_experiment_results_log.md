# Experiment Results Log

## Phase 3B: Scaled Clip-Level TempGlitch

Status: completed on local Phase 3B artifacts.

Command:

```powershell
python scripts\run_tempglitch_split_experiments.py --experiment-name tempglitch_phase3b --categories Blinking "Frozen Animation" "Shooting Error" "Stuck in Place" "Velocity Bug" --limit-per-group 10 --clip-length 16 --stride 16 --size 128 --scorer frame_diff --scorer feature_distance --scorer mini_latent --analysis --top-errors 20
```

Actual result: best global clip-level test AUROC was `0.504053` from `feature_distance`.
See [22_phase3b_scaled_failure_analysis.md](22_phase3b_scaled_failure_analysis.md).

## Phase 6B: Video-Level Aggregation

Status: completed on the existing local Phase 3B artifacts. No dataset download was required.

Command:

```powershell
python scripts\run_tempglitch_video_level_experiments.py --experiment-name tempglitch_phase3b --processed-dir data\processed\tempglitch_phase3b --input-outputs-dir outputs\tempglitch_phase3b --output-dir outputs\tempglitch_phase3b_video_level --scorer frame_diff --scorer feature_distance --scorer mini_latent --aggregation mean max median p90 p95 topk_mean --top-k 3
```

Actual selected results:

| Scorer | Best aggregation by test AUROC | Test AUROC | Test F1 | TP / FP / FN / TN |
| --- | --- | ---: | ---: | --- |
| `frame_diff` | `p90` | `0.460000` | `0.666667` | `10 / 10 / 0 / 0` |
| `feature_distance` | `median` | `0.540000` | `0.620690` | `9 / 10 / 1 / 0` |
| `mini_latent` | `p90` or `p95` | `0.520000` | `0.642857` / `0.689655` | `9 / 9 / 1 / 1` or `10 / 9 / 0 / 1` |

Interpretation:

- Best video-level AUROC is `0.54`, still close to random.
- `mini_latent` does not outperform `feature_distance` globally.
- Validation-F1 thresholds still favor high recall and many false positives.
- The result does not open the gate for broad Phase 7 ablations.

## Generated Artifacts

All generated artifacts are gitignored:

- `outputs/tempglitch_phase3b_video_level/*_validation_video_scores.csv`
- `outputs/tempglitch_phase3b_video_level/*_test_video_scores.csv`
- `outputs/tempglitch_phase3b_video_level/*_video_calibration.json`
- `outputs/tempglitch_phase3b_video_level/*_test_video_metrics.json`
- `outputs/tempglitch_phase3b_video_level/*_category_video_metrics.json`
- `outputs/tempglitch_phase3b_video_level/*_category_video_metrics.md`
- `outputs/tempglitch_phase3b_video_level/video_level_summary.json`
- `outputs/tempglitch_phase3b_video_level/video_level_comparison.md`

## Skipped And TBD

- Dataset download: skipped because all required Phase 3B artifacts existed locally.
- Real LeWorldModel integration: `TBD`; outside Phase 6B scope.
- Temporal localization metrics: `TBD`; public temporal spans are not verified.
