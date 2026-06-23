# Current Research State

Date: 2026-06-23

## Verified

- `R5-WOB` passed SHA256 verification and the repository offline intake validator as a
  provenance-bound non-locked output bundle.
- `R5-WOB` contains calibration-normal plus buggy-positive evidence and preserves
  `validation_buggy_used_for_fit_select=false`, `locked_test_materialized=false`, and
  `locked_test_scored=false`.
- `R5-WOB` proves pipeline execution and class-conditional signal presence under a
  normal-calibrated threshold.
- The `R5-XGame` four-role split is frozen and leakage-audited with 36 `train_normal`,
  12 `calibration_normal`, 12 `evaluation_normal_negative`, and 60
  `evaluation_buggy_positive` rows.
- The staged `R5-XGame` runner, Kaggle launcher, and output-bundle validator exist in the repo.
- Phase B / `R5-XGame` is the active scientific gate, and the external Kaggle run is treated as
  in progress until the downloaded bundle is validated locally.

## Blocked

- `R5-WOB` is not a valid binary benchmark because it has zero
  `evaluation_normal_negative` episodes.
- `R5-WOB` must not be used to claim AUROC, FPR@95TPR, binary discrimination, superiority, state
  of the art, cross-game generalization, temporal localization, action-conditioning benefit, or
  SIGReg benefit.
- No `R5-XGame` metric is claim-ready until `r5_xgame_outputs.tar.gz`,
  `r5_xgame_outputs.tar.gz.sha256`, and `r5_xgame_staged.log` pass local intake validation.
- Locked test remains closed.

## Safe Wording

Use this wording for `R5-WOB` when a concise summary is needed:

`A provenance-bound non-locked positive-probe evaluation demonstrating pipeline execution and
class-conditional signal presence under a normal-calibrated threshold, but not yet a complete
binary benchmark.`

## Planned Next State

- If Phase B intake passes, the repository may record valid non-locked binary metrics for
  `R5-XGame`.
- Until that intake passes, Phase C benchmark-prep work, Phase D ablation design, and Phase E
  paper scaffolding remain prep-only lanes.
