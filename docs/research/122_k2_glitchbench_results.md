# 122 - K2 GlitchBench Results

Date: 2026-06-25
Status: validated bounded K2 intake

## Intake Status

- Downloaded tarball:
  `C:\Users\ADMIN\Downloads\glitchbench_k2_outputs.tar.gz`
- Tarball SHA256:
  `a2a69b615b2988d952b8f753dca0f0fc204b60b1bef66823ce731a84a92ff5df`
- Local intake summary:
  `outputs/glitchbench_k2_intake/k2_glitchbench_intake_summary.json`
- Local intake summary SHA256:
  `31a59c634b9348b1a10a12cd829db382aeea64ea10a80c38c2345266e70c9493`
- Local report SHA256:
  `2fa38145448d7bf6c23c4825132d37a1ea91ce8d3c28c4561a69b45a95c246f0`

The downloaded K2 scientific bundle now validates locally with:

- summary status `k2_complete_lewm_and_baselines`
- `12` train-normal clips
- `24` validation clips
- K2 package validation status `validated`
- zero reported grouped cross-split leakage
- LeWM seed42/43/44 artifact receipts present with matching checkpoint-sidecar hashes
- `locked_test_materialized=false`
- `locked_test_scored=false`

## Frozen Benchmark Scope

This K2 result is bounded to the exact image-level synthetic-normal GlitchBench subset package
materialized by this repo. It does not support temporal-localization, natural-normal gameplay,
cross-game generalization, SOTA, broad superiority, SIGReg benefit, action-conditioning benefit,
or any locked-test claim.

## Metric Table

| Method | Seed | Aggregation | AUROC | AUPRC | F1 | Precision | Recall | Balanced accuracy | FPR@95TPR |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `frame_diff` |  |  | 0.500000 | 0.500000 | 0.666667 | 0.500000 | 1.000000 | 0.500000 | 1.000000 |
| `feature_distance` |  |  | 1.000000 | 1.000000 | 0.666667 | 0.500000 | 1.000000 | 0.500000 | 0.000000 |
| `video_autoencoder` |  |  | 1.000000 | 1.000000 | 0.666667 | 0.500000 | 1.000000 | 0.500000 | 0.000000 |
| `cnn_lstm` |  |  | 1.000000 | 1.000000 | 0.666667 | 0.500000 | 1.000000 | 0.500000 | 0.000000 |
| `video_transformer` |  |  | 1.000000 | 1.000000 | 0.666667 | 0.500000 | 1.000000 | 0.500000 | 0.000000 |
| `lewm` | `42` | `mean` | 0.500000 | 0.719150 | 0.400000 | 0.333333 | 0.500000 | 0.250000 | 1.000000 |
| `lewm` | `42` | `max` | 0.500000 | 0.719150 | 0.400000 | 0.333333 | 0.500000 | 0.250000 | 1.000000 |
| `lewm` | `43` | `mean` | 0.416667 | 0.663594 | 0.344828 | 0.294118 | 0.416667 | 0.208333 | 1.000000 |
| `lewm` | `43` | `max` | 0.416667 | 0.663594 | 0.344828 | 0.294118 | 0.416667 | 0.208333 | 1.000000 |
| `lewm` | `44` | `mean` | 0.500000 | 0.719150 | 0.400000 | 0.333333 | 0.500000 | 0.250000 | 1.000000 |
| `lewm` | `44` | `max` | 0.500000 | 0.719150 | 0.400000 | 0.333333 | 0.500000 | 0.250000 | 1.000000 |

## Readout

- Top AUROC rows are `feature_distance`, `video_autoencoder`, `cnn_lstm`, and
  `video_transformer`, all at AUROC `1.0`, AUPRC `1.0`, and FPR@95TPR `0.0`.
- The best recorded LeWM rows are seed42 `mean`, seed42 `max`, seed44 `mean`, and seed44 `max`,
  each at AUROC `0.5`.
- For LeWM `mean` aggregation across seed42/43/44, the seed-average AUROC is `0.472222` with
  population SD `0.039284`; AUPRC is `0.700631` with population SD `0.026189`.

## Interpretation Boundary

K2 is an honest negative comparison surface for LeWM on this bounded public benchmark. On this
validated split, the best simple baseline and every learned baseline rank above the recorded LeWM
rows. That does not license a broad "learned baselines beat LeWM generally" statement; it licenses
only a split-bounded report that this image-level synthetic-normal GlitchBench slice does not favor
the recorded LeWM configurations.

The thresholded classification metrics require a separate caution. Every AUROC `1.0` non-LeWM row
still reports F1 `0.666667`, precision `0.5`, recall `1.0`, and balanced accuracy `0.5` under the
shared train-normal `p95` threshold rule. This means K2 currently shows perfect ranking separation
for those methods on this tiny split, but not perfect threshold calibration.

## Allowed Claims

- The downloaded K2 scientific bundle is locally SHA256-verified and intake-validated.
- The K2 split is image-level, synthetic-normal, and leakage-audited with false locked-test flags.
- On this exact frozen split, `feature_distance` and all three learned baselines record AUROC
  `1.0`, while the best recorded LeWM rows reach AUROC `0.5`.
- This bounded benchmark therefore does not support a positive LeWM-vs-baseline claim on the K2
  GlitchBench slice.

## Rejected Claims

- LeWM is superior on GlitchBench.
- Learned baselines are broadly superior in gameplay glitch detection.
- K2 establishes temporal localization.
- K2 establishes natural-normal gameplay performance.
- K2 establishes cross-game generalization, SIGReg benefit, action-conditioning benefit, SOTA, or
  any locked-test conclusion.
