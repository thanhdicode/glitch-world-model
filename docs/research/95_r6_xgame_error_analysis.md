# 95 - R6 XGame Error Analysis

Date: 2026-06-23

## Scope

This analysis uses only the validated downloaded `R5-XGame` bundle at:

`C:\Users\ADMIN\Downloads\results (1)\r5_xgame`

The detailed error review is anchored to the validated best recorded configuration:

- method family: `lewm`
- method: `lewm`
- window scorer: `lewm_mse_max`
- seed: `44`
- episode aggregation: `top2_mean`
- threshold: `0.10253587123`
- threshold source: `calibration_normal_p95`

Support counts for this bounded evaluation:

- total evaluation episodes: `72`
- buggy-positive episodes: `60`
- normal-negative episodes: `12`

## Confusion Summary

For the best recorded bounded row:

- true positives: `40`
- true negatives: `11`
- false negatives: `20`
- false positives: `1`

This matches the recorded precision/recall pattern:

- precision approximately `0.9756`
- recall approximately `0.6667`
- F1 approximately `0.7921`

## False Positive Summary

Observed false positives: `1 / 12` normal-negative episodes.

| Episode ID | Source | Score | Threshold | Prediction |
| --- | --- | ---: | ---: | --- |
| `normal/ep-0054` | `NORMAL-TRAIN/ep-0054/ep-0054.tar` | `0.103498` | `0.102536` | `Buggy` |

Interpretation:

- the only false positive sits extremely close to the threshold
- this supports a threshold-sensitivity explanation
- the evidence does not support a stronger causal claim than “near-threshold normal episode”

## False Negative Summary

Observed false negatives: `20 / 60` buggy-positive episodes.

By source-path prefix:

| Prefix | False negatives |
| --- | ---: |
| `TextureCorruption` | `5` |
| `ZClipping` | `5` |
| `ScreenTear` | `4` |
| `ZFighting` | `4` |
| `TextureMissing` | `2` |

The false negatives are:

| Episode ID | Source | Score | Threshold | Prediction | Error type |
| --- | --- | ---: | ---: | --- | --- |
| `ScreenTear/ep-0000` | `TEST/ScreenTear/ep-0000/ep-0000.tar` | `0.089855` | `0.102536` | `Normal` | `false_negative` |
| `ScreenTear/ep-0002` | `TEST/ScreenTear/ep-0002/ep-0002.tar` | `0.077869` | `0.102536` | `Normal` | `false_negative` |
| `ScreenTear/ep-0004` | `TEST/ScreenTear/ep-0004/ep-0004.tar` | `0.094389` | `0.102536` | `Normal` | `false_negative` |
| `ScreenTear/ep-0008` | `TEST/ScreenTear/ep-0008/ep-0008.tar` | `0.088718` | `0.102536` | `Normal` | `false_negative` |
| `TextureCorruption/ep-0000` | `TEST/TextureCorruption/ep-0000/ep-0000.tar` | `0.082363` | `0.102536` | `Normal` | `false_negative` |
| `TextureCorruption/ep-0001` | `TEST/TextureCorruption/ep-0001/ep-0001.tar` | `0.090665` | `0.102536` | `Normal` | `false_negative` |
| `TextureCorruption/ep-0003` | `TEST/TextureCorruption/ep-0003/ep-0003.tar` | `0.071379` | `0.102536` | `Normal` | `false_negative` |
| `TextureCorruption/ep-0004` | `TEST/TextureCorruption/ep-0004/ep-0004.tar` | `0.088842` | `0.102536` | `Normal` | `false_negative` |
| `TextureCorruption/ep-0005` | `TEST/TextureCorruption/ep-0005/ep-0005.tar` | `0.074592` | `0.102536` | `Normal` | `false_negative` |
| `TextureMissing/ep-0003` | `TEST/TextureMissing/ep-0003/ep-0003.tar` | `0.074019` | `0.102536` | `Normal` | `false_negative` |
| `TextureMissing/ep-0007` | `TEST/TextureMissing/ep-0007/ep-0007.tar` | `0.090816` | `0.102536` | `Normal` | `false_negative` |
| `ZClipping/ep-0000` | `TEST/ZClipping/ep-0000/ep-0000.tar` | `0.069212` | `0.102536` | `Normal` | `false_negative` |
| `ZClipping/ep-0004` | `TEST/ZClipping/ep-0004/ep-0004.tar` | `0.085939` | `0.102536` | `Normal` | `false_negative` |
| `ZClipping/ep-0006` | `TEST/ZClipping/ep-0006/ep-0006.tar` | `0.066537` | `0.102536` | `Normal` | `false_negative` |
| `ZClipping/ep-0007` | `TEST/ZClipping/ep-0007/ep-0007.tar` | `0.060621` | `0.102536` | `Normal` | `false_negative` |
| `ZClipping/ep-0008` | `TEST/ZClipping/ep-0008/ep-0008.tar` | `0.077852` | `0.102536` | `Normal` | `false_negative` |
| `ZFighting/ep-0000` | `TEST/ZFighting/ep-0000/ep-0000.tar` | `0.082027` | `0.102536` | `Normal` | `false_negative` |
| `ZFighting/ep-0004` | `TEST/ZFighting/ep-0004/ep-0004.tar` | `0.093883` | `0.102536` | `Normal` | `false_negative` |
| `ZFighting/ep-0005` | `TEST/ZFighting/ep-0005/ep-0005.tar` | `0.059527` | `0.102536` | `Normal` | `false_negative` |
| `ZFighting/ep-0008` | `TEST/ZFighting/ep-0008/ep-0008.tar` | `0.074850` | `0.102536` | `Normal` | `false_negative` |

## Bounded Interpretation

Supported:

- within the frozen non-locked split, the best recorded row is much more recall-limited than
  precision-limited
- the error mass is dominated by false negatives, not false positives
- the misses cluster in a subset of source-path families rather than being evenly spread across all
  buggy-positive episodes

Not supported:

- a root-cause explanation for why those source-path families are harder
- any cross-game or locked-test conclusion
- any temporal-localization conclusion
