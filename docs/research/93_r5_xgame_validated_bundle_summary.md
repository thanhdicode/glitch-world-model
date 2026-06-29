# 93 - R5-XGame Validated Bundle Summary

Date: 2026-06-23

## Scope

This note closes the R5-XGame packaging/intake documentation gate. It records the validated
downloaded bundle after the packaging repair and does not describe a new scientific run.

## Intake Status

- Live output directory validator status:
  `r5_xgame_output_validated`
- Tarball/sidecar validator status:
  `r5_xgame_tarball_validated`
- Old tarball SHA256:
  `05d298c29904142d9e28db97e485db80b8b68eb56b520450594936593970fbd2`
- Final K-B tarball SHA256:
  `e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`
- Final K-B metrics SHA256:
  `6ec94af80a40eeff718aefa285be870694eeadeaaefa6624babe3a5ee84f8474`
- Packaging fix:
  `stage_package.json` is now snapshotted before tarball sealing, so the extracted tarball carries
  the same required stage marker as the live output directory.
- Reconciliation note:
  the 2026-06-29 user-downloaded K-B bundle validates with
  `stage_package_marker.has_legacy_tarball_record=false`,
  `stage_package_marker.has_legacy_sidecar_record=false`, and
  `stage_package_marker.stale_legacy_tarball_sha256=false`.
- Scientific-run status:
  unchanged. No retraining, no new Kaggle launch, and no locked-test access were introduced by the
  repair.

## Frozen Split And Seeds

- `train_normal=36`
- `calibration_normal=12`
- `evaluation_normal_negative=12`
- `evaluation_buggy_positive=60`
- Seeds:
  `42`, `43`, `44`

## Best Observed Non-Locked Validation Result

Best recorded configuration:

- seed `44`
- method `lewm`
- window scorer `lewm_mse_max`
- episode aggregation `top2_mean`

Best recorded metrics:

- AUROC approximately `0.9097`
- AUPRC approximately `0.9814`
- F1 approximately `0.7921`
- Precision approximately `0.9756`
- Recall approximately `0.6667`
- Balanced Accuracy approximately `0.7917`

## Safe Claim Boundary

Safe wording:

`R5-XGame provides non-locked binary validation evidence that latent surprise scores separate
buggy-positive and normal-negative gameplay episodes, with the best recorded configuration
reaching AUROC approximately 0.91 on the frozen R5-XGame split.`

Do not rewrite this evidence into:

- SOTA language
- solved glitch-detection language
- locked-test language
- broad cross-game generalization
- a final paper-grade benchmark claim

## Limitation Note

- Only 12 normal-negative evaluation episodes are present.
- The evaluation set is positive-heavy: 60 buggy-positive versus 12 normal-negative episodes.
- This is frozen non-locked validation evidence only.
- The result is not proof of broad generalization.

## Related Evidence

- [Package Fix Report](../../PACKAGE_FIX_REPORT.md)
- [Phase B R5-XGame Execution Report](phase_b_r5_xgame_execution_report.md)
- [R5-XGame Runbook](r5_xgame_runbook.md)
