# Glitch World Model

This workspace starts with a small baseline pipeline for video game glitch detection. The first milestone is intentionally simple: turn gameplay videos or frame folders into clips, score each clip with frame-difference anomaly scores, evaluate against optional glitch labels, and plot the timeline.

## Research roadmap

This repo is currently a baseline research MVP for the topic "Latent World Models for Video Game Glitch Detection: A JEPA-based Approach." See the [research overview](docs/research/00_research_overview.md) for the project scope and hypothesis.

`mini_latent` is the current lightweight latent-dynamics proxy. `lewm_latent` is reserved for future real LeWorldModel integration and is intentionally guarded until that work is explicitly scoped.

Research planning docs:

- [Literature matrix](docs/research/02_literature_matrix.md)
- [Dataset and benchmark map](docs/research/04_dataset_benchmark_map.md)
- [Experiment plan](docs/research/06_experiment_plan.md)
- [Risks and limitations](docs/research/09_risks_and_limitations.md)

## Layout

```text
data/raw/          input videos or frame folders
data/processed/    generated frame clips and manifests
outputs/           scores, metrics, and plots
src/               project code
external/          third-party references such as LeWorldModel and World of Bugs
```

## Install

```powershell
python -m pip install -e .[dev]
```

Video input additionally requires OpenCV. If you only have frame folders, the default install is enough. Install video support with:

```powershell
python -m pip install opencv-python
```

## Run The Baseline

Run a synthetic sanity-check demo:

```powershell
python scripts\run_synthetic_demo.py
```

Create a dynamics-focused toy dataset where glitches are teleport/wall-crossing events:

```powershell
python scripts\create_dynamics_test_dataset.py
```

Run a harder dynamics experiment with short teleport glitches and noisier normal motion:

```powershell
python scripts\run_hard_dynamics_experiments.py
```

Download a lightweight GlitchBench subset through the Hugging Face dataset viewer API:

```powershell
python scripts\download_glitchbench_subset.py --limit 12
python scripts\run_glitchbench_subset_experiments.py
```

Run a small World of Bugs asset demo using example images already present in `external/world-of-bugs`:

```powershell
python scripts\run_worldofbugs_asset_demo.py
```

Run the full baseline on your own video or frame folder:

```powershell
python -m glitch_detection.run_baseline --input data/raw/my_frames --labels data/raw/my_labels.csv --name my_experiment --clip-length 16 --stride 8 --size 128 --scorer frame_diff
```

Use the same runner with the feature-distance scorer:

```powershell
python -m glitch_detection.run_baseline --input data/raw/my_frames --labels data/raw/my_labels.csv --name my_feature_experiment --clip-length 16 --stride 8 --size 128 --scorer feature_distance
```

Run the mini latent transition scorer:

```powershell
python -m glitch_detection.run_baseline --input data/raw/my_frames --labels data/raw/my_labels.csv --name my_mini_latent_experiment --clip-length 16 --stride 8 --size 128 --scorer mini_latent
```

The LeWM scorer slot is registered but intentionally guarded until a checkpoint is available:

```powershell
python -m glitch_detection.lewm_latent --manifest data/processed/my_experiment/manifest.csv --labels data/raw/my_labels.csv --output outputs/my_experiment_lewm_scores.csv --checkpoint path/to/lewm.ckpt
```

Expected next implementation step: load LeWM, encode each clip, predict next latent embeddings, and write latent prediction error scores.

Create a compact Markdown report from an experiment:

```powershell
python -m glitch_detection.dataset_report --name my_experiment --manifest data/processed/my_experiment/manifest.csv --labels data/raw/my_labels.csv --scores outputs/my_experiment_scores.csv --metrics outputs/my_experiment_metrics.json --output outputs/my_experiment_report.md
```

Compare multiple baselines:

```powershell
python -m glitch_detection.compare_experiments --metric FrameDiff=outputs/my_experiment_metrics.json --metric FeatureDistance=outputs/my_experiment_feature_metrics.json --output outputs/my_experiment_comparison.md
```

Preprocess a video or folder of frames:

```powershell
python -m glitch_detection.preprocess --input data/raw/sample_video.mp4 --output data/processed/sample --clip-length 16 --stride 8 --size 128
```

Score clips with the frame-difference baseline:

```powershell
python -m glitch_detection.frame_diff --manifest data/processed/sample/manifest.csv --output outputs/sample_scores.csv
```

Score clips with the lightweight feature-distance baseline:

```powershell
python -m glitch_detection.feature_distance --manifest data/processed/sample/manifest.csv --labels data/raw/labels.csv --output outputs/sample_feature_scores.csv
```

Evaluate with labels. Labels are optional CSV rows with `source,start_frame,end_frame,label`, where `label` is `1` for glitch:

```powershell
python -m glitch_detection.evaluate --scores outputs/sample_scores.csv --labels data/raw/labels.csv --output outputs/sample_metrics.json
```

Plot scores:

```powershell
python -m glitch_detection.plot_scores --scores outputs/sample_scores.csv --output outputs/sample_scores.png
```

Later LeWorldModel scoring should reuse the same `manifest.csv` and `scores.csv` format so experiments stay comparable.
