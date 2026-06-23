# 96 - R6 XGame Bounded Comparison

Date: 2026-06-23

## Scope

This comparison uses only `r5_xgame_comparison.csv` from the validated non-locked `R5-XGame`
bundle.

Every row below is bounded to the same frozen evaluation support:

- total evaluation episodes: `72`
- buggy-positive episodes: `60`
- normal-negative episodes: `12`
- threshold source for every compared row: `calibration_normal_p95`

## Best Recorded Rows Within The Frozen Split

| Family | Config | AUROC | AUPRC | F1 | Precision | Recall | Balanced Accuracy | FPR@95TPR | AUROC CI | F1 CI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `lewm` | seed `44`, `lewm_mse_max`, `top2_mean` | `0.9097` | `0.9814` | `0.7921` | `0.9756` | `0.6667` | `0.7917` | `0.4167` | `[0.8281, 0.9720]` | `[0.6966, 0.8738]` |
| `feature_distance` | `max` | `0.7681` | `0.9509` | `0.6882` | `0.9697` | `0.5333` | `0.7250` | `1.0000` | `[0.6484, 0.8719]` | `[0.5677, 0.7925]` |
| `frame_diff` | `max` | `0.7167` | `0.9381` | `0.6593` | `0.9677` | `0.5000` | `0.7083` | `0.9167` | `[0.5812, 0.8339]` | `[0.5434, 0.7600]` |

## Bounded Readout

Within this frozen non-locked split:

- the best recorded LeWM row exceeds the best recorded baseline rows on AUROC, AUPRC, F1, recall,
  balanced accuracy, and FPR@95TPR
- the best baseline remains `feature_distance`, not `frame_diff`
- the AUROC confidence intervals still overlap, so this comparison supports a bounded ranking
  difference inside this split, not a broad superiority claim

## Family-Level Support Counts

Compared rows available in the validated bundle:

| Family | Compared rows | Support per row |
| --- | ---: | --- |
| `lewm` | `54` | `72` episodes = `60` buggy-positive + `12` normal-negative |
| `feature_distance` | `3` | same frozen support |
| `frame_diff` | `3` | same frozen support |

Average AUROC across all recorded rows in each family:

| Family | Mean AUROC across recorded rows |
| --- | ---: |
| `lewm` | `0.8008` |
| `feature_distance` | `0.7426` |
| `frame_diff` | `0.6704` |

This average is descriptive only. It does not replace the frozen best-row comparison and does not
justify a broad family-level claim.

## Category-Limit Note

The validated `category` field is single-valued:

- unique category count: `1`
- category value: `world_of_bugs`

That means the current bundle supports split-level comparison, but not a meaningful multi-category
contrast within the validated `category` field.
