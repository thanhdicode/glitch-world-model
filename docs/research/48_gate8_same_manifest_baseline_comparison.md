# Gate 8 Same-Manifest Baseline Comparison

Status date: 2026-06-12
Result: `gate8_passed_same_manifest`

Gate 8 scored two baselines on exactly the Gate 7 canonical manifest. The scorer rejected
fingerprint, metadata, count, order, and `window_id` mismatches.

## Baselines

- `frame_diff`: mean absolute grayscale difference between adjacent frames in each four-frame
  window.
- `feature_distance`: Euclidean distance from a six-dimensional RGB mean/std centroid.

The feature centroid was fit only on the Gate 6 train-normal Lance dataset, whose fingerprint is
`3ffbcf221f6204e8f9d56d36c5f4495a1086288f62d885b06630e0458bec9d08`.

## Shared Evidence

- Window count: 10,081.
- Canonical manifest SHA-256:
  `c1b2971d259cf0cdc495c9b7b171d1bcb9f34d2c6c073e4bdd51cb60fcb00003`.
- Baseline scores SHA-256:
  `5a0e0df78e002d294c37d28d0e9ae47936ab16b2a74d8d2f99da486c6017e2de`.
- Gate 8 metadata SHA-256:
  `52370d3ab39b3d033c370df1dfb96d77bad077ff9eb8785c821a393e29fa0f2f`.
- Evaluation code Git SHA: `f22e1be92fed098752069616deb7ed2b26b8fcc1`.

Metrics are reported in Gate 9 because AUROC/AUPRC and the threshold protocol must be shared
across LeWM and baselines. Locked test was neither materialized nor scored.
