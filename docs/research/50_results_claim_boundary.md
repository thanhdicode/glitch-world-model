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
