# R5-XGame Required Kaggle Inputs

## Required Mounted Roots

- Attach Kaggle dataset `benedictwilkinsai/world-of-bugs-normal`, expected below `/kaggle/input/.../NORMAL-TRAIN/`.
- Attach Kaggle dataset `benedictwilkinsai/world-of-bugs-test`, expected below `/kaggle/input/.../TEST/`.

## Role Resolution

| Role | Root | Archive count |
| --- | --- | ---: |
| train-normal | normal | 36 |
| calibration-normal | normal | 12 |
| evaluation-normal-negative | normal | 12 |
| evaluation-buggy-positive | test dataset, validation rows only | 60 |

The frozen manifest excludes all 59 WOB `test` rows. Locked-test inputs are neither required nor
permitted. Fresh checkpoints are outputs of the future Kaggle run, not mounted inputs; old
R5-WOB artifacts must not be attached.

## Kaggle Preflight

```bash
python scripts/run_r5_xgame_staged.py --manifest configs/wob_protocol/r5_xgame_split.csv --input-root /kaggle/input --stage preflight
```
