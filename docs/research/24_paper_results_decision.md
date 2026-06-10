# Paper Results Decision

## 1. Current best available evidence

The strongest current evidence is Phase 3B: a leakage-aware 100-video TempGlitch slice across all five public categories. It uses `5,572` clips and a repo-defined `60 / 20 / 20` train/validation/test video split.

Phase 6C correction: "leakage-aware" here meant source/clip disjointness only. A conservative
pair-suspect audit found `19 / 35` suspected pairs crossing the Phase 3B splits (`65` total
grouping units). Therefore
all Phase 3B and Phase 6B performance results remain exploratory.

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

Phase 6B video-level aggregation is complete. The next method-facing step is a guarded real
LeWorldModel integration audit; the next paper-facing step is to consolidate Phase 6D/6E
negative and diagnostic evidence without claiming superiority.

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

- The repo provides a pair-suspect grouped TempGlitch split protocol for future runs.
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

## 11. Phase 6C correction

Phase 6C adds pair-suspect grouped splits, validation-only configuration selection, locked-test
single-config evaluation, and pair-level bootstrap confidence intervals. The existing test slice
was already exposed, so the current locked-test rehearsal is not a fresh final result. Repeated
grouped refit/scoring was completed in Phase 6D for seeds `42` through `46`. The selected
pipeline achieved AUROC `0.573170 +/- 0.117582`, but all per-seed AUROC confidence intervals
include `0.5`, so the result does not establish above-chance performance or method superiority.

## 12. Phase 6E validation-only neural result

Phase 6E completed a real Kaggle CUDA Conv3D autoencoder run fitted on `1,724` train-normal
clips and scored `1,071` validation clips. Validation AUROC was `0.403865`. Locked test was not
materialized or scored. This is engineering evidence only and does not support improvement,
LeWorldModel, JEPA, or state-of-the-art claims.
