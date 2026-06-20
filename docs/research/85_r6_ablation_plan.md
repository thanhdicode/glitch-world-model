# 85 — R6 Ablation Plan

Date: 2026-06-20
Status: `SCAFFOLD_ONLY`

## Purpose

This document defines the R6 minimal decision-relevant ablation plan for both TempGlitch and
World of Bugs. TempGlitch CPU-safe work may be prepared from existing validated R5 inputs, but no
R6 item is executed in the current task. WOB items remain blocked until R5-WOB validates, and GPU
items remain separately gated. No ablation-result claim is made until validated outputs exist.

The machine-readable dependency queue is `configs/r6_ablation_queue.json`.

## Ablation Categories

### Category 1: CPU-Safe Ablations From Existing Score Files

These ablations reuse existing TempGlitch R5 raw scores and require no GPU. Their code and input
checks can be prepared now; execution remains a later explicit task.

| ID | Ablation | Question | Input | Compute |
|---|---|---|---|---|
| A1 | Aggregation | Is anomaly evidence sparse (mean vs max vs top2_mean)? | R5 comparison CSV | CPU |
| A2 | Surprise distance | Is ranking distance-sensitive (L2 vs cosine)? | R5 comparison CSV | CPU |
| A3 | Threshold calibration | What is the F1/FPR trade-off at various normal-calibrated thresholds? | R5 episode scores | CPU |
| A4 | Failure-mode analysis | Which categories/episodes fail and why? | R5 episode scores + labels | CPU |

### Category 2: Kaggle-Required Ablations

These require retraining or re-scoring on GPU and must run on Kaggle.

| ID | Ablation | Question | Compute | Prerequisite |
|---|---|---|---|---|
| A5 | SIGReg default vs zero | Does SIGReg change collapse/ranking? | Kaggle GPU | R5 complete |
| A6 | Training budget | Does additional optimization help (500 vs 3000 vs full)? | Kaggle GPU | R5 complete |

### Category 3: WOB-Specific Ablations

| ID | Ablation | Question | Compute | Prerequisite |
|---|---|---|---|---|
| A7 | WOB aggregation | Same as A1 but on WOB scores | CPU | R5-WOB validated |
| A8 | WOB surprise distance | Same as A2 but on WOB scores | CPU | R5-WOB validated |
| A9 | WOB threshold calibration | Same as A3 but on WOB scores | CPU | R5-WOB validated |
| A10 | WOB failure-mode analysis | Per-game failure analysis | CPU | R5-WOB validated |
| A11 | Action-conditioning | Zero-action vs real-action WOB comparison | Kaggle GPU | R5-WOB validated |

## Execution Order

1. **Prepare now, do not run**: A1-A4 CPU-safe TempGlitch input/runner checks.
2. **After R5-WOB ingestion**: A7-A10 CPU-safe WOB ablations become eligible.
3. **After validated R5-XGAME and a separate GPU decision**: A5-A6 may be considered.
4. **Last and separately gated**: A11 requires a frozen WOB zero-action protocol and training.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/run_r6_tempglitch_ablations.py` | TempGlitch ablation runner |
| `scripts/run_r6_wob_ablations.py` | WOB ablation runner |
| `scripts/validate_r6_ablations.py` | Validate ablation outputs |

## Claim Safety

- Do not claim SIGReg benefit until A5 produces repeated-seed evidence.
- Do not claim action-conditioning benefit until A11 produces controlled evidence.
- Do not claim any ablation result until the corresponding output file exists.
- Report negative results and limitations visibly.
- Locked test remains closed throughout R6.

## Paper Integration

Ablation results populate `paper/tables/r6_ablation_results.tex` only after validation.
The current paper table contains placeholders only.
