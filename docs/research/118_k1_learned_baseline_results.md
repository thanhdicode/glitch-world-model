# 118 - K1 Learned Baseline Results

Date: 2026-06-24
Status: validated bounded non-locked evidence

## Executive Verdict

K1 completed successfully and the downloaded bundle now validates locally.

Within the exact currently cited non-locked TempGlitch follow-up support, the strongest learned
baseline is `cnn_lstm` with `max` episode aggregation. Its AUROC matches the best simple-baseline
AUROC row numerically and remains below the best LeWM row. The paired AUROC delta versus the best
LeWM row crosses zero for the strongest learned baseline, so this is a bounded comparison study,
not a superiority claim.

## Artifact Validation Status

| Item | Status | Value |
| --- | --- | --- |
| Tarball SHA256 | matched | `3a1da8f8ef0e8ca8e78de317548664280e79d09e7ce95bd56d50e1c62133b74d` |
| Extract root | present | `outputs/learned_baselines_k1/learned_baselines_k1/` |
| Local validator | passed | `status=validated` |
| Train-normal clips | verified | `2167` |
| Validation clips | verified | `1898` |
| Locked-test materialized | false | validator-backed |
| Locked-test scored | false | validator-backed |

Local validation receipt SHA256:

- `ab5187a9636c347c9b7a97d5c1b5b9ef2eea34cd27c978b7a92166e2edbb9a64`

## Canonical Support

All learned-baseline rows below use the same existing bounded TempGlitch follow-up support:

- calibration normals:
  - `Godot_Blinking_Normal_106`
  - `Godot_Frozen_Animation_Platformer_Normal_107`
- evaluation normal-negative episodes: `12`
- evaluation buggy-positive episodes: `22`
- evaluation total: `34`

## Best Learned Row Per Method

| Method | Best aggregation | AUROC | AUPRC | F1 | Precision | Recall | Balanced accuracy | FPR@95TPR | AUROC 95% CI | F1 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `video_autoencoder` | `mean` | `0.560606` | `0.700532` | `0.681818` | `0.681818` | `0.681818` | `0.549242` | `0.833333` | `[0.390890, 0.738636]` | `[0.555556, 0.790698]` |
| `cnn_lstm` | `max` | `0.613636` | `0.724853` | `0.711111` | `0.695652` | `0.727273` | `0.571970` | `0.916667` | `[0.440455, 0.800041]` | `[0.594595, 0.816327]` |
| `video_transformer` | `mean` | `0.590909` | `0.775551` | `0.240000` | `1.000000` | `0.136364` | `0.568182` | `1.000000` | `[0.461515, 0.727273]` | `[0.000000, 0.428571]` |

## Comparison Anchors

| Comparator | Configuration | AUROC | AUPRC | F1 | Precision | Recall | Balanced accuracy | FPR@95TPR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Best LeWM row | seed44 `lewm_l2_max` + episode `mean` | `0.715909` | `0.802619` | `0.714286` | `0.750000` | `0.681818` | `0.632576` | `0.750000` |
| LeWM seed aggregate | `lewm_l2_max` + episode `mean`, seeds42/43/44 mean | `0.606061` | `0.729142` | `0.732063` | `0.730952` | `0.742424` | `0.607323` | `0.888889` |
| Best `frame_diff` row | episode `mean` | `0.583333` | `0.721564` | `0.615385` | `0.705882` | `0.545455` | `0.564394` | `0.750000` |
| Best `feature_distance` row | episode `top2_mean` | `0.613636` | `0.731004` | `0.160000` | `0.666667` | `0.090909` | `0.503788` | `0.833333` |
| Best learned baseline | `cnn_lstm` + episode `max` | `0.613636` | `0.724853` | `0.711111` | `0.695652` | `0.727273` | `0.571970` | `0.916667` |

## Paired Comparison Against The Best LeWM Row

All paired deltas use the exact same evaluation episodes and group the bootstrap by `pair_id`.

| Learned baseline | Best aggregation | Delta AUROC vs best LeWM | Delta AUPRC vs best LeWM | DeLong p-value |
| --- | --- | --- | --- | ---: |
| `video_autoencoder` | `mean` | `-0.155303` with 95% CI `[-0.312500, -0.012371]` | `-0.102087` with 95% CI `[-0.206929, -0.014794]` | `0.072595` |
| `cnn_lstm` | `max` | `-0.102273` with 95% CI `[-0.242451, 0.037207]` | `-0.077766` with 95% CI `[-0.189327, 0.023819]` | `0.209116` |
| `video_transformer` | `mean` | `-0.125000` with 95% CI `[-0.379870, 0.154545]` | `-0.027068` with 95% CI `[-0.237167, 0.152674]` | `0.445361` |

Interpretation:

- best LeWM remains the strongest observed row on this split
- best learned-baseline AUROC does not exceed the best LeWM AUROC
- the strongest learned baseline does not show a non-overlapping paired AUROC advantage over LeWM

## Best Learned Baseline Versus Simple Baselines

Using `cnn_lstm` + episode `max` as the strongest learned row:

- versus `frame_diff` + episode `mean`:
  - delta AUROC `0.030303`, 95% CI `[-0.122744, 0.198875]`, DeLong `p=0.730589`
- versus `feature_distance` + episode `top2_mean`:
  - delta AUROC `0.000000`, 95% CI `[-0.256233, 0.227348]`, DeLong `p=1.000000`

This supports a narrow statement that the best learned baseline is competitive with the recorded
simple baselines on this split, not that it clearly dominates them.

## Allowed Claims

- The K1 learned-baseline Kaggle run completed successfully and its downloaded bundle validates
  locally.
- All three learned baselines are now scored on the exact currently cited bounded TempGlitch
  follow-up support.
- The strongest learned baseline is `cnn_lstm` with `max` aggregation at AUROC `0.613636`.
- The best LeWM row remains higher than the best learned-baseline row on this split.
- The strongest learned baseline is competitive with the recorded simple baselines on this split.

## Rejected Claims

- state of the art
- broad superiority
- cross-game generalization
- temporal localization
- SIGReg benefit
- action-conditioning benefit
- any locked-test performance statement

## Paper-Safe Wording

> On the current frozen non-locked TempGlitch follow-up support, the strongest learned baseline is
> CNN-LSTM with max episode aggregation. Its AUROC is below the best LeWM row and numerically
> matches the best simple-baseline AUROC row, so the result supports a bounded comparison rather
> than a broad superiority claim.

## Analysis Artifact Hashes

| Artifact | SHA256 |
| --- | --- |
| `k1_followup_episode_scores.csv` | `f610f648d425df699c41e3707d7067486e18c186a799bfabd2f4bd265af87fe7` |
| `k1_followup_comparison.csv` | `4702efa7f243cab1252314cd73926e1376c53e6dfbe50369caffd0cefbb3b748` |
| `k1_followup_summary.json` | `969c4c210d73d3971fb15fbf8f3d84584b729209a8b79865521ce0ae758fdbeb` |
| `K1_FOLLOWUP_REPORT.md` | `14de2db17eab27526a9ceaca6615cacb570da2d74d93e8492d97961934abb7be` |

## Next Action

Phase P2 is now artifact-backed. The next V4 action is Phase P3 local GlitchBench preparation,
followed by the user-operated Kaggle K2 gate.
