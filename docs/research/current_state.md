# Current Research State

Date: 2026-06-22

## VERIFIED

- The downloaded R5-WOB success bundle passed SHA256 verification and the repository offline intake validator: bundle SHA256 `6b08c2cf07ed71a55f71fb0e288a445f460309b98f479e21eba13f8722ba2274`.
- The bundle contains the seven core intake artifacts. The frozen evaluation manifest hash is `f7dbd85876809a1c2437cf5827ce4c27f289078ca0904ed70c1d75908a1bcec6` and contains 12 calibration-normal plus 60 evaluation-buggy episodes.
- All staged R5-WOB phases are reported complete in the supplied Kaggle log. Direct intake validation confirms seeds 42/43/44, `frame_diff`, and `feature_distance` are present.
- `validation_buggy_used_for_fit_select=false`, `locked_test_materialized=false`, and `locked_test_scored=false`.

## INFERRED

- Seed-level calibrated positive-probe F1 varies materially; this warrants seed-aware reporting rather than a single-seed narrative.

## BLOCKED

- R5-WOB has zero normal evaluation negatives. AUROC and FPR@95TPR are therefore unavailable, and AUPRC=1 is not a meaningful binary-benchmark result.
- Cross-game/source generalization, method superiority, action-conditioning benefit, and locked-test results remain unproven.

## PLANNED

- R5-XGame will require disjoint train-normal, calibration-normal, evaluation-normal-negative, and evaluation-buggy-positive groups before live scoring.
