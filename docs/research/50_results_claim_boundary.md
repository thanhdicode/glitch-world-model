# Gate 7-9 Result Claim Boundary

Status date: 2026-06-12

## Allowed

- The frozen Gate 6 v8 checkpoint produced finite MSE and L2 surprise scores for 10,081
  non-locked Lance windows.
- LeWM, frame difference, and train-normal-fitted feature distance were evaluated on the
  identical canonical manifest.
- On this one-buggy-episode window-level pilot, LeWM max aggregation had the highest observed
  AUROC/AUPRC among the evaluated scorers.
- The grouped normal-P95 operating point failed for LeWM, producing zero recall and F1.

## Required Qualification

Every metric statement must say that the evaluation is validation-only, window-level, based on
one buggy episode, and derived from a one-epoch 16-step checkpoint pilot. Windows are correlated
within episodes and do not provide independent sample evidence.

## Forbidden

- LeWM broadly detects gameplay glitches.
- LeWM is superior to baselines beyond this exact non-locked subset.
- The result is state of the art.
- SIGReg improves glitch detection.
- The method temporally localizes glitches.
- Any locked-test or final benchmark performance claim.

Gate 10 remains closed. Locked test was neither materialized nor scored.

## R3/R4 Training Artifact Boundary

Status date: 2026-06-17

R3/R4 checkpoint-training records are not detection metrics. They can support only bounded
training, checkpoint/reload, leakage-flag, early-stopping, and artifact-integrity statements that
are directly backed by recovered files or clearly scoped live logs.

No AUROC, AUPRC, F1, FPR-at-TPR, baseline-comparison, superiority, temporal-localization,
SIGReg-benefit, WOB-expansion, or locked-test claim is allowed until R5 produces identical-episode
validation scores and metrics under the frozen non-locked protocol.

Early-stopped training is valid only as training-gate evidence. It is not detection-performance
evidence, and it must be reported as early-stopped rather than as completion of all 15,000 target
optimizer updates.
