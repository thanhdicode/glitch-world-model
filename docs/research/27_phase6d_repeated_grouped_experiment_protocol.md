# Phase 6D Repeated Grouped Experiment Protocol

## Objective

Phase 6D produces a fresh repeated grouped refit/scoring result package without using test
performance for scorer, aggregation, or threshold selection.

## Dataset And Subset Policy

- Dataset: public `asgaardlab/TempGlitch` Hugging Face artifact.
- Dataset revision: recorded in `data/raw/tempglitch_phase3b/metadata.csv`.
- Local inputs: the existing 100-video Phase 3B subset and its 5,572 preprocessed clips.
- Subset policy: fixed across all seeds so repeated results measure split/refit variability.
- Original sample mode: sequential. This remains a limitation; Phase 6D does not describe the
  subset as random-stratified or representative of the full benchmark.
- No raw videos, clips, generated manifests, scores, or result artifacts are committed.

## Repeated Split Policy

- Seeds: `42`, `43`, `44`, `45`, `46`.
- Grouping mode: `pair_id_heuristic`.
- Group key: TempGlitch category plus trailing numeric source index.
- Split ratios: train `0.6`, validation `0.2`, test `0.2`, assigned as whole groups.
- Required leakage condition: zero pair-suspect groups cross train, validation, or test.

## Fitting And Scoring Policy

- Scorers: `frame_diff`, `feature_distance`, `mini_latent`.
- `frame_diff`: no fitting.
- `feature_distance`: fit centroid using train-normal clips only.
- `mini_latent`: fit PCA encoder and transition model using train-normal clips only.
- Validation scores are generated for every scorer.
- Test scores are generated only for the single validation-selected scorer.
- Fit metadata records scorer, fit split, train sources used, train-normal clip count,
  validation source count, test source count, and whether labels were used for fitting.

## Model Selection Policy

- Aggregations: `mean`, `max`, `median`, `p90`, `p95`, `topk_mean`.
- `topk_mean` uses the top three clip scores.
- Each scorer/aggregation threshold is calibrated by best validation F1.
- The final scorer/aggregation is selected by validation AUROC.
- If every candidate validation AUROC is null, selection falls back to validation F1.
- Test metrics are unavailable to the selection function.

## Locked-Test And Uncertainty Policy

- Exactly one selected scorer/aggregation/fixed threshold is evaluated per seed.
- No ranked test candidate table is produced.
- Metrics: video-level AUROC, F1, precision, recall, accuracy, and confusion counts.
- Confidence intervals: `1,000` bootstrap samples, grouped by `pair_id_heuristic`,
  confidence level `0.95`, bootstrap seed equal to the split seed.
- AUROC bootstrap samples containing one class are skipped and counted honestly.
- Repeated summary reports arithmetic mean and population standard deviation across seeds.

## Commands

Dry-run split audit:

```powershell
python scripts\run_tempglitch_repeated_grouped_splits.py `
  --dry-run `
  --metadata data\raw\tempglitch_phase3b\metadata.csv `
  --manifest data\processed\tempglitch_phase3b\manifest.csv `
  --labels data\processed\tempglitch_phase3b\labels.csv `
  --output-root outputs\tempglitch_phase6d `
  --sample-mode sequential `
  --seeds 42 43 44 45 46
```

Full repeated refit/scoring:

```powershell
python scripts\run_tempglitch_repeated_grouped_splits.py `
  --metadata data\raw\tempglitch_phase3b\metadata.csv `
  --manifest data\processed\tempglitch_phase3b\manifest.csv `
  --labels data\processed\tempglitch_phase3b\labels.csv `
  --output-root outputs\tempglitch_phase6d `
  --sample-mode sequential `
  --seeds 42 43 44 45 46 `
  --scorer frame_diff `
  --scorer feature_distance `
  --scorer mini_latent `
  --aggregation mean max median p90 p95 topk_mean `
  --n-bootstrap 1000
```

## Claim Limitations

Phase 6D can support reproducibility claims about repeated pair-suspect grouped evaluation,
train-normal fitting, validation-only selection, single-config locked testing, and grouped
bootstrap confidence intervals.

Phase 6D cannot establish official pair identity, representative full-dataset performance,
temporal localization, mIoU, JEPA/SIGReg success, real LeWorldModel performance, state of the
art, or latent-dynamics superiority unless the repeated results themselves support the narrow
comparison.
