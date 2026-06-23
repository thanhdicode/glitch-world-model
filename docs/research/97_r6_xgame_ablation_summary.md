# 97 - R6 XGame Ablation Summary

Date: 2026-06-23

## Scope

This summary uses the `60` already-recorded rows in `r5_xgame_comparison.csv`.

No new scoring, retraining, threshold search, or Kaggle run was performed.

## What Is Available

Available ablation axes in the validated bundle:

- LeWM seed: `42`, `43`, `44`
- window scorer variants:
  `lewm_mse_mean`, `lewm_mse_max`, `lewm_mse_top2_mean`,
  `lewm_l2_mean`, `lewm_l2_max`, `lewm_l2_top2_mean`
- episode aggregations:
  `mean`, `max`, `top2_mean`
- baseline methods:
  `frame_diff`, `feature_distance`
- threshold source:
  `calibration_normal_p95`

Not available in this bundle:

- temporal smoothing variants
- alternative calibration roles
- retraining-budget ablations
- SIGReg ablations
- action-conditioning ablations

## Seed-Level Stability

Best recorded row per LeWM seed:

| Seed | Best scorer | Best aggregation | Best AUROC | Mean AUROC across 18 rows | Population std |
| --- | --- | --- | ---: | ---: | ---: |
| `42` | `lewm_mse_top2_mean` | `top2_mean` | `0.7944` | `0.7678` | `0.0250` |
| `43` | `lewm_mse_max` | `max` | `0.8319` | `0.7736` | `0.0464` |
| `44` | `lewm_mse_max` | `top2_mean` | `0.9097` | `0.8610` | `0.0511` |

Bounded interpretation:

- seed `44` is the strongest seed in this validated bundle
- seeds `42` and `43` remain materially below seed `44`
- the bundle shows seed sensitivity, so the best row should not be rephrased as a stable
  all-seed average

## Aggregation Readout

Average AUROC across the `18` LeWM rows for each aggregation:

| Aggregation | Mean AUROC | Population std | Row count |
| --- | ---: | ---: | ---: |
| `mean` | `0.7478` | `0.0393` | `18` |
| `max` | `0.8272` | `0.0495` | `18` |
| `top2_mean` | `0.8275` | `0.0512` | `18` |

Bounded interpretation:

- `max` and `top2_mean` dominate `mean` on average within the recorded LeWM rows
- `max` and `top2_mean` are effectively tied at the level of this descriptive summary

## Scorer Readout

Average AUROC across `9` rows for each LeWM scorer variant:

| Window scorer | Mean AUROC | Population std | Best seed | Best aggregation | Best AUROC |
| --- | ---: | ---: | --- | --- | ---: |
| `lewm_mse_max` | `0.8207` | `0.0567` | `44` | `top2_mean` | `0.9097` |
| `lewm_l2_max` | `0.8150` | `0.0580` | `44` | `top2_mean` | `0.9097` |
| `lewm_mse_top2_mean` | `0.8032` | `0.0571` | `44` | `max` | `0.9000` |
| `lewm_l2_top2_mean` | `0.7931` | `0.0620` | `44` | `max` | `0.9000` |
| `lewm_mse_mean` | `0.7884` | `0.0558` | `44` | `top2_mean` | `0.8833` |
| `lewm_l2_mean` | `0.7846` | `0.0616` | `44` | `top2_mean` | `0.8917` |

## Threshold Contract

All `60` recorded rows use the same threshold policy:

- threshold source: `calibration_normal_p95`
- calibration support: `12` calibration-normal episodes

Observed threshold ranges:

- all recorded rows: `0.00694595618443` to `5.12809312344`
- `frame_diff`: `0.0144854433782` to `0.0481297982857`
- `feature_distance`: `0.0850248935794` to `0.172695526481`

The bundle supports threshold comparison only across already-recorded rows. It does not support a
new threshold sweep or a different calibration protocol without leaving the validated evidence
surface.
