# 128 - K-B R5-XGame Final Intake

Date: 2026-06-29

## Scope

This note records the final local intake of the user-downloaded K-B / R5-XGame Kaggle output in
`C:\Users\ADMIN\Downloads\results K-B\r5_xgame`. It updates the repository context after the
successful K-B run and supersedes the earlier packaging-hash notes for the current downloaded
bundle. It does not describe a new Kaggle launch, retraining action, locked-test materialization,
or locked-test scoring.

## Validator Evidence

Commands run locally from the repository root:

```powershell
python scripts/validate_r5_xgame_output_bundle.py `
  --tarball "C:\Users\ADMIN\Downloads\results K-B\r5_xgame\r5_xgame_outputs.tar.gz" `
  --sha256-file "C:\Users\ADMIN\Downloads\results K-B\r5_xgame\r5_xgame_outputs.tar.gz.sha256" `
  --frozen-manifest configs/wob_protocol/r5_xgame_split.csv

python scripts/validate_r5_xgame_output_bundle.py `
  --output-dir "C:\Users\ADMIN\Downloads\results K-B\r5_xgame" `
  --frozen-manifest configs/wob_protocol/r5_xgame_split.csv
```

Both validations passed.

## Final Intake Status

- Output directory validator status: `r5_xgame_output_validated`
- Tarball/sidecar validator status: `r5_xgame_tarball_validated`
- Tarball SHA256:
  `e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`
- Metrics SHA256:
  `6ec94af80a40eeff718aefa285be870694eeadeaaefa6624babe3a5ee84f8474`
- Frozen manifest raw SHA256:
  `4f4b0ca5fe6e7ea207dd5a8f4ec97a0d00af486a109d2f215e9c83880c89182c`
- Bundle manifest raw SHA256:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`
- Normalized manifest SHA256 for both checked-in and bundle CSV content:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`
- `manifest_raw_sha256_match=false`
- `manifest_normalized_sha256_match=true`
- `stage_package_marker.has_legacy_tarball_record=false`
- `stage_package_marker.has_legacy_sidecar_record=false`
- `stage_package_marker.stale_legacy_tarball_sha256=false`

The raw manifest hash difference remains a Windows CRLF versus bundle LF line-ending difference;
the normalized CSV content matches.

## Frozen Support

The validated manifest has 120 rows:

- `train_normal=36`
- `calibration_normal=12`
- `evaluation_normal_negative=12`
- `evaluation_buggy_positive=60`

The evaluated binary support is 72 episodes:

- `normal-negative=12`
- `buggy-positive=60`

Safety flags from `r5_xgame_metrics.json` remain:

- `validation_buggy_used_for_fit_select=false`
- `locked_test_materialized=false`
- `locked_test_scored=false`

## Best Recorded Rows

Best LeWM row:

- seed: `44`
- method: `lewm`
- window scorer: `lewm_mse_max`
- episode aggregation: `top2_mean`
- AUROC: `0.909722222222`
- AUPRC: `0.981384073045`
- F1: `0.792079207921`
- precision: `0.975609756098`
- recall: `0.666666666667`
- balanced accuracy: `0.791666666667`
- FPR@95TPR: `0.416666666667`
- AUROC CI: `[0.828081597222, 0.971958502024]`
- F1 CI: `[0.696604787494, 0.873816747573]`

Best baseline row:

- method: `feature_distance`
- window scorer: `feature_distance`
- episode aggregation: `max`
- AUROC: `0.768055555556`
- AUPRC: `0.950909828866`
- F1: `0.688172043011`
- precision: `0.969696969697`
- recall: `0.533333333333`
- balanced accuracy: `0.725`
- FPR@95TPR: `1`
- AUROC CI: `[0.648436239919, 0.871851773953]`
- F1 CI: `[0.567748647524, 0.792461329254]`

## Safe Claim Boundary

Safe wording:

`R5-XGame provides bounded non-locked binary validation evidence on its frozen 12-normal-negative /
60-buggy-positive split. The best recorded LeWM configuration, seed44 with lewm_mse_max and
top2_mean aggregation, reached AUROC 0.909722 and AUPRC 0.981384.`

Required caveats:

- This is validation-only evidence.
- The split is positive-heavy and has only 12 normal-negative evaluation episodes.
- The AUROC confidence intervals for the best LeWM and best baseline rows overlap.
- This does not support SOTA, broad glitch-detection, cross-game generalization,
  action-conditioning benefit, or locked-test claims.

