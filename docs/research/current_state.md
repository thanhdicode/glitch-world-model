# Current Research State

Date: 2026-06-30

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
- The staged `R5-XGame` runner, Kaggle launcher, and output-bundle validator exist in the repo,
  and the downloaded bundle now passes both `r5_xgame_output_validated` and
  `r5_xgame_tarball_validated`.
- The final K-B / `R5-XGame` tarball SHA256 is
  `e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`.
- `R5-XGame` now provides bounded non-locked binary validation evidence; the best recorded
  configuration reached AUROC `0.909722`, AUPRC `0.981384`, F1 `0.792079`, precision `0.975610`,
  recall `0.666667`, and balanced accuracy `0.791667`.
- The final K-B tarball and sidecar reflect the user-downloaded successful Kaggle output; no
  retraining, new Kaggle launch, or locked-test action was performed by local intake.
- The user-downloaded K-A expanded TempGlitch output is locally intake-reviewed as a
  non-locked, pair-disjoint validation artifact with 2 calibration-normal episodes and 67
  evaluation episodes (38 buggy-positive / 29 normal-negative), zero cross-role overlap, false
  locked-test flags, and best recorded LeWM AUROC `0.700544` / AUPRC `0.796566`.

## Blocked

- `R5-WOB` is not a valid binary benchmark because it has zero
  `evaluation_normal_negative` episodes.
- `R5-WOB` must not be used to claim AUROC, FPR@95TPR, binary discrimination, superiority, state
  of the art, cross-game generalization, temporal localization, action-conditioning benefit, or
  SIGReg benefit.
- The current `R5-XGame` evidence is bounded to a frozen, non-locked, positive-heavy evaluation
  split with only 12 normal-negative episodes, so it must not be promoted into broad
  generalization, superiority, state-of-the-art, or locked-test language.
- The expanded K-A TempGlitch evidence is auxiliary rather than headline evidence: AUROC is
  moderate, intervals remain wide, best LeWM FPR@95TPR is high, and no significance artifact was
  present in the downloaded folder.
- Locked test remains closed.

## Safe Wording

Use this wording for `R5-WOB` when a concise summary is needed:

`A provenance-bound non-locked positive-probe evaluation demonstrating pipeline execution and
class-conditional signal presence under a normal-calibrated threshold, but not yet a complete
binary benchmark.`

Use this wording for `R5-XGame` when a concise summary is needed:

`R5-XGame provides non-locked binary validation evidence that latent surprise scores separate
buggy-positive and normal-negative gameplay episodes, with the best recorded configuration
reaching AUROC approximately 0.91 on the frozen R5-XGame split.`

Use this wording for K-A expanded TempGlitch when a concise summary is needed:

`The expanded TempGlitch K-A follow-up increases the non-locked pair-disjoint evaluation support
to 67 episodes and records best LeWM AUROC approximately 0.70, above the best simple-baseline
AUROC approximately 0.63, while remaining an auxiliary result because uncertainty is wide and no
significance artifact is available.`

## Planned Next State

- Downstream work may cite the validated non-locked `R5-XGame` bundle with its limitation note,
  and may cite K-A expanded as auxiliary support-expansion evidence with its limitation note, but
  cross-source comparison, broad benchmark claims, and locked-test work remain closed.
