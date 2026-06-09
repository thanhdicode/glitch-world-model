# Paper Results Decision

## 1. Current best available evidence

The strongest current evidence is Phase 3B: a leakage-aware 100-video TempGlitch slice across all five public categories. It uses `5,572` clips and a repo-defined `60 / 20 / 20` train/validation/test video split.

## 2. Main result table

| Scorer | Test precision | Test recall | Test F1 | Test AUROC |
| --- | ---: | ---: | ---: | ---: |
| `frame_diff` | `0.522810` | `1.000000` | `0.686639` | `0.410416` |
| `feature_distance` | `0.525487` | `0.989529` | `0.686441` | `0.504053` |
| `mini_latent` | `0.522810` | `1.000000` | `0.686639` | `0.458728` |

## 3. Does mini_latent outperform baselines?

No. `mini_latent` does not outperform the simple baselines globally. It is below `feature_distance` and above `frame_diff` by AUROC, but both differences are weak and not enough for a superiority claim.

Category-specific note:

- `mini_latent` has its best category AUROC on `Velocity Bug` (`0.531094`).
- It does not win any category by AUROC.

## 4. Does the project support temporal localization?

No. The public TempGlitch labels are binary per-video labels. The repo's current conversion maps buggy videos to full-video positive intervals. That is not temporal-span supervision.

## 5. Does the project support full paper?

Not yet. The engineering package is stronger, but the scientific performance result is weak. A full paper would need:

- stronger method or real LeWM integration
- video-level aggregation for per-video labels
- ablations
- failure-case figures
- preferably verified temporal-span annotations

## 6. Does the project support short paper?

Yes, with an honest framing:

- reproducible benchmark pipeline
- public benchmark access resolution
- leakage-aware evaluation
- failure analysis showing why clip-level evaluation with binary per-video labels is hard
- careful positioning of latent-surprise methods as future work or a negative/diagnostic result

## 7. Recommended next phase

Recommended next: Phase 6B, add video-level aggregation for per-video labels.

Reason:

- The current labels are per-video.
- Clip-level thresholding produces many false positives.
- Video-level aggregation directly matches the available supervision.

## 8. Decision gate before Phase 7 ablations

Do not run broad ablations until one of these is true:

- video-level aggregation shows a clearer signal
- a stronger method improves ranking under the current split
- temporal-span labels become available

If none of those happens, the best paper strategy is short-paper reproducibility and failure analysis.

## 9. Phase 6B video-level result

Phase 6B evaluated `mean`, `max`, `median`, `p90`, `p95`, and `topk_mean` aggregation on the
existing Phase 3B validation and test videos. Thresholds were selected only on validation
videos and applied unchanged to test videos.

- Best global test AUROC: `feature_distance` with `median`, `0.54`.
- Best `mini_latent` test AUROC: `0.52` with `p90` or `p95`.
- Best `frame_diff` test AUROC: `0.46` with `p90`.
- Video-level F1 remains dominated by high recall and false positives.

Decision: Phase 6B better matches the public label granularity, but it does not reveal a clear
enough signal to justify broad Phase 7 ablations. Continue the short-paper reproducibility and
failure-analysis path while prioritizing method improvement or better supervision.

## 10. Claim status after Phase 6B

Allowed:

- The repo provides a leakage-aware TempGlitch split protocol.
- The repo evaluates `frame_diff`, `feature_distance`, and `mini_latent` at clip and video level.
- Thresholds are selected on validation and fixed on test.
- Video-level aggregation better matches TempGlitch's public per-video labels.
- Binary per-video labels limit temporal localization claims.

Forbidden:

- No state-of-the-art claim.
- No real LeWorldModel claim.
- No temporal IoU or mIoU claim.
- No global `mini_latent` superiority claim.
- No VLM superiority claim.
- No dataset creation claim.
