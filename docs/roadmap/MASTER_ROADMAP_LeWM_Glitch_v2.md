# MASTER ROADMAP V2 — Mandatory Real LeWM Main Method

Date: June 10, 2026
Target deadline: July 20, 2026
Status: implementation roadmap; all unexecuted experiments remain `experiment-pending`.

## 1. Executive Decision

The project strategy changes from “real LeWM optional” to **real LeWM mandatory for any
LeWM-based paper claim**.

- Kaggle GPU becomes the primary training backend after local smoke tests.
- `mini_latent` remains a sanity check and fallback, not the main contribution.
- The current Conv3D validation run remains an engineering baseline, not improvement evidence.
- The paper may start as a reproducibility draft, but a LeWM title/contribution is blocked until
  Gate 7.
- If real LeWM fails before the deadline, the honest fallback is a non-LeWM reproducibility and
  negative-results paper.

## 2. New Research Claim Hierarchy

| Level | Evidence required | Maximum safe claim |
| --- | --- | --- |
| Strong | Real action-conditioned LeWM trained/fine-tuned on normal gameplay; checkpoint, logs, surprise scores, clean evaluation | “We train and evaluate an action-conditioned LeWorldModel for gameplay glitch detection.” |
| Medium | Official LeWM architecture/SIGReg trained with documented zero-action or action-free adapter; checkpoint and metrics | “We evaluate an action-agnostic adaptation of LeWorldModel.” |
| Limited | Official checkpoint loads and produces verified embeddings, but no gameplay training/evaluation | “We demonstrate checkpoint-level LeWM integration feasibility.” |
| Weak | Only `mini_latent`/Conv3D exists | “We evaluate lightweight latent-dynamics proxies.” Never say LeWM-based. |

No level permits state-of-the-art, superiority, real-time, or temporal-localization claims
without direct evidence.

## 3. Revised Phase Roadmap

### Phase 0 — Repo Audit And Reproducibility Baseline

**Objective:** preserve the verified research foundation before model integration.

**Current evidence:** editable install works; `162` tests pass as of this roadmap session;
synthetic and real-data baseline pipelines exist; split/threshold/locked-test gates are present.

**Commands**

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python scripts\run_synthetic_demo.py
python scripts\validate_research_release.py --ci
python scripts\check_claim_registry.py
```

**Gate 1:** all checks pass; no new claim is made from synthetic outputs.

### Phase 1 — Official LeWM Source And Runtime Audit

**Objective:** prove the exact upstream API, dependency, data, checkpoint, and license contract.

**Verified starting facts**

- Submodule commit: `8edfeb336732b5f3ce7b8b210d0ba370a09e2cac`.
- Official training is action-conditioned.
- Default input window is four observations: history `3`, prediction `1`.
- Loss is prediction MSE plus SIGReg.
- Official checkpoints are environment-specific.
- Current repo environment lacks LeWM runtime dependencies.

**Create/inspect**

- `docs/research/36_lewm_integration_audit.md`
- `scripts/smoke_lewm_checkpoint.py`
- `src/glitch_detection/lewm_adapter.py`
- `tests/test_lewm_adapter.py`

**Verify**

```bash
uv venv --python=3.10
uv pip install "stable-worldmodel[train,env]"
python scripts/smoke_lewm_checkpoint.py --help
```

**Gate 2 artifact:** audit plus checkpoint-load smoke report containing upstream commit,
checkpoint SHA-256, device, tensor shapes, and failure reason if blocked.

**Decision:** no checkpoint load means no inference/training work is described as integrated.

### Phase 2 — Dataset Strategy For True LeWM Training

**Objective:** choose normal-only training trajectories and held-out glitch evaluation without
source, pair, episode, or temporal-window leakage.

**Primary MVP**

- Train/validation: TempGlitch paired `Normal` videos, split by pair/source before windowing.
- Evaluation: held-out TempGlitch normal/buggy videos.
- Action mode: zero-action 1D baseline, explicitly named action-agnostic.

**Preferred strong path**

- Generate or extract normal gameplay trajectories with synchronized actions from a controlled
  Godot/Procgen/Atari/World-of-Bugs-compatible environment.
- Create controlled glitch trajectories in the same environment.
- Preserve game/session/episode IDs and action vectors.

**External datasets**

- TempGlitch: operational binary per-video evaluation; no verified temporal spans.
- World of Bugs: controlled research platform; requires extraction/conversion.
- VideoGlitchBench: temporal candidate, but public access must be confirmed before use.
- GlitchBench: image-only case study; cannot support temporal claims.

**Schema**

```text
dataset_id, revision, source, episode_id, step_idx, frame_path,
action_path/action_vector, label, category, split, pair_id
```

**Gate 3:** at least one normal-only training source and one held-out glitch evaluation source;
zero cross-split episodes/pairs; dataset provenance saved.

### Phase 3 — Video/Frame To LeWM Dataset Conversion

**Objective:** convert source-disjoint episodes to the exact installed stable-worldmodel dataset
contract.

**Create**

- `src/glitch_detection/lewm_data.py`
- `scripts/build_lewm_hdf5_dataset.py`
- `scripts/inspect_lewm_dataset.py`
- `tests/test_lewm_hdf5_format.py`
- `docs/research/37_lewm_data_format.md`

**Required columns**

- `pixels`: RGB observations, preserving episode order.
- `action`: real action vector, or documented 1D zero vector for MVP.
- `episode_idx`/`ep_idx` and `step_idx`.
- Optional `state`, `observation`, `proprio` only when genuinely available.

Do not hard-code HDF5 internals before inspecting the installed `stable-worldmodel` writer and
reader. Current upstream configs use both HDF5 and Lance.

**Conversion rules**

- Split episodes before generating temporal windows.
- Preserve raw frame provenance.
- Record source FPS, sampling stride, resize policy, action mode, and checksum.
- Do not normalize pixels manually if upstream transform performs ImageNet conversion.
- Reject clips shorter than `history_size + num_preds`.

**Gate 4:** a 5-10 clip dataset loads through the real upstream loader; keys, dtype, shapes,
episode boundaries, and action dimensions pass tests.

### Phase 4 — Kaggle GPU Training Infrastructure

**Objective:** run LeWM smoke training reproducibly with checkpoint resume.

**Create**

- `kaggle/lewm_train_kaggle.py`
- `scripts/prepare_lewm_kaggle_package.py`
- `configs/lewm_kaggle_train.yaml`
- `docs/research/38_lewm_kaggle_training_guide.md`
- validation-only fingerprint/approval automation derived from Phase 6E tooling

**Smoke configuration**

- Python `3.10`.
- Device `cuda`; CPU allowed only for local smoke and never claimed as Kaggle training.
- Start with image size `112` or upstream-compatible reduced size after shape verification.
- Batch size `2-8`; gradient accumulation if needed.
- `100-500` steps or one epoch.
- SIGReg projections may be reduced only as an explicitly recorded smoke config.
- Save weights, object checkpoint if supported, config, environment, losses, and resume metadata.

**Resume**

- Write checkpoint every epoch and on graceful stop.
- Store run ID/config hash/checkpoint SHA-256.
- Resume only when dataset/config hashes match.
- Kaggle outputs stay outside Git.

**Gate 5:** CUDA smoke training completes and a resumed run advances from a saved checkpoint.

### Phase 5 — Mandatory LeWM Training/Fine-Tuning

**Level A: integration proof**

- 5-20 normal clips, `100-500` steps.
- Proves forward/backward, pred loss, SIGReg loss, checkpoint save/load.

**Level B: paper MVP**

- Normal-only training subset.
- Source/pair-disjoint validation.
- Multiple epochs within Kaggle quota.
- Save best validation checkpoint.
- Record latent variance/covariance diagnostics to detect collapse.

**Level C: strong experiment**

- Real action-logged gameplay.
- Multiple seeds and selected ablations.
- Pretrained-vs-scratch only when architecture/action dimensions are compatible.

**Gate 6:** real checkpoint, training log, validation loss, finite non-collapsed latents, and
successful encoding of one normal and one non-locked glitch clip.

### Phase 6 — LeWM Surprise Scoring

**Objective:** generate interface-compatible anomaly scores from a frozen checkpoint.

For observations `o_t`, actions `a_t`, embeddings `z_t`, and prediction `z_hat_(t+1)`:

```text
z_t = encoder(o_t)
z_hat_(t+1) = predictor(z_history, a_history)
surprise_t = distance(z_hat_(t+1), stop_gradient(z_(t+1)))
clip_score = aggregate(surprise_t)
```

**Implement**

- `src/glitch_detection/lewm_surprise.py`
- `scripts/run_lewm_scoring.py`
- `scripts/export_lewm_latents.py`
- `scripts/plot_lewm_surprise_timeline.py`
- tests for shapes, determinism, checkpoint mismatch, and no-test access

**Distances:** L2/MSE first; cosine and normal-fitted Mahalanobis as validation-only ablations.

**Gate 7:** `scores.csv` is generated from a real LeWM checkpoint; validation metrics are finite;
the checkpoint/config/score hashes are recorded.

Only after Gate 7 may the repo use a qualified LeWM-based claim.

### Phase 7 — Baseline Comparison

Run on identical grouped splits:

1. `frame_diff`
2. `feature_distance`
3. `mini_latent`
4. Conv3D autoencoder
5. Real LeWM/action-agnostic LeWM adaptation
6. Optional CNN-LSTM/VideoMAE only if implementation and compute are controlled

**Gate 8:** comparison table with AUROC, PR-AUC, F1, precision, recall, confidence intervals,
config hashes, and no cherry-picking.

### Phase 8 — LeWM Ablations

Prioritize only:

1. zero-action vs real-action/action-free mode;
2. SIGReg weight;
3. L2 vs cosine surprise;
4. mean vs max vs top-k aggregation;
5. training data size or scratch vs compatible pretrained initialization.

**Gate 9:** at least two completed validation-only ablation tables with seeds/config hashes.

### Phase 9 — Final Evaluation And Research Integrity

- Split by source/session/episode/pair before windowing.
- Fit model, normalization, covariance, and thresholds without test data.
- Freeze one validation-selected config.
- Open locked test only through fingerprint-bound approval.
- Score locked test once.
- Report negative results and confidence intervals.

**Gate 10:** final table traces every metric to immutable artifacts and claim registry entries.

### Phase 10 — Figures, Paper, And Demo

Do not begin a LeWM-framed final paper before Gate 7.

Required evidence:

- architecture figure that labels action mode;
- training/validation loss and collapse diagnostics;
- surprise score distribution/timeline;
- main comparison and ablation tables;
- limitations covering labels, action availability, and domain mismatch.

If only binary per-video labels exist, do not claim temporal localization or temporal IoU.

## 4. Kaggle Training Plan

### Safe execution order

1. Local dependency/checkpoint smoke.
2. Dataset converter tests.
3. Local CPU forward/backward smoke.
4. Kaggle package dry-run and credential scan.
5. Separate fingerprint-bound dataset upload approval.
6. Separate fingerprint-bound kernel push approval.
7. CUDA smoke train.
8. Download and strictly ingest artifacts.
9. Validation-only MVP training.
10. Save validation decision; request locked-test approval separately.

### Required artifacts

```text
run_config.yaml
environment.json
dataset_metadata.json
training_metadata.json
loss_history.json
collapse_diagnostics.json
checkpoint_weights.pt
checkpoint.sha256
validation_scores.csv
validation_metrics.json
protocol_audit.json
resume_metadata.json
```

### OOM/timeout policy

- Reduce batch size, then use gradient accumulation.
- Reduce workers/prefetch, then image size only with a new config ID.
- Reduce SIGReg projection count only for smoke; record it.
- Resume from the latest hash-matching checkpoint.
- Never silently change model/data config during resume.
- Never treat an interrupted/no-checkpoint run as trained.

## 5. LeWM Integration Architecture

```text
manifest/split
    -> LeWM dataset builder
    -> upstream-compatible episode dataset
    -> LeWMAdapter
         checkpoint loader
         pixel preprocessor
         action adapter: real | zero | action-free
         encoder/predictor
    -> LeWMSurpriseScorer
         per-step latent error
         clip aggregation
    -> scores.csv
    -> validation calibration / gated test evaluation
```

`LeWMAdapter` must isolate upstream imports so the default package remains usable without
PyTorch. It must validate checkpoint provenance, tensor shapes, action dimension, image size,
history length, and device before inference.

## 6. Dataset Conversion Plan

### Video-only MVP

- Use only normal sources for training.
- Decode frames in episode order.
- Sample a fixed temporal stride.
- Add a 1D zero action vector per sampled transition.
- Store `action_mode=zero_action` in every dataset/run metadata artifact.

### Action-logged strong path

- Capture frame, action, episode ID, step index, game/session ID, and terminal flag together.
- Verify action timestamps align with state transitions.
- Split by game/session/episode before generating windows.

### Pseudo-action policy

Optical flow or frame-difference vectors may be evaluated only as an ablation. Because they are
computed from observations, they cannot be described as real controls.

## 7. Metrics And Evaluation Plan

**Always:** AUROC, PR-AUC, F1, precision, recall, accuracy, score distributions, confidence
intervals, per-category breakdown.

**Threshold:** fit on validation only; apply unchanged to test.

**Temporal metrics:** event F1, temporal IoU, detection delay only when verified temporal spans
exist. Full-video binary labels do not support these metrics.

**Diagnostics:** label alignment, score direction, finite scores, latent variance, covariance
rank, source/pair leakage, duplicate clips, and checkpoint/config hashes.

## 8. Baseline Plan

| Baseline | Role | Fit rule |
| --- | --- | --- |
| frame difference | no-training visual baseline | no fit |
| feature distance | simple appearance anomaly | train-normal only |
| mini latent | proxy sanity check | train-normal only |
| Conv3D autoencoder | learned reconstruction baseline | train-normal only |
| LeWM adaptation | mandatory main method | train-normal only |
| optional CNN-LSTM/VideoMAE | stronger temporal reference | only if protocol-compatible |

All methods use identical split records and validation/test release gates.

## 9. Ablation Plan

Run only after a stable LeWM checkpoint and scorer exist.

| Priority | Ablation | Scientific question |
| --- | --- | --- |
| P0 | zero-action vs real-action/action-free | Does action conditioning matter? |
| P0 | SIGReg weight including zero | Does regularization prevent collapse/improve surprise? |
| P1 | L2 vs cosine | Is ranking robust to distance choice? |
| P1 | mean/max/top-k | Is anomaly evidence sparse in time? |
| P2 | data size/checkpoint epoch | Does more normal data improve generalization? |

## 10. Risk Register

| Risk | Impact | Mitigation / decision |
| --- | --- | --- |
| No action labels in TempGlitch | Original LeWM claim blocked | Zero-action adaptation plus controlled action-logged dataset path |
| Pretrained action/domain mismatch | Invalid inference | Shape/provenance gate; train from scratch or encoder-only ablation |
| Stable-worldmodel schema/API drift | Converter failure | Pin versions; inspect installed reader/writer; adapter tests |
| Random temporal-window leakage | Inflated metrics | Split episodes before conversion/windowing |
| Kaggle OOM | No checkpoint | Small batch, accumulation, reduced smoke config, resume |
| Kaggle timeout | Incomplete run | Epoch checkpoints and hash-checked resume |
| Representation collapse | Meaningless surprise | Latent variance/covariance diagnostics; SIGReg ablation |
| Weak/below-random validation | No paper performance claim | Debug validation only; publish negative result or stop locked test |
| Binary video labels | No temporal claim | Video-level metrics; do not report temporal IoU |
| Deadline pressure | Overclaim risk | Gate-based scope; fallback title excludes LeWM |

## 11. Definition Of Done

The project may call the method **LeWM-based** only when all are true:

- official LeWM code/version and license recorded;
- real LeWM architecture instantiated;
- real checkpoint loaded or produced;
- training/fine-tuning log exists;
- action mode and dataset schema documented;
- normal-only fitting verified;
- latent prediction errors produce `scores.csv`;
- validation metrics and baseline comparison exist;
- locked test, if reported, passed the explicit release gate;
- claim registry and paper wording match the exact integration mode.

## 12. Immediate Next 72 Hours

### Hours 0-12

- Pin a Python 3.10 LeWM environment.
- Inspect installed stable-worldmodel dataset reader/writer.
- Download one official checkpoint outside Git and record SHA-256.
- Implement checkpoint-load/shape smoke test.

### Hours 12-36

- Implement `LeWMAdapter` with isolated optional imports.
- Implement and test a 5-10 clip zero-action dataset converter.
- Prove upstream loader reads it without episode leakage.

### Hours 36-72

- Run local CPU forward/backward smoke.
- Prepare Kaggle LeWM package and dry-run.
- Run no live action without fresh approvals.
- If approved later, run CUDA smoke and verify checkpoint resume.

**72-hour success condition:** Gate 4 passes locally and the Kaggle smoke package is ready.

## 13. Codex Master Prompt To Implement Phase 1-4

```text
You are implementing Phase 1-4 of the mandatory real-LeWM roadmap in
glitch-world-model. Audit the repo and external/le-wm before editing.

Constraints:
- Do not push Git, upload Kaggle live, score locked test, delete user files, or submit a paper.
- Do not commit datasets, checkpoints, outputs, credentials, caches, or large artifacts.
- Preserve manifest.csv, labels.csv, scores.csv, and metrics.json interfaces.
- Keep LeWM dependencies optional and isolated from the default package.
- Do not claim LeWM training or integration unless verified artifacts exist.

Inspect:
- external/le-wm/{README.md,train.py,jepa.py,module.py,utils.py,config/}
- src/glitch_detection/{lewm_latent.py,experiment_protocol.py,splits.py}
- scripts/run_phase6e_kaggle_automation.py
- docs/research/36_lewm_integration_audit.md
- docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v2.md

Implement in order:
1. Pin/document a Python 3.10 LeWM runtime and exact dependency versions.
2. Create src/glitch_detection/lewm_adapter.py with optional imports, checkpoint provenance,
   shape/action validation, and clear unavailable errors.
3. Create scripts/smoke_lewm_checkpoint.py. It may load and inspect one official checkpoint
   but must not produce benchmark metrics.
4. Inspect the installed stable-worldmodel reader/writer before defining custom storage.
5. Create src/glitch_detection/lewm_data.py and scripts/build_lewm_hdf5_dataset.py for a
   5-10 clip zero-action smoke dataset. Record action_mode=zero_action and split episodes
   before windowing.
6. Add tests for keys, dtype, shapes, episode boundaries, deterministic conversion, optional
   dependency failure, checkpoint mismatch, and no locked-test access.
7. Create a Kaggle validation-only training script/config with checkpoint resume and dry-run.
8. If APIs mismatch, document the exact mismatch and add the smallest adapter; do not rewrite
   upstream LeWM.
9. If no GPU is available, run only CPU smoke and state that Kaggle training is not completed.

Run:
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py

Final report:
- files inspected/changed
- exact dependency/API findings
- commands and test evidence
- generated artifacts and hashes
- locked-test/Kaggle-live status
- safe and unsafe claims
- blocker and next gate
```

## 14. Paper Claim Safety Table

| Potential wording | Status now | Condition to become safe |
| --- | --- | --- |
| “LeWM-Glitch” title | Unsafe | Gate 7 plus real comparison evidence |
| “We train LeWorldModel on gameplay” | Unsafe | Real checkpoint and training logs from official architecture |
| “Action-conditioned LeWM” | Unsafe | Synchronized real actions used in training/evaluation |
| “Action-agnostic LeWM adaptation” | Unsafe now | Zero-action/action-free real training plus scores and metrics |
| “We load an official LeWM checkpoint” | Unsafe now | Checkpoint smoke test and SHA-256 artifact |
| “mini_latent is LeWM” | Rejected | Never safe |
| “LeWM outperforms baselines” | Unsafe | Same-split comparison and uncertainty support it |
| “Temporal localization” | Unsafe | Verified span labels and temporal metrics |
| “Real-time” | Unsafe | Reproducible FPS/latency benchmark |
| “State of the art” | Rejected | Requires broad comparable benchmark evidence; not planned |
