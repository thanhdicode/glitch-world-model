---
name: R5-WOB baseline_scores calibration episode count bug
description: validate_manifest_rows() default expected_calibration_episode_count=2 is wrong for WOB expansion protocol which has 12 calibration episodes.
---

## Rule
When calling `validate_manifest_rows()` from `run_gate8_baselines_from_lance.py`, always pass
`expected_calibration_episode_count=_WOB_CALIBRATION_EPISODE_COUNT` (= 12), not the bare default of 2.

## Why
The default value of 2 in `lewm_lance_eval.validate_manifest_rows()` was set for the TempGlitch
protocol. The WOB expansion eval manifest (`wob_expansion_eval_manifest.csv`) has 72 rows:
12 `calibration_normal` and 60 `evaluation_buggy`. Using the default caused the R5-WOB
`baseline_scores` stage to crash with `ValueError: invalid calibration episode count: 12.`

This was the only failure in the Kaggle run — Stages 1 (preflight) and 2 (materialize_lance)
both passed cleanly.

## How to apply
If `validate_manifest_rows` is ever called for a new protocol, check the manifest's
`evaluation_role == "calibration_normal"` count first and pass it explicitly.
Do NOT rely on the default `2` for anything other than the original TempGlitch 2-episode setup.
