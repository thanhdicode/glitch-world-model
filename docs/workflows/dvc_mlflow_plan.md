# DVC and MLflow Plan

## Purpose

DVC and MLflow are optional future tools for experiment reproducibility. They are documented now so the project can adopt them safely later without committing raw datasets or requiring cloud services.

## DVC policy

- DVC is for data and pipeline reproducibility.
- Do not run `dvc add` on raw datasets until source URL, license, access date, and allowed use are verified.
- Keep DVC cache out of git.
- Do not require DVC in core CI.
- Prefer small smoke-test subsets before tracking any large artifact.

## Proposed future DVC stages

| Stage | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `preprocess_tempglitch` | Convert verified TempGlitch source data to clip manifests | raw videos/frames, converted labels | `data/processed/tempglitch/manifest.csv` |
| `score_frame_diff` | Run frame-difference baseline | manifest | `outputs/tempglitch_frame_diff_scores.csv` |
| `score_feature_distance` | Run feature-distance baseline | manifest, labels | `outputs/tempglitch_feature_distance_scores.csv` |
| `score_mini_latent` | Run mini latent baseline | manifest, labels | `outputs/tempglitch_mini_latent_scores.csv` |
| `evaluate` | Compute metrics | scores, labels | `outputs/*_metrics.json` |
| `summarize` | Build comparison tables | metrics JSON files | Markdown summary |

## MLflow policy

- MLflow is for local experiment tracking.
- Do not require an external tracking server.
- Keep `mlruns/` gitignored.
- Store canonical results in CSV/JSON files first; MLflow is secondary metadata.

## Proposed MLflow tracking fields

- `dataset_name`
- `dataset_version`
- `dataset_source`
- `scorer`
- `clip_length`
- `stride`
- `image_size`
- `latent_dim`
- `threshold`
- `auroc`
- `f1`
- `precision`
- `recall`
- `git_commit`

## Adoption checklist

- [ ] Dataset source and license verified.
- [ ] Labels converted to existing CSV schema.
- [ ] Baseline commands run successfully without DVC.
- [ ] DVC stage commands reviewed.
- [ ] `mlruns/` and `.dvc/cache/` confirmed ignored.
