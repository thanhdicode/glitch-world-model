# R5-XGame Required Kaggle Inputs

R5-XGame is a fresh four-role World of Bugs validation run. It must not mount or reuse any old
R5-WOB seed artifacts, checkpoints, or output bundles.

## Required Kaggle Datasets

| Purpose | Kaggle dataset slug | Expected root under `/kaggle/input` | Required path pattern |
| --- | --- | --- | --- |
| Normal train/calibration/evaluation rows | `benedictwilkinsai/world-of-bugs-normal` | A mounted root containing `NORMAL-TRAIN/` | `NORMAL-TRAIN/ep-*/ep-*.tar` |
| Buggy validation-positive rows | `benedictwilkinsai/world-of-bugs-test` | A mounted root containing `TEST/` | `TEST/ep-*/ep-*.tar` |

The resolver also honors `NORMAL_INPUT_ROOT` and `TEST_INPUT_ROOT` environment overrides when a
Kaggle mount layout is unusual.

## Frozen Manifest Coverage

| Role | Label | Source root | Archive count | Used for |
| --- | --- | --- | ---: | --- |
| `train_normal` | Normal | `NORMAL-TRAIN/` | 36 | Fresh seed42/43/44 LeWM training only |
| `calibration_normal` | Normal | `NORMAL-TRAIN/` | 12 | Threshold calibration only |
| `evaluation_normal_negative` | Normal | `NORMAL-TRAIN/` | 12 | Binary evaluation negatives |
| `evaluation_buggy_positive` | Buggy | `TEST/` | 60 | Binary evaluation positives |

The 59 excluded WOB test rows are not needed. Locked test is not needed and must not be attached,
materialized, or scored.

## Kaggle Preflight Command

```bash
cd /kaggle/working/glitch-world-model
python scripts/run_r5_xgame_staged.py \
  --manifest configs/wob_protocol/r5_xgame_split.csv \
  --input-root /kaggle/input \
  --output-dir /kaggle/working/r5_xgame \
  --stage preflight
```

Expected success: `status` is `preflight_complete`, role counts are `36/12/12/60`, and every
`missing_count` is zero. If any old `r5_wob`, `wob_seed*_artifacts`, or checkpoint-looking dataset is
mounted, the run must stop before training.
