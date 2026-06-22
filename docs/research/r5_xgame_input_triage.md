# R5-XGame Input Triage

## VERIFIED

- `configs/wob_protocol/split.csv` provides 179 real WOB metadata rows with `dataset_id`, `source`, `episode_id`, `pair_id`, `category`, `label`, and `split`.
- The candidate pool is 48 normal train rows, 12 normal validation rows, 60 buggy validation rows, and 59 buggy test rows.
- Episode IDs, pair IDs, and source paths are unique across the source split. No `game_id` exists; WOB source paths provide the available disjointness grouping.
- The 59 `test` rows are excluded from R5-XGame. Local raw materialization remains incomplete, so metadata readiness is not a permission to score locally.

## DECISION

The metadata is sufficient to freeze a real non-locked split. The prior R5-WOB checkpoints cannot be reused because they trained on all 48 original train-normal rows, including the 12 rows now held out as normal negatives. R5-XGame therefore requires new normal-only seed42/43/44 training on its frozen 36-row training partition.
