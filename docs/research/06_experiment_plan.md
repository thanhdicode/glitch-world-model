# Experiment Plan

## Stage A: synthetic sanity check

| Field | Plan |
| --- | --- |
| Objective | Verify end-to-end pipeline mechanics. |
| Data | Synthetic brightness-change frames from `scripts/run_synthetic_demo.py`. |
| Scorer/model | `frame_diff`, optionally `feature_distance` and `mini_latent`. |
| Expected output | `manifest.csv`, `scores.csv`, `metrics.json`, score plot. |
| Metric | F1, AUROC, positive clip count. |
| Pass/fail criterion | Pipeline runs and obvious glitch interval scores higher than normal clips. |
| Risk | Too easy; not evidence for real gameplay glitches. |

## Stage B: easy/hard dynamics experiments

| Field | Plan |
| --- | --- |
| Objective | Test whether temporal-dynamics baselines catch teleport/wall-crossing events. |
| Data | `create_dynamics_test_dataset.py` and `create_hard_dynamics_dataset.py`. |
| Scorer/model | `frame_diff`, `feature_distance`, `mini_latent`. |
| Expected output | Per-scorer metrics and comparison Markdown. |
| Metric | F1, precision, recall, AUROC. |
| Pass/fail criterion | `mini_latent` behaves competitively and failure modes are documented. |
| Risk | Generated data can make visual baselines unrealistically strong. |

## Stage C: GlitchBench subset image-based demo

| Field | Plan |
| --- | --- |
| Objective | Exercise public glitch imagery through the existing file interface. |
| Data | Lightweight GlitchBench subset if user explicitly downloads it. |
| Scorer/model | `frame_diff`, `feature_distance`; `mini_latent` only if temporal framing is meaningful. |
| Expected output | Dataset report and baseline comparison. |
| Metric | Clip-level F1/AUROC after interval conversion. |
| Pass/fail criterion | Report clearly states static-image limitation. |
| Risk | Repeated static frames make frame-difference weak by design. |

## Stage D: World of Bugs asset/data audit

| Field | Plan |
| --- | --- |
| Objective | Determine what WOB assets/labels can be mapped into this repo. |
| Data | `external/world-of-bugs` after submodule initialization. |
| Scorer/model | No new model at first; audit only. |
| Expected output | Notes on asset paths, label shape, and conversion plan. |
| Metric | Not applicable for audit; later F1/AUROC if labels map cleanly. |
| Pass/fail criterion | Clear conversion path without coupling package to `external/`. |
| Risk | Environment setup may be too heavy for MVP. |

## Stage E: real temporal gameplay benchmark

| Field | Plan |
| --- | --- |
| Objective | Evaluate temporal glitch detection on public video data. |
| Data | TempGlitch, VideoGlitchBench, or another verified gameplay video benchmark. |
| Scorer/model | Baselines first, then `mini_latent`, then future `lewm_latent`. |
| Expected output | Benchmark report with documented splits and commands. |
| Metric | Clip-level and, if possible, temporal localization metrics. |
| Pass/fail criterion | Results are reproducible and claims match benchmark protocol. |
| Risk | Access, licensing, temporal labels, and compute. |

## Stage F: future LeWM integration

| Field | Plan |
| --- | --- |
| Objective | Replace proxy latent dynamics with real LeWM latent prediction error. |
| Data | Normal gameplay for adaptation plus labeled glitch evaluation data. |
| Scorer/model | `lewm_latent`. |
| Expected output | `scores.csv` compatible with existing evaluation and reporting. |
| Metric | Same metrics as baselines plus surprise calibration analysis. |
| Pass/fail criterion | LeWM integration is reproducible and compared against all simpler baselines. |
| Risk | Checkpoints, dependencies, GPU constraints, and model API mismatch. |
