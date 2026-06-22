# R5-XGame Postrun Intake Template

Use this only after the Kaggle operator sends:

- `r5_xgame_outputs.tar.gz`
- `r5_xgame_outputs.tar.gz.sha256`
- Kaggle console log

## Local Validation Command

```powershell
python scripts/validate_r5_xgame_output_bundle.py `
  --tarball <download-dir>\r5_xgame_outputs.tar.gz `
  --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256 `
  --frozen-manifest configs\wob_protocol\r5_xgame_split.csv
```

Required validator status: `r5_xgame_tarball_validated`.

## Intake Checklist

- SHA256 sidecar matches the tarball.
- Frozen manifest hash matches `configs/wob_protocol/r5_xgame_split.csv`.
- Role counts are exactly 36 train-normal, 12 calibration-normal, 12 evaluation-normal-negative,
  and 60 evaluation-buggy-positive.
- Evaluation episode rows contain both normal and buggy labels.
- Stage markers through `stage_package.json` are present.
- Provenance says `locked_test_materialized=false`, `locked_test_scored=false`,
  `validation_buggy_used_for_fit_select=false`, and `old_r5_wob_checkpoint_reused=false`.

Do not update claims or paper tables until this checklist passes.
