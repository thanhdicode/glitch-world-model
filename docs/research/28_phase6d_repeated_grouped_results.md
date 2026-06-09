# Phase 6D Repeated Grouped Results

## Status

Full repeated grouped refit/scoring completed for seeds `42`, `43`, `44`, `45`, and `46`.
Every seed refit the train-dependent scorers, selected one scorer/aggregation on validation,
and evaluated exactly that selected configuration on test.

This is the first complete Phase 6D protocol-hardened result package. It is suitable as a
reproducibility and diagnostic result, but it is not a fully untouched final benchmark result:
the fixed 100-video subset was originally sampled sequentially and its videos were inspected in
earlier phases.

## Inputs And Policy

- Public artifact: `asgaardlab/TempGlitch`
- Dataset revision: `1d46a63c31ebfe3b675b51a2231d547da372eff9`
- Fixed local subset: `100` videos and `5,572` clips
- Original subset sample mode: sequential
- Grouping: `pair_id_heuristic`
- Scorers: `frame_diff`, `feature_distance`, `mini_latent`
- Aggregations: `mean`, `max`, `median`, `p90`, `p95`, `topk_mean`
- Selection: validation AUROC, fallback validation F1
- Threshold: best validation F1 for each candidate
- Locked test: one validation-selected configuration per seed
- Bootstrap: `1,000` samples per metric and seed, grouped by `pair_id_heuristic`

## Split And Fitting Audit

| Seed | Train videos | Validation videos | Test videos | Cross-split groups | Train-normal sources | Train-normal clips |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 42 | 62 | 18 | 20 | 0 | 31 | 1,724 |
| 43 | 60 | 21 | 19 | 0 | 31 | 1,785 |
| 44 | 62 | 19 | 19 | 0 | 31 | 1,809 |
| 45 | 63 | 19 | 18 | 0 | 31 | 1,752 |
| 46 | 61 | 19 | 20 | 0 | 32 | 1,928 |

`feature_distance` and `mini_latent` used only the train-normal sources and clips shown above.
`frame_diff` required no fitting. Validation and test sources were excluded from fitting.

## Validation Selection And Locked Test

Each seed compared `18` scorer/aggregation candidates on validation before test scoring.

| Seed | Validation-selected config | Validation AUROC | Locked-test AUROC | Locked-test F1 |
| ---: | --- | ---: | ---: | ---: |
| 42 | `mini_latent/p95` | `0.580247` | `0.620000` | `0.642857` |
| 43 | `mini_latent/p95` | `0.736364` | `0.647727` | `0.526316` |
| 44 | `mini_latent/p90` | `0.704545` | `0.681818` | `0.600000` |
| 45 | `feature_distance/median` | `0.750000` | `0.350649` | `0.500000` |
| 46 | `mini_latent/p90` | `0.644444` | `0.565657` | `0.545455` |

Repeated selected-pipeline result:

- Locked-test AUROC: `0.573170 +/- 0.117582` population standard deviation
- Locked-test F1: `0.562925 +/- 0.051708` population standard deviation

## Pair-Grouped Bootstrap Confidence Intervals

| Seed | AUROC 95% CI | F1 95% CI |
| ---: | --- | --- |
| 42 | `[0.400000, 0.823177]` | `[0.521739, 0.740741]` |
| 43 | `[0.347173, 0.897784]` | `[0.235294, 0.777778]` |
| 44 | `[0.393813, 0.895937]` | `[0.315587, 0.833553]` |
| 45 | `[0.127273, 0.509288]` | `[0.300000, 0.642857]` |
| 46 | `[0.342593, 0.766667]` | `[0.300000, 0.740972]` |

Every AUROC interval includes `0.5`. The wide intervals and seed-to-seed variation show that
the fixed 100-video subset does not support a strong above-chance or superiority claim.

## Interpretation And Claim Decision

The validation selector chose `mini_latent` in four of five seeds, but Phase 6D evaluates only
the selected pipeline on locked test. It does not produce test comparisons for every scorer in
every seed, so it cannot establish `mini_latent` or latent-dynamics superiority.

The selected pipeline has mean AUROC above `0.5`, but the variation is high and one seed falls
well below chance. The result supports the protocol implementation and a diagnostic short-paper
framing, not a performance-superiority claim.

## Generated Artifact Paths

Generated artifacts remain gitignored:

- `outputs/tempglitch_phase6d/seed_42/` through `seed_46/`
- `outputs/tempglitch_phase6d/phase6d_repeated_summary.json`
- `outputs/tempglitch_phase6d/phase6d_repeated_summary.md`

## Remaining Limitations

- `pair_id_heuristic` is not an official pair ID.
- The fixed subset was originally sampled sequentially, not random-stratified.
- The same 100 videos were inspected in earlier exploratory phases.
- The result estimates selected-pipeline performance, not per-scorer superiority.
- Public labels remain binary per video; temporal localization and mIoU are unsupported.
- Real LeWorldModel, JEPA, and SIGReg are not implemented or evaluated.
