# Glitch World Model

This workspace starts with a small baseline pipeline for video game glitch detection. The first milestone is intentionally simple: turn gameplay videos or frame folders into clips, score each clip with frame-difference anomaly scores, evaluate against optional glitch labels, and plot the timeline.

## Research roadmap

This repo is currently a research engineering workspace for the topic "Latent World Models for Video Game Glitch Detection: A JEPA-based Approach." See the [research overview](docs/research/00_research_overview.md) for the project scope and hypothesis.

`mini_latent` remains the lightweight latent-dynamics proxy. LeWM integration engineering now
includes strict checkpoint loading, finite non-gameplay CPU inference, real-data conversion,
reduced CPU smokes, a strictly validated Kaggle CUDA train/resume smoke, and a strictly validated
normal-only TempGlitch training pilot plus a limited non-locked window-level evaluation.

Current LeWM gate status:

- Gates 1-8 passed at their documented engineering/evaluation level.
- Gate 5 passed strict Kaggle CUDA train/resume artifact validation.
- Gate 6 v8 completed normal-only CUDA training, checkpoint reload, and finite normal/non-locked
  buggy validation encoding; strict validation returned `gate6_passed`.
- Gate 7 produced 10,081 real LeWM window scores; Gate 8 used the identical manifest for two
  baselines; Gate 9 reported AUROC/AUPRC and grouped normal-P95 F1.
- The exact 500-update research-MVP GPU profile completed as engineering evidence only.
- R4 rerun seed43/44 archives are locally SHA256-verified and pass per-seed artifact validators.
- R5 completed for the non-locked TempGlitch identical-episode family with provenance-bound
  manifest, score, metric, and report outputs.
- World of Bugs remains a controlled post-R5 expansion track; WOB-P1 seed42, seed43, and seed44
  training artifact verification are complete, `R5-WOB` is validated as a positive-probe bundle,
  and `R5-XGame` compute is now intake-validated as a non-locked binary bundle.
- The repaired `R5-XGame` tarball now passes `r5_xgame_output_validated` and
  `r5_xgame_tarball_validated`; the repair was packaging-only and did not relaunch Kaggle or
  retrain LeWM.
- Local WOB replay remains blocked on missing raw tar coverage, but the Kaggle-native `WOB-P0`
  audit has now passed and resolved all 120 non-locked rows with locked test still closed.
- The verified WOB-P1 seed42/seed43/seed44 artifacts are training evidence only, not WOB
  detection-performance evidence.
- The best recorded `R5-XGame` configuration reached AUROC `0.909722` on the frozen
  12-negative / 60-positive split; this remains bounded validation evidence only.
- Roadmap V4 is now the canonical next-action authority and reopens the evidence lane for a fuller
  method-paper upgrade while preserving the current claim boundaries and locked-test closure.
- Gate 9 remains a one-buggy-episode pilot; Gate 10 has not run.
- Locked test remains closed.
- Only exact qualified pilot and R5-family metrics are supported; broad superiority, temporal
  localization, SIGReg benefit, WOB-result, cross-game generalization, and neural locked-test
  claims remain unsupported.

Research planning docs:

- [Project Playbook](PLAYBOOK.md)
- [Fast agent boot context](docs/context/BOOT.md)
- [Context cache policy](docs/context/CONTEXT_POLICY.md)
- [Current execution roadmap](docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md)
- [Real LeWM integration audit](docs/research/36_lewm_integration_audit.md)
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
- [LeWM runtime and checkpoint report](docs/research/37_lewm_runtime_checkpoint_report.md)
- [LeWM data contract](docs/research/38_lewm_data_format.md)
- [LeWM Kaggle training guide](docs/research/39_lewm_kaggle_training_guide.md)
- [Real-dataset Gate 3-4 protocol](docs/research/40_gate3_gate4_real_dataset_protocol.md)
- [Gate 5 current-state audit](docs/research/41_gate5_current_state.md)
- [Gate 5 approval status](docs/research/42_gate5_kernel_approval_status.md)
- [Gate 5 Kaggle execution record](docs/research/43_gate5_kaggle_cuda_smoke_results.md)
- [Gate 5 CUDA validation](docs/research/44_gate5_cuda_smoke_validation.md)
- [Gate 6 normal-only training plan](docs/research/45_gate6_lewm_normal_training_plan.md)
- [Gate 6 pilot results](docs/research/46_gate6_lewm_training_pilot_results.md)
- [Gate 7 LeWM scoring results](docs/research/47_gate7_lewm_surprise_scoring_results.md)
- [Gate 8 same-manifest comparison](docs/research/48_gate8_same_manifest_baseline_comparison.md)
- [Gate 9 pilot results](docs/research/49_gate9_minimal_ablation_results.md)
- [Gate 7-9 claim boundary](docs/research/50_results_claim_boundary.md)
- [R3/R4 multiseed status](docs/research/67_r3_r4_multiseed_status.md)
- [R5 identical-episode evaluation plan](docs/research/68_r5_identical_episode_eval_plan.md)
- [R5 + WOB controlled expansion plan](docs/research/68_r5_tempglitch_and_wob_expansion_plan.md)
- [R5 TempGlitch identical-episode results](docs/research/69_r5_tempglitch_identical_episode_results.md)
- [WOB controlled expansion plan](docs/research/70_wob_controlled_expansion_plan.md)
- [R5-XGame validated bundle summary](docs/research/93_r5_xgame_validated_bundle_summary.md)

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

The resumable Kaggle automation defaults to dry-run. Non-locked-test live actions use repository
standing authorization after security, license, protocol, package, and idempotency checks:

```powershell
python scripts\run_phase6e_kaggle_automation.py --dry-run
```

Fingerprints remain audit and idempotency records. Locked-test access still requires a separate
direct user command. Historical June 2026 runs used the former approval workflow.

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
python scripts\validate_context_cache.py
```

Refresh the fast context cache after each task handoff:

```powershell
python scripts\update_context_cache.py --refresh-boot
```

Generate paper tables and compile the first bounded draft when `latexmk` and the official
Springer class are available:

```powershell
python scripts\make_paper_tables.py
latexmk -pdf -cd paper/main.tex
```

Current status: Phase 6E is complete as a validation-only Conv3D engineering result. The separate
LeWM path has passed Gates 1-9 at their documented engineering or pilot scope. Gate 6 v8
completed the bounded normal-only gameplay pilot on a Tesla T4 and passed strict artifact
validation. The research-MVP GPU profile is complete as engineering evidence only, the R4 rerun
seed43/44 archives are locally SHA256-verified and validator-backed, and R5 has now completed a
non-locked TempGlitch identical-episode evaluation family. Those R5 results are qualified to that
frozen validation-only family and do not support broad superiority or general glitch-detection
claims. Kaggle-native `WOB-P0` has now passed with a verified downloaded evidence bundle, and the
WOB-P1 seed42, seed43, and seed44 training artifacts are SHA256-verified and validator-passed
under the train-normal / validation-normal protocol. `R5-WOB` completed as a validated
positive-probe bundle, and K-B / `R5-XGame` compute completed with a downloaded bundle that now
passes `r5_xgame_output_validated` and `r5_xgame_tarball_validated` locally. The final K-B tarball
SHA256 is `e41b5940a6a79713c25b03437fa76e360308fa310db9c35f812b4864ec6fff02`. The best recorded
non-locked `R5-XGame` configuration reached AUROC `0.909722` on the frozen 12-normal-negative /
60-buggy-positive split; this remains bounded validation evidence, not broad generalization or a
locked-test result. The pair-disjoint TempGlitch follow-up is validator-backed on two calibration
normals and a same-support 12-normal-negative / 22-buggy-positive evaluation split. The first
bounded paper draft and paragraph-level claim audit are complete locally. The next gate is the
official-kit paper build/claim audit and a bounded-submission versus stronger-compute decision.
The locked test still requires a separate explicit command.

The June 11, 2026 Gate 5 TempGlitch dataset upload is ready. The first approved kernel push
returned HTTP `409 Conflict` before a run was established; the local cause was a kernel slug that
matched the dataset slug. A second approved v2 push was accepted by Kaggle, then failed before
training because the generated script looked for `/kaggle/src/lewm-runtime.txt`. A third approved
v3 push was accepted by Kaggle, then failed before training because full LeWM environment
dependency installation failed while building `box2d-py`. A v4 package now uses
`huynhdieuthanh/lewm-gate5-cuda-smoke-v4` with minimal smoke dependencies. Its approved run
reached the Lance loader, then failed because `/kaggle/input` is read-only. V5 fixed writable
copying but assumed the wrong mount path. V6 recursively discovered the Lance directories,
completed on CUDA, resumed from epoch 1 to epoch 2, and passed the strict artifact validator.

The reusable split-safe core is implemented in
`src/glitch_detection/experiment_protocol.py`. It validates grouped splits, fits
train-dependent scorers on train-normal clips, scores and calibrates validation, records
provenance, and keeps test records unmaterialized unless explicitly requested. Test scoring
still requires a separate explicit release approval.

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

`run_baseline` is a demo/sanity-check runner. It fits thresholds on the same rows it evaluates.
Train-dependent scorers are blocked unless the explicitly unsafe demo flag is supplied; do not
use those outputs for benchmark claims. Research experiments must use the split-aware runners,
which fit on train-normal, calibrate on validation, and apply frozen settings to test.

Use the same runner with the feature-distance scorer for a demo only:

```powershell
python -m glitch_detection.run_baseline --input data/raw/my_frames --labels data/raw/my_labels.csv --name my_feature_experiment --clip-length 16 --stride 8 --size 128 --scorer feature_distance --demo-allow-evaluation-label-fitting
```

Run the mini latent transition scorer for a demo only:

```powershell
python -m glitch_detection.run_baseline --input data/raw/my_frames --labels data/raw/my_labels.csv --name my_mini_latent_experiment --clip-length 16 --stride 8 --size 128 --scorer mini_latent --demo-allow-evaluation-label-fitting
```

The optional-runtime LeWM scorer preserves the repository scoring interface. It requires the
isolated LeWM environment and compatible checkpoint/data contracts:

```powershell
python -m glitch_detection.lewm_latent --manifest data/processed/my_experiment/manifest.csv --labels data/raw/my_labels.csv --output outputs/my_experiment_lewm_scores.csv --checkpoint path/to/lewm.ckpt
```

All planned WOB-P1 training artifacts are now verified. Any future WOB evaluation must stay on
the frozen manifest/reporting path and remain closed until a separate explicit human command opens
the non-locked `R5-WOB` step. Locked test remains separately gated.

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
python -m glitch_detection.feature_distance --manifest data/processed/sample/manifest.csv --labels data/raw/labels.csv --output outputs/sample_feature_scores.csv --demo-allow-evaluation-label-fitting
```

Fit a threshold on validation scores only. Labels are optional CSV rows with
`source,start_frame,end_frame,label`, where `label` is `1` for glitch:

```powershell
python -m glitch_detection.evaluate --scores outputs/validation_scores.csv --labels data/raw/validation_labels.csv --output outputs/validation_metrics.json --fit-threshold
```

For test evaluation, pass the frozen validation threshold explicitly:

```powershell
python -m glitch_detection.evaluate --scores outputs/test_scores.csv --labels data/raw/test_labels.csv --output outputs/test_metrics.json --threshold 0.123
```

Plot scores:

```powershell
python -m glitch_detection.plot_scores --scores outputs/sample_scores.csv --output outputs/sample_scores.png
```

Later LeWorldModel scoring should reuse the same `manifest.csv` and `scores.csv` format so experiments stay comparable.
