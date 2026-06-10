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
- [TempGlitch integration plan](docs/research/11_tempglitch_integration_plan.md)
- [Phase 6C protocol hardening](docs/research/25_phase6c_protocol_hardening_plan.md)
- [Phase 6C protocol results](docs/research/26_phase6c_protocol_results.md)
- [Phase 6D repeated grouped protocol](docs/research/27_phase6d_repeated_grouped_experiment_protocol.md)
- [Phase 6D repeated grouped results](docs/research/28_phase6d_repeated_grouped_results.md)
- [Phase 6E Kaggle video autoencoder protocol](docs/research/29_phase6e_kaggle_video_autoencoder_protocol.md)
- [Phase 6E Kaggle validation results](docs/research/31_phase6e_kaggle_validation_results.md)

Phase 6D completed five pair-suspect grouped refit/selection/locked-test runs with zero
cross-split groups. The selected pipeline achieved locked-test AUROC `0.573 +/- 0.118`; this
supports the reproducible protocol, not latent-dynamics superiority. Results remain limited by
the sequential fixed subset and prior exposure of the same 100 videos.

Phase 6E adds the first gradient-trained neural baseline package: a compact Conv3D autoencoder
that fits train-normal clips and scores validation clips. A real Kaggle CUDA run completed on
June 10, 2026. Strict local ingestion verified `1,071` validation scores, zero non-finite scores,
zero cross-split groups, and an untouched locked test. Validation AUROC was `0.403865`; this is
an engineering result and does not support a performance-improvement claim.

### Phase 6E Kaggle GPU run

Use the [Kaggle launch package](kaggle/phase6e_video_autoencoder/README.md) to prepare the private
dataset, run the five notebook cells, download artifacts, and validate them locally. Record a
real run with the [Phase 6E Kaggle run log template](docs/research/30_phase6e_kaggle_run_log_template.md).
The verified run is recorded in the
[Phase 6E Kaggle validation results](docs/research/31_phase6e_kaggle_validation_results.md).
No locked-test neural score may be claimed before a validation decision is saved and the
locked-test release gate is explicitly opened.

The resumable Kaggle automation defaults to dry-run and stops at fingerprint-bound approval
gates:

```powershell
python scripts\run_phase6e_kaggle_automation.py --dry-run
```

Live upload and kernel push require separate one-time approvals. The June 10, 2026 run consumed
fingerprint-bound approvals and completed artifact ingestion while keeping locked test untouched.

## Research-Grade Workflow

The repository is governed as a reproducible ML research lab. Start with [AGENTS.md](AGENTS.md),
the [Codex task protocol](docs/workflows/codex_task_protocol.md), the
[claim protocol](docs/workflows/research_claim_protocol.md), and the
[experiment release gates](docs/workflows/experiment_release_gates.md).

Install project development tools without adding GPU frameworks to the default environment:

```powershell
uv venv
uv pip install -e ".[dev]"
```

Pip fallback:

```powershell
python -m pip install -e ".[dev]"
```

Install and run repository hooks:

```powershell
pre-commit install
pre-commit run --all-files
```

Run the local research release gate:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts\validate_research_release.py --ci
python scripts\check_claim_registry.py
```

Generate paper tables and compile the cautious paper scaffold when `latexmk` is available:

```powershell
python scripts\make_paper_tables.py
latexmk -pdf -cd paper/main.tex
```

Current status: Phase 6E is complete as a validation-only engineering result; real LeWM is not
implemented. The next phase is the Phase 7A LeWM integration audit. Do not touch locked test
without satisfying the documented release gate and receiving explicit authorization.

Phase 0 verification commands:

```powershell
git pull --ff-only
git submodule update --init
python -m pip install -e ".[dev]"
python scripts\run_synthetic_demo.py
python -m pytest
```

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
python -m pip install -e ".[dev]"
```

Video input additionally requires OpenCV. If you only have frame folders, the default install is enough. Install video support with:

```powershell
python -m pip install opencv-python
```

The optional Kaggle/GPU video-autoencoder baseline requires PyTorch:

```powershell
python -m pip install -e ".[gpu]"
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

Audit the Phase 6E neural training partition without loading PyTorch or touching test:

```powershell
python scripts\run_kaggle_video_autoencoder.py --dry-run --manifest data\processed\tempglitch_phase3b\manifest.csv --split outputs\tempglitch_phase6d\seed_42\split.csv --output-root outputs\tempglitch_phase6e\seed_42
```

On Kaggle, run the same script without `--dry-run`, pass `--clips-root` for the uploaded
processed clip tree, and use `--device cuda`. The runner trains only on train-normal clips and
scores validation only; see the Phase 6E protocol before materializing locked test data.

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
