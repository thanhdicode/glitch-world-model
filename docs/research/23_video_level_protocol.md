# Phase 6B Video-Level Evaluation Protocol

## 1. Motivation

The public TempGlitch artifact exposes binary per-video labels. Phase 3B mapped each buggy
video to a full-video positive interval so the existing clip CSV pipeline could run, but this
makes visually normal clips inside buggy videos positive. The resulting clip-level evaluation
is therefore mismatched to the available supervision.

Phase 6B aggregates clip anomaly scores into one score per source/video before calibration and
evaluation. This matches the public label granularity without inventing temporal spans.

## 2. Aggregation methods

For every scorer, Phase 6B evaluates:

- `mean`
- `max`
- `median`
- `p90`
- `p95`
- `topk_mean`, using the highest three clip scores by default

If a source has fewer than three clips, `topk_mean` uses all available clips.

## 3. Labels and split

- Source label is positive when the source has at least one positive label interval.
- A source with no positive interval is an implicit negative.
- Sources remain in the Phase 3B repo-defined split.
- No source or clip crosses train, validation, and test boundaries.

## 4. Threshold policy

- Aggregate validation clips into validation video scores.
- Select one global threshold per scorer and aggregation by best validation-video F1.
- Apply that threshold unchanged to test videos.
- Per-category test metrics use the same global validation-selected threshold.
- Never tune a threshold on test videos or separately per test category.

## 5. Metrics

Report AUROC, precision, recall, F1, accuracy, TP, FP, FN, TN, source count, positive source
count, and negative source count. AUROC is `null` when a group has only one class.

## 6. Reproducible command

```powershell
python scripts\run_tempglitch_video_level_experiments.py `
  --experiment-name tempglitch_phase3b `
  --processed-dir data\processed\tempglitch_phase3b `
  --input-outputs-dir outputs\tempglitch_phase3b `
  --output-dir outputs\tempglitch_phase3b_video_level `
  --scorer frame_diff `
  --scorer feature_distance `
  --scorer mini_latent `
  --aggregation mean max median p90 p95 topk_mean `
  --top-k 3
```

## 7. Claim guardrails

Allowed:

- The repo evaluates three baseline scorers at clip and video level.
- Video-level aggregation matches the granularity of the public TempGlitch labels.
- Thresholds are selected on validation videos and applied unchanged to test videos.

Forbidden:

- No temporal localization, temporal IoU, or mIoU claim.
- No state-of-the-art claim.
- No real LeWorldModel claim.
- No global `mini_latent` superiority claim unless results establish it.
