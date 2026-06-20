# 90 — R6 TempGlitch CPU-Safe Ablation Plan and Runner

Date: 2026-06-20
Status: `INFRASTRUCTURE_READY — PENDING_R5_OUTPUT_FILES`

## Purpose

This note documents the R6 CPU-safe TempGlitch ablation infrastructure (A1–A4).
All four ablations reuse files produced by the R5 identical-episode evaluation and
require no GPU. The scripts are implemented and tested. Execution is blocked until
the R5 TempGlitch output directory is locally present.

R5-WOB, R5-XGAME, R6 WOB ablations (A7–A11), and locked test remain separately gated.

## Ablation Summary

| ID | Name | Compute | Input | Status |
|---|---|---|---|---|
| A1 | Aggregation comparison | CPU | `r5_comparison.csv` | PREPARABLE — script ready |
| A2 | Surprise-distance comparison | CPU | `r5_comparison.csv` | PREPARABLE — cosine NOT_AVAILABLE |
| A3 | Threshold calibration summary | CPU | `r5_comparison.csv` | PREPARABLE — full sweep needs extra R5 output |
| A4 | Failure-mode analysis | CPU | `r5_episode_manifest.csv`, `r5_comparison.csv` | PREPARABLE — per-episode FP/FN needs extra R5 output |
| A5 | SIGReg ablation | Kaggle GPU | R5-XGAME validated | BLOCKED |
| A6 | Training budget | Kaggle GPU | R5-XGAME validated | BLOCKED |
| A7–A10 | WOB CPU ablations | CPU | validated R5-WOB receipt | BLOCKED_R5_WOB_VALIDATION |
| A11 | WOB action-conditioning | Kaggle GPU | validated R5-WOB + frozen zero-action protocol | BLOCKED |

## Required R5 Input Files

The following files must be present in the R5 TempGlitch output directory
(`outputs/r5_tempglitch_identical_episode/` by default):

| File | Purpose |
|---|---|
| `r5_comparison.csv` | Per-scorer metrics (AUROC, AUPRC, F1, threshold, CI bounds) |
| `r5_episode_manifest.csv` | Episode-level manifest with category and label fields |
| `r5_episode_eval.json` *(optional)* | Full eval JSON with calibration episode counts |

These are produced by:
```bash
python scripts/run_r5_tempglitch_identical_episode_evaluation.py \
    --train-lance <path> \
    --validation-normal-lance <path> \
    --validation-buggy-lance <path> \
    --seed-artifact-root seed42:<path> \
    --seed-artifact-root seed43:<path> \
    --seed-artifact-root seed44:<path> \
    --output-dir outputs/r5_tempglitch_identical_episode
```

## A1 — Aggregation Comparison

**Question**: Is anomaly evidence sparse (max aggregation picks up one extreme window)
versus diffuse (mean aggregation integrates across all windows)?

**Method**: Groups all rows in `r5_comparison.csv` by `episode_aggregation` (max / mean)
and by `window_aggregation` (mse_max / mse_mean / l2_max / l2_mean). Reports mean AUROC,
mean AUPRC, max AUROC, and mean F1 per group. Also reports the best individual configuration
by AUROC and by AUPRC.

**Output**: `r6_a1_aggregation_ablation.json`

## A2 — Surprise-Distance Comparison

**Question**: Is the MSE distance metric or the L2 distance metric more informative for
detecting glitch-type transitions?

**Method**: Groups rows by window aggregation family:
- MSE family: `mse_max`, `mse_mean`
- L2 family: `l2_max`, `l2_mean`
- Cosine: **NOT_AVAILABLE_FROM_CURRENT_ARTIFACTS** — cosine surprise distance was not
  computed during R5; current score CSVs contain only `mse_t{1,2,3}` and `l2_t{1,2,3}`.

Baselines (`frame_diff`, `feature_distance`) are reported separately for reference.

**Output**: `r6_a2_surprise_distance_ablation.json`

## A3 — Threshold Calibration Summary

**Question**: What is the F1/FPR trade-off at the existing calibration threshold?

**Method**: Reports stored `calibration_normal_P95` threshold, F1, precision, recall,
and FPR@95TPR for every configuration in the comparison CSV. A full multi-point threshold
sweep would require per-episode raw scores, which are not saved in the current R5 artifact
family. The output marks `sweep_complete=False` and lists what is missing for a full sweep.

**Output**: `r6_a3_threshold_calibration_ablation.json`

**To enable full sweep**: Re-run R5 eval with a `--save-episode-scores` flag (not yet
implemented in the R5 runner).

## A4 — Failure-Mode Analysis

**Question**: Which TempGlitch categories or episodes are detected well or poorly?

**Method**: Groups episode manifest rows by `category` field and reports normal/buggy
episode counts per category. Flags categories with no buggy or no normal coverage.
Reports best and worst F1 LeWM configurations from the comparison CSV. Per-episode
false-positive/false-negative breakdown is not available because per-episode predictions
are not saved in the current R5 artifact family.

**Output**: `r6_a4_failure_mode_ablation.json`

## How to Run

### All ablations (A1–A4):
```bash
python scripts/run_r6_tempglitch_cpu_ablations.py \
    --r5-output-dir outputs/r5_tempglitch_identical_episode \
    --output-dir outputs/r6_tempglitch_ablations \
    --ablation all
```

### Single ablation:
```bash
python scripts/run_r6_tempglitch_cpu_ablations.py \
    --r5-output-dir outputs/r5_tempglitch_identical_episode \
    --output-dir outputs/r6_tempglitch_ablations \
    --ablation a1
```

## How to Validate

```bash
python scripts/validate_r6_ablations.py \
    --output-dir outputs/r6_tempglitch_ablations
```

## Claim Safety

All A1–A4 results are from the **non-locked R5 TempGlitch validation family only**.

The following claims are **not supported** by A1–A4 outputs:
- SIGReg benefit (requires A5 with repeated-seed GPU evidence)
- Action-conditioning benefit (requires A11 with controlled zero-vs-real-action evidence)
- WOB or cross-game generalization (requires validated R5-WOB receipt)
- Temporal localization performance
- State of the art or superiority
- Locked-test performance

Negative results and limitations must be reported visibly alongside any positive findings.

## Limitations

1. **Wide bootstrap CIs**: R5 used only 2 calibration-normal episodes and 34 evaluation
   episodes. Ablation differences between aggregation modes may be within CI overlap.
2. **Cosine not available**: Cosine surprise distance was not computed in R5; it cannot
   be derived from saved artifacts.
3. **No per-episode predictions**: A3 threshold sweep is single-point only; A4
   failure-mode analysis is category-level only.
4. **Non-locked validation only**: All metrics are from the validation split.
   Locked test remains closed.

## Paper Integration

Ablation results populate `paper/tables/r6_ablation_results.tex` only after:
1. The script runs successfully on the locally present R5 output directory.
2. `validate_r6_ablations.py` passes with `valid=True`.
3. No placeholder or fabricated metric is present in any output file.
