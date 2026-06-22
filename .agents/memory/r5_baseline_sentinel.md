---
name: R5 baseline window_aggregation sentinel
description: The string "n/a" is a legitimate value for window_aggregation in R5 comparison CSVs for baseline scorers (frame_diff, feature_distance), not a placeholder.
---

## Rule
Do NOT add `"n/a"` or `"N/A"` to placeholder/forbidden-string sets when validating R5 or R6 ablation output files.

## Why
R5 comparison CSVs (`r5_comparison.csv`) use `window_aggregation = "n/a"` for baseline scorers (`baseline_frame_diff`, `baseline_feature_distance`) because baselines have no window-level aggregation parameter. This is a documented sentinel, not a missing value.

If a validator flags `"n/a"` as a placeholder, it will incorrectly mark all baseline rows as invalid.

## How to apply
In `validate_r6_ablations.py` and any future output validators, `_PLACEHOLDER_STRINGS` should contain only fabrication markers: `{"TODO", "TBD", "PLACEHOLDER", "—", "???"}`. Never include `"n/a"` or `"N/A"`.
