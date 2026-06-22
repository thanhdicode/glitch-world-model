# R5-XGame Split Freeze

## VERIFIED

`configs/wob_protocol/r5_xgame_split.csv` was deterministically generated from `configs/wob_protocol/split.csv` by `scripts/freeze_r5_xgame_split.py`.

| Role | Label | Count |
| --- | --- | ---: |
| `train_normal` | Normal | 36 |
| `calibration_normal` | Normal | 12 |
| `evaluation_normal_negative` | Normal | 12 |
| `evaluation_buggy_positive` | Buggy | 60 |

The manifest uses only non-test source rows. The evaluation is class-imbalanced (12 normal / 60 buggy) because the available normal pool is small; rows were not duplicated or oversampled.

## BLOCKED

No `game_id` is available, so this is source-path/episode/pair disjoint rather than a demonstrated cross-game split. A future R5-XGame execution must retrain all three seeds on the frozen 36-row training set.
