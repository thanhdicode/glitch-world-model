# Research Overview

## Project title

Latent World Models for Video Game Glitch Detection: A JEPA-based Approach

## Summary

This project explores whether video game glitches can be detected as abnormal deviations in gameplay dynamics. The current repository is a compact Python research MVP: it preprocesses gameplay frames into clips, scores clips with lightweight baselines, evaluates scores against interval labels, and reports results in comparable file formats. The long-term research direction is to replace the current small latent proxy with a real LeWorldModel-style JEPA latent world model and use latent prediction error as a glitch surprise score.

## Research question

Can a latent world model trained or adapted on normal gameplay detect video game glitches by measuring prediction error or surprise over time?

## Hypothesis

Glitches often violate the learned dynamics of normal gameplay: objects teleport, intersect impossible geometry, freeze when movement should continue, flicker, or transition into states inconsistent with recent context. A latent world model should produce higher next-latent prediction error on these clips than on normal clips.

## Proposed contribution

- A reproducible baseline pipeline for clip-level game glitch detection.
- A clear comparison between simple visual baselines and a latent-dynamics proxy.
- A research plan for integrating LeWorldModel without disrupting the existing CSV-based experiment interface.
- A dataset and benchmark strategy that separates public evidence from synthetic sanity checks.

## Current repo status

The repo already contains:

- preprocessing into `manifest.csv`
- scorers: `frame_diff`, `feature_distance`, `mini_latent`, and guarded `lewm_latent`
- evaluation into `metrics.json`
- score plotting and Markdown reports
- synthetic and dynamics demo scripts
- tests for the main helpers and pipeline

Known local setup gaps may include missing `pytest`, `numpy`, `Pillow`, and `opencv-python`.

## Current MVP pipeline

```text
frame folder or video
-> preprocess.py
-> manifest.csv and clip folders
-> selected scorer
-> scores.csv
-> evaluate.py
-> metrics.json
-> plot_scores.py / dataset_report.py
```

The current best latent-dynamics proxy is `mini_latent`: PCA encoding over frames plus a simple transition model that predicts the next latent state from current latent state and latent velocity.

## Target future pipeline with real LeWorldModel

```text
normal gameplay
-> clip generation
-> LeWM encoder
-> latent sequence z_t
-> LeWM predictor or adapted transition head
-> prediction error e_t = ||z_{t+1} - zhat_{t+1}||
-> clip score
-> threshold or lightweight classifier
-> glitch detection
```

The future `lewm_latent` scorer should reuse the existing `manifest.csv`, `scores.csv`, labels CSV, and `metrics.json` interfaces.

## In scope now

- Research documentation and scaffolding.
- Baseline planning.
- Dataset and benchmark mapping.
- Reproducibility planning.
- Keeping `mini_latent` as the current LeWM proxy.

## Explicitly out of scope now

- Real LeWorldModel checkpoint loading.
- Dataset, checkpoint, or video downloads.
- Claims of state-of-the-art performance.
- Re-architecting the Python package.
- Changing the existing file interfaces.
