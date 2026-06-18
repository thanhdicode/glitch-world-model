# PLAYBOOK.md - LeWM-Glitch Research Operating Bible

Last updated: 2026-06-18
Status owner: repository owner / technical program lead
Canonical branch at update: `main`
Evidence cutoff: post-R5 repo alignment through commit
`2f10ead60bd8a8cfb815f6ce1f83af06ba97538f`

## 0. How To Use This Playbook

This document is the long-form operating reference for the Glitch World Model project. Read it
before a major code change, experiment, Kaggle operation, paper edit, or release decision.

- `RULES.md` is the non-negotiable safety layer.
- `AGENTS.md` is the compact agent entry point.
- `docs/context/BOOT.md` is the default fast-start context for routine agent work.
- `PLAYBOOK.md` explains the project, evidence, gates, roles, commands, risks, and next actions.
- `docs/research/` stores detailed evidence, protocols, results, and historical decisions.
- `docs/workflows/` stores focused operational procedures.

Platform and system instructions always apply. Within repository guidance, resolve conflicts in
this order:

1. current explicit user instruction;
2. `RULES.md`;
3. `AGENTS.md`;
4. `PLAYBOOK.md`;
5. current verified documents under `docs/research/`;
6. historical plans and superseded documents.

If this playbook conflicts with a newer checked artifact, update the playbook in the same task.
Do not silently choose the more exciting interpretation.

### Context Efficiency Layer

Routine tasks should start from `RULES.md`, `AGENTS.md`, and `docs/context/BOOT.md`, then use
`PROJECT_STATE.md`, `NEXT_ACTION.md`, `TASK_ROUTER.md`, and `REPO_MAP.md` to choose the smallest
relevant file set. Open this playbook when a task touches roadmap status, claims, paper scope,
gate decisions, or ambiguous safety policy. After each task, update `LAST_HANDOFF.md`, refresh
the context cache, and run `scripts/validate_context_cache.py`. The target is a boot context
under 200 lines without hiding safety rules.

### When In Doubt

1. Stop before locked-test access or any external side effect that fails repository policy.
2. Find the artifact or primary source that supports the proposed statement.
3. Use the weaker claim when evidence levels differ.
4. Keep locked test closed.
5. Use standing authorization for validated non-locked-test Kaggle actions; require a separate
   direct user command for locked test.

## 1. Project Identity

| Field | Current value |
| --- | --- |
| Research title | Latent World Models for Video Game Glitch Detection: A JEPA-based Approach |
| Repository | `thanhdicode/glitch-world-model` |
| Target venue | EAI FISAT 2026 |
| Official submission deadline | 2026-07-20 |
| Internal PDF freeze | 2026-07-18, planning target |
| Internal early submission | 2026-07-19, planning target |
| Current venue format | Springer LNICST, anonymized English PDF |
| Regular paper length | 12-15 pages, excluding appendices, references, acknowledgements |
| Main research method | LeWM/JEPA latent prediction surprise |
| Current gate state | Gates 1-8 passed; Gate 9 passed as a limited non-locked window pilot; R5 completed for the non-locked TempGlitch family; Gate 10 closed |
| Locked test | Closed, unmaterialized, unscored for the LeWM path |

LeWM integration engineering exists together with a limited one-buggy-episode window pilot and a
completed validation-only, non-locked TempGlitch R5 identical-episode family.

## 2. One-Page Executive Summary

Manual game QA is expensive because modern games expose large state spaces, long temporal
dependencies, and rare failures that are easy to miss. Many glitches are not strange still
images. They are implausible transitions: teleportation, wall crossing, frozen animation,
blinking, invalid velocity, or action/state inconsistency.

The project tests a simple research idea: learn normal gameplay dynamics, then treat latent
prediction error as surprise. A JEPA-style world model predicts future representations rather
than reconstructing every pixel. This may reduce sensitivity to lighting, texture, and camera
noise while preserving dynamics that matter for gameplay.

LeWorldModel is the mandatory main-method path for any LeWM-framed paper claim. The audited
upstream method is action-conditioned, uses a ViT encoder and autoregressive predictor, and
trains with prediction loss plus SIGReg. The repository has already verified:

- an isolated Python 3.10 LeWM runtime;
- strict loading of an official PushT checkpoint;
- finite non-gameplay CPU surprise output;
- leakage-aware TempGlitch and World of Bugs protocols;
- synthetic and reduced real-data Lance conversion;
- reduced CPU forward/backward, checkpoint save, and hash-matching resume.

The repository has not verified:

- broad multi-episode LeWM glitch-detection performance;
- LeWM superiority, SIGReg benefit, temporal localization, or state of the art;
- a neural locked-test result.

Gate 5 passed strict CUDA/resume artifact validation. Gate 6 v8 then completed the bounded
normal-only TempGlitch pilot on CUDA, verified checkpoint reload and finite validation encoding,
and passed the strict validator with locked-test flags false. Gates 7-9 then produced 10,081
real frozen-checkpoint scores, same-manifest baselines, and validation-only pilot metrics. The
exact 500-update GPU profile is complete as engineering evidence only, the R4 rerun seed43/44
artifacts are now SHA256-verified and validator-backed, and R5 has completed a provenance-bound
non-locked TempGlitch identical-episode evaluation family. The current operational phase is WOB
controlled planning. World of Bugs remains a controlled post-R5 expansion track, not an active
execution family.

## 3. Why This Project Exists

### Practical Motivation

- Manual QA cannot exhaustively cover every action, camera state, physics interaction, and asset
  combination.
- Rare temporal failures can survive conventional screenshot review.
- A reusable anomaly score can prioritize clips for human inspection.

### Scientific Motivation

- Static appearance detectors cannot fully represent whether a transition is physically or
  temporally plausible.
- Pixel reconstruction can overemphasize texture and low-level variation.
- Latent prediction offers a direct dynamics-aware anomaly signal.
- Action-conditioned models can test whether observations agree with the controls that produced
  them.

### Integrity Commitment

Weak results are valid research outcomes. If LeWM underperforms simple baselines, the project
must report the negative result, analyze failure modes, and narrow the paper. It must never
invent a metric, hide a limitation, or turn engineering readiness into performance evidence.

## 4. Research Problem And Scope

### Problem

Given a gameplay clip or frame sequence, emit a scalar surprise score and, when supported by
labels, a binary glitch decision. The target method learns normal gameplay dynamics and detects
violations through next-latent prediction error.

### In Scope

- video/frame preprocessing and manifest generation;
- train-normal anomaly methods;
- action-conditioned, zero-action, or explicitly modified action-free LeWM paths;
- clip/video-level binary detection;
- validation calibration, grouped evaluation, uncertainty, and failure analysis;
- optional event segments only when verified span labels exist.

### Out Of Scope Without New Evidence

- root-cause debugging of source-code defects;
- open-ended glitch captioning;
- temporal localization from binary per-video labels;
- training on glitch samples under a normal-only protocol;
- claims of real-time operation without latency/FPS measurement.

### Interfaces

| Stage | Required interface |
| --- | --- |
| Input clips | gameplay frames or videos |
| Manifest | `manifest.csv` |
| Labels | `source,start_frame,end_frame,label` CSV |
| Scores | `scores.csv` |
| Metrics | `metrics.json` |

Primary metrics are AUROC, PR-AUC, F1, precision, recall, accuracy, and confidence intervals.
Temporal IoU, event F1, and detection delay are allowed only with verified temporal spans.

## 5. Core Hypothesis

Glitches are violations of learned gameplay dynamics. A world model trained on normal
trajectories should predict ordinary transitions more accurately than abnormal transitions.

For observations `o_t`, action history `a_t`, latent targets `z_t`, and predicted latents
`z_hat_t`:

```text
z_t = encoder(o_t)
z_hat_(t+1) = predictor(z_history, a_history)
surprise_t = distance(z_hat_(t+1), stop_gradient(z_(t+1)))
clip_score = aggregate(surprise_t)
```

The hypothesis is not yet supported by gameplay-scale LeWM metrics. JEPA and SIGReg may be
described as components of the audited method, but their gameplay detection benefit remains
`experiment-pending` until the relevant ablations and validation artifacts exist.

## 6. Research Questions

- **RQ1:** Does LeWM latent surprise separate normal and glitch gameplay?
- **RQ2:** Does the action-conditioned World of Bugs path outperform a zero-action adaptation?
- **RQ3:** Does TempGlitch zero-action LeWM produce a useful anomaly signal despite missing
  action logs?
- **RQ4:** How does LeWM compare with `frame_diff`, `feature_distance`, `mini_latent`, and Conv3D?
- **RQ5:** How do SIGReg weight, surprise distance, and temporal aggregation affect results?
- **RQ6:** When results are weak, which failure modes dominate: label granularity, domain
  mismatch, representation collapse, action mismatch, or visual confounds?

## 7. Safe Contributions And Forbidden Claims

| Claim | Status | Evidence required | Current wording |
| --- | --- | --- | --- |
| Checkpoint-level LeWM integration | paper-safe, limited | strict load report and finite smoke | "We verify checkpoint-level LeWM integration feasibility." |
| Real-data conversion | paper-safe, limited | frozen protocols and upstream Lance loader proof | "We convert reduced TempGlitch and WOB episodes to the audited data contract." |
| CPU forward/backward/resume smoke | paper-safe, engineering | local metadata and hash-matching resume | "Reduced CPU engineering smokes complete." |
| Gates 1-6 passed | paper-safe, governance | gate reports and validators | State the exact engineering scope. |
| Gate 5 CUDA/resume smoke | paper-safe, engineering | strict v6 artifact validation | State that this is bounded engineering evidence. |
| Exact Gate 7-9 window-pilot metrics | paper-safe, tightly qualified | reports 47-50 and hashed artifacts | State one buggy episode, correlated windows, and failed LeWM P95 F1. |
| Broad LeWM glitch-detection performance | paper-unsafe | multi-episode comparable evidence | Do not say. |
| LeWM beats baselines generally | paper-unsafe | broader comparison on independent episodes | Do not say. |
| SIGReg improves detection | paper-unsafe | Gate 9 controlled ablation | Do not say. |
| JEPA superiority | paper-unsafe | protocol-compatible comparative evidence | Do not say. |
| State of the art | paper-unsafe | broad comparable benchmark evidence | Do not say. |
| Real-time operation | paper-unsafe | reproducible hardware latency/FPS benchmark | Do not say. |
| TempGlitch temporal localization | paper-unsafe | verified span labels and temporal metrics | Do not say from current binary labels. |
| Neural locked-test result | paper-unsafe | Gate 10 one-time release | Do not say. |
| Kaggle LeWM CUDA resume | paper-unsafe | strict downloaded artifact validation | Do not say. |

### Do Not Say

- "LeWM detects gameplay glitches" as a general conclusion from the one-episode pilot.
- "SIGReg improves anomaly detection" before a controlled Gate 9 ablation.
- "Locked-test performance" for validation-only or previously exposed evidence.
- "Temporal localization" when labels cover only whole videos.

### Do Not Do

- Run a Kaggle action that fails security, license, protocol, package, or idempotency policy.
- Materialize or score locked test.
- Delete remote Kaggle resources or publish credentials, private data, or unlicensed data.
- Fit thresholds, covariance, normalization, or model choices on test.
- Commit data, outputs, Lance datasets, checkpoints, tracker stores, or credentials.

## 8. Current Verified Status

Status date: 2026-06-18.

| Gate | Status | Evidence | Missing | Paper claim impact |
| --- | --- | --- | --- | --- |
| 1 | passed | baseline pipeline, tests, release tooling | none for gate | Reproducible pipeline claim allowed. |
| 2 | passed | `37_lewm_runtime_checkpoint_report.md` | gameplay use | Checkpoint integration only. |
| 3 | passed | frozen TempGlitch/WOB protocol artifacts summarized in report 40 | official TempGlitch pair IDs; replay action audit | Dataset protocol claim allowed with limitations. |
| 4 | passed | real-data Lance loader proof in reports 38 and 40 | full-scale materialization | Reduced conversion claim allowed. |
| 5 | passed | v6 T4 run, CUDA device, epoch 1 to 2 resume, matching hashes, finite artifacts, locked-test false | none | Kaggle CUDA engineering smoke claim allowed. |
| 6 | passed | v8 T4 normal-only pilot, strict reload/encoding validation | full training scale | Bounded gameplay-training engineering claim allowed. |
| 7 | passed | 10,081 finite real LeWM window scores and hashes | broader buggy validation | Exact validation scoring claim allowed. |
| 8 | passed | two baselines on the identical canonical manifest | broader baseline suite | Exact same-manifest comparison allowed. |
| 9 | passed pilot | AUROC/AUPRC and grouped-normal-P95 F1 for eight scorers | multi-episode evidence and working LeWM calibration | Only the qualified one-episode pilot result is allowed. |
| 10 | closed | no materialization or scoring | frozen decision and explicit direct user command | No neural locked-test claim. |

The exact 500-update non-locked GPU profile completed and passed strict artifact validation as
engineering evidence only. The 2026-06-17 R4 rerun archives for seed43 and seed44 are now local
SHA256-verified and pass the per-seed artifact validators; R5 is complete for the non-locked
TempGlitch identical-episode family, local WOB replay remains `BLOCKED_MISSING_INPUTS`, and the
Kaggle-native `WOB-P0` pass is now verified from a downloaded evidence bundle. The LeWM
TempGlitch private dataset is ready and matched the local approved Lance inventory by
name and size. One exact fingerprint-approved kernel push on 2026-06-11 returned HTTP 409 before
a run was established; its one-time approval is consumed. The local cause was a kernel slug equal
to the dataset slug. A second exact approval for the corrected v2 package was then consumed for
one push; Kaggle accepted the kernel version, but it failed before training because the generated
script looked for `/kaggle/src/lewm-runtime.txt`. A third exact approval for v3 was consumed for
one push; Kaggle accepted the kernel version, but full LeWM environment dependency installation
failed on `box2d-py` before training. V4 installed minimal dependencies and reached the real Lance
loader, then failed because `LanceDataset` attempted to write under read-only `/kaggle/input`.
V5 copied both Lance datasets to writable `/tmp/lewm_input`, but failed because its fixed
dataset-slug path did not contain the Lance directories at runtime. V6 recursively discovered
the named Lance directories, completed on a T4, advanced resume from epoch 1 to epoch 2, and
passed the strict local validator with matching hashes and false locked-test flags. The Phase 6E
Conv3D run remains separate from LeWM Gate 5.

## 9. Gate Roadmap To FISAT 2026

### Gate 1 - Baseline And Protocol Foundation

- **Objective:** keep preprocess -> score -> evaluate -> report reproducible and fail-closed.
- **Required artifacts:** tests, CSV/JSON contracts, split and locked-test guards.
- **Commands:** `python -m pytest`; release and claim validators.
- **Pass criteria:** default checks pass and no prohibited tracked artifacts exist.
- **Blockers:** broken interfaces, leakage, missing validators.
- **Safe claim after pass:** reproducible research pipeline.
- **Next gate:** runtime/checkpoint audit.

### Gate 2 - Runtime And Checkpoint Audit

- **Objective:** prove exact LeWM runtime and official checkpoint compatibility.
- **Required artifacts:** runtime versions, upstream commit, checkpoint SHA-256, tensor shapes.
- **Commands:** `python scripts/smoke_lewm_checkpoint.py --help` before any approved smoke.
- **Pass criteria:** strict load and finite non-gameplay inference.
- **Blockers:** dependency drift, checkpoint/config mismatch.
- **Safe claim after pass:** checkpoint-level integration feasibility.
- **Next gate:** dataset protocol.

### Gate 3 - Dataset Protocol

- **Objective:** freeze leakage-safe train/validation/locked-test metadata.
- **Required artifacts:** split CSV, provenance JSON, audit JSON, exposure history, hashes.
- **Commands:** inspect `scripts/freeze_tempglitch_protocol.py --help` and
  `scripts/freeze_wob_protocol.py --help`.
- **Pass criteria:** split before windowing; zero cross-split pair/source/episode groups;
  train-normal rule; locked test metadata-only.
- **Blockers:** missing provenance, ambiguous pairing, action uncertainty.
- **Safe claim after pass:** frozen protocol exists, with named limitations.
- **Next gate:** conversion/adapter.

### Gate 4 - Dataset Conversion And Adapter

- **Objective:** load reduced real episodes through the installed upstream Lance reader.
- **Required artifacts:** converter metadata, hashes, schema and boundary audit.
- **Commands:** `python scripts/inspect_lewm_dataset.py --help`.
- **Pass criteria:** correct keys, shapes, dtypes, action dimensions, and episode boundaries.
- **Blockers:** storage API drift, malformed actions, unsafe pickle content.
- **Safe claim after pass:** reduced real-data conversion and loader compatibility.
- **Next gate:** Kaggle CUDA smoke/resume.

### Gate 5 - Kaggle CUDA Smoke And Resume

- **Objective:** prove CUDA training and hash-matching checkpoint resume.
- **Required artifacts:** environment, config, data/training metadata, losses, collapse
  diagnostics, protocol audit, checkpoint hash, and resume metadata.
- **Commands:** package dry-run and strict validator commands in Section 23.
- **Pass criteria:** CUDA true, device `cuda`, resumed epoch advances, hashes match, finite
  diagnostics, locked-test flags false.
- **Blockers:** consumed or missing approval, Kaggle submission conflict, quota, OOM, timeout,
  missing artifact, validator failure.
- **Safe claim after pass:** Kaggle CUDA engineering smoke with verified resume.
- **Next gate:** gameplay-scale normal-only training.

### Gate 6 - Real LeWM Training

- **Objective:** produce a gameplay checkpoint from normal-only training data.
- **Required artifacts:** training config/log, checkpoint, validation loss, collapse diagnostics,
  environment and hashes.
- **Commands:** only after Gate 5; review `python scripts/run_kaggle_lewm.py --help`.
- **Pass criteria:** finite training, non-collapsed latents, checkpoint reload, validation clip
  encoding, no locked-test access.
- **Blockers:** collapse, domain mismatch, action mismatch, quota.
- **Safe claim after pass:** qualified gameplay training engineering, not detection performance.
- **Next gate:** validation scoring.

### Gate 7 - Validation Scoring And Metrics

- **Objective:** generate gameplay `scores.csv` from a frozen real LeWM checkpoint.
- **Required artifacts:** checkpoint/config/score/metric hashes, validation protocol audit.
- **Commands:** validation-only `python -m glitch_detection.lewm_latent ...`; never use locked
  inputs.
- **Pass criteria:** finite scores, validation metrics, correct action mode, reproducible hashes.
- **Blockers:** scorer mismatch, non-finite scores, label alignment, score direction.
- **Safe claim after pass:** carefully qualified LeWM-based validation result.
- **Next gate:** same-split baseline comparison.

### Gate 8 - Baseline Comparison

- **Objective:** compare methods under identical grouped splits and selection rules.
- **Required artifacts:** comparison table, confidence intervals, config hashes, provenance.
- **Commands:** use split-aware runners and `scripts/summarize_all_experiments.py`.
- **Pass criteria:** no cherry-picking; AUROC, PR-AUC, F1, precision, recall, and CI present.
- **Blockers:** missing baseline, inconsistent split, tuning on test.
- **Safe claim after pass:** relative validation findings within the executed protocol.
- **Next gate:** ablations.

### Gate 9 - LeWM Ablations

- **Objective:** isolate action mode, SIGReg, distance, aggregation, and data-size effects.
- **Required artifacts:** validation-only tables, seeds, configs, hashes, collapse diagnostics.
- **Commands:** no canonical run command until Gate 7 freezes the scorer contract.
- **Pass criteria:** at least two controlled ablation tables without test access.
- **Blockers:** compute, unstable checkpoint, confounded configuration changes.
- **Safe claim after pass:** only effects directly supported by controlled validation evidence.
- **Next gate:** frozen validation decision.

### Gate 10 - One-Time Locked Test And Final Evidence

- **Objective:** evaluate exactly one frozen configuration once.
- **Required artifacts:** validation decision, selected config SHA-256, one-time approval,
  test scores/metrics hashes, disclosure record.
- **Commands:** inspect `python scripts/evaluate_tempglitch_locked_test.py --help`; execution
  requires explicit approval and is not authorized by this playbook.
- **Pass criteria:** one config, one score run, frozen threshold, no post-test tuning.
- **Blockers:** missing approval, leakage, invalid artifact, prior access.
- **Safe claim after pass:** the exact locked-test result, with limitations and provenance.
- **Next gate:** final paper/release packaging.

## 10. Timeline And Freeze Dates

These are internal planning targets, not completed events. Replan openly if a gate slips.

| Target | Internal date | Exit condition |
| --- | --- | --- |
| Gate 5 | 2026-06-14 | Strict CUDA/resume artifact validator passes. |
| Gates 6-7 | 2026-06-28 | Gameplay checkpoint and validation metrics exist. |
| Gate 8 | 2026-07-03 | Same-split comparison table is frozen. |
| Gate 9 | 2026-07-07 | Priority ablations and failure analysis complete. |
| Gate 10 decision | 2026-07-10 | Open only if validation decision is defensible. |
| Full draft | 2026-07-12 | All claims trace to registry/evidence. |
| Evidence freeze | 2026-07-15 | No new experiment scope except critical correction. |
| PDF freeze | 2026-07-18 | LNICST PDF, references, alt text, anonymization checked. |
| Submit early | 2026-07-19 | Confy+ upload and PDF verification complete. |
| Official deadline | 2026-07-20 | Venue deadline; do not plan to use the final hours. |

The roadmap target and official FISAT page agree on 2026-07-20. The PDF freeze and early
submission dates are project risk controls, not venue deadlines.

## 11. Dataset Strategy

| Dataset | Role | Current status | Label type | Actions | Allowed claims |
| --- | --- | --- | --- | --- | --- |
| TempGlitch | primary video benchmark | public revision frozen; reduced conversion verified | binary per-video/category | unavailable; explicit zero-action `(T,1)` | protocol/conversion only until LeWM metrics exist |
| World of Bugs | controlled action path | inventory/protocol and reduced conversion verified | normal/bug episodes and categories | scalar actions converted to one-hot `(T,4)` | structural action-conditioned engineering with sync caveat |
| GlitchBench | static auxiliary case study | public image artifact verified | image-level descriptions/types | none | static-image evidence only |
| VideoGlitchBench | optional temporal benchmark | paper verified; public artifact unverified | descriptions and spans on paper | unknown | related work/future work only |
| Atari/Procgen | optional dynamics sanity path | not implemented | environment-dependent | available in controlled capture | future-work only |
| Synthetic repo data | mechanics sanity checks | available on demand | generated interval labels | generated/none | no benchmark or novelty claim |

Rules:

- Split by pair/source/session/episode before generating windows.
- Fit train-dependent methods on allowed train-normal data only.
- Keep locked-test media unmaterialized until release.
- Record revision, license, source identity, action mode, resize, stride, and hashes.
- Never infer temporal spans from whole-video binary labels.

TempGlitch is the zero-action MVP because it lacks verified action logs. World of Bugs is the
action-conditioned path because the data contains actions, but a tar audit does not prove every
action's physical semantics; preserve that limitation until replay synchronization is checked.

## 12. Methodology

```text
raw video/frames
  -> manifest and source provenance
  -> grouped train/validation/locked-test metadata
  -> dataset converter
  -> LeWM training or frozen-checkpoint inference
  -> per-step latent prediction error
  -> clip aggregation
  -> scores.csv
  -> validation calibration and metrics.json
  -> claim registry
  -> generated paper table
```

### Method Components

- **Manifest:** binds clip IDs to source, time range, path, frame count, and FPS.
- **LeWM adapter:** isolates optional dependencies, strict checkpoint loading, preprocessing,
  temporal shape, action dimensions, and device checks.
- **Zero-action mode:** supplies zero actions while retaining the upstream architecture; it must
  be named as an action-agnostic adaptation.
- **Real-action mode:** consumes aligned action vectors and is the strongest scientific path.
- **Action-free mode:** changes the predictor and is currently declared but not implemented by
  the official adapter.
- **Scorer registry:** keeps methods comparable through shared `scores.csv` output.
- **Calibration:** selects threshold on validation only.
- **Reporting:** records metrics, uncertainty, provenance, limitations, and claim scope.

## 13. LeWM Integration Strategy

The audited upstream identity is commit
`8edfeb336732b5f3ce7b8b210d0ba370a09e2cac`, MIT licensed. The verified isolated runtime uses
Python 3.10.12, `stable-worldmodel==0.1.1`, `stable-pretraining==0.1.7`,
`transformers==4.57.6`, and a checkpoint-compatible PyTorch runtime.

The adapter must validate:

- checkpoint and config existence;
- checkpoint SHA-256 and strict state-dict compatibility;
- image size, history length, action dimension, and device;
- tensor shape `(B,T,C,H,W)`;
- real versus zero-action semantics;
- finite surprise output;
- optional dependency failure with an actionable message.

| Mode | Meaning | Current status | Required wording |
| --- | --- | --- | --- |
| `real` | official action-conditioned path with real actions | reduced WOB engineering smoke | "action-conditioned" only with synchronized action evidence |
| `zero_action` | official architecture supplied zero controls | reduced TempGlitch engineering smoke | "zero-action adaptation" |
| `action_free` | predictor modified to remove actions | not implemented | "future method variant" |

`mini_latent` is a PCA/linear transition proxy. It is never LeWM, JEPA, or SIGReg.

Current missing evidence is no longer CUDA resume or profile feasibility. The missing evidence is
R5 identical-episode TempGlitch metrics, frozen validation reporting at episode level, and any
post-R5 WOB expansion artifacts.

## 14. Baseline Strategy

| Baseline | Role | Status | Fit rule | Claim limit |
| --- | --- | --- | --- | --- |
| `frame_diff` | minimal motion/change baseline | implemented | no fit | visual-change baseline |
| `feature_distance` | appearance anomaly baseline | implemented | train-normal | limited temporal meaning |
| `mini_latent` | lightweight dynamics proxy | implemented | train-normal | not LeWM |
| Conv3D autoencoder | learned reconstruction baseline | validation CUDA run complete | train-normal | negative validation engineering result |
| CNN-LSTM | temporal neural baseline | future-work | protocol-dependent | no claim yet |
| VideoMAE + Mahalanobis | frozen video representation baseline | future-work | normal feature statistics | no claim yet |
| TimeSformer + Mahalanobis | frozen/supervised reference | future-work | protocol-dependent | no claim yet |
| Qwen/LLaVA-style VLM | semantic fallback | future-work | prompt/runtime dependent | no temporal claim without spans |
| LeWM surprise | mandatory main method | Gate 7-9 non-locked pilot complete | train-normal | exact pilot metrics only; no broad claim |

All comparisons must use identical split records. Advanced baselines should wait until Gate 7
unless a task explicitly scopes them as independent engineering work.

## 15. Evaluation Protocol

1. Freeze group-level split metadata before windows are created.
2. Fit model, normalization, covariance, and train-dependent scorers on train-normal only.
3. Score validation and verify finite outputs and score direction.
4. Choose model, aggregation, and threshold using validation only.
5. Record bootstrap confidence intervals and per-category diagnostics.
6. Freeze exactly one configuration before any locked-test request.
7. Apply the frozen validation threshold unchanged to test.
8. Score locked test once.

Every metric artifact must identify:

- dataset revision and split hash;
- git SHA and dirty state;
- scorer/model/config/checkpoint hash;
- fit split and threshold source;
- action mode;
- score and metrics hashes;
- locked-test materialization/scoring flags.

AUROC should accompany F1 because F1 can look favorable under a threshold that predicts almost
everything positive. PR-AUC is especially important under class imbalance.

## 16. Artifact And Evidence Policy

### May Be Committed

- source code, tests, configs, schemas, and validators;
- redacted templates and dry-run examples;
- small evidence summaries with provenance;
- research docs, claim registry entries, and generated paper tables.

### Must Not Be Committed

- `outputs/`, `data/raw/`, `data/processed/`;
- checkpoints, weights, Lance datasets, converted media;
- `mlruns/`, `wandb/`, DVC cache, virtual environments, caches;
- `.env`, `kaggle.json`, tokens, private keys, credentials;
- downloaded external reference repositories.

### Required SHA-256 Evidence

- dataset/package inventory;
- split;
- resolved configuration;
- checkpoint/weights;
- `scores.csv`;
- `metrics.json`;
- environment lock or environment report.

Store local artifacts only under ignored project paths or approved external storage. Never put
machine-specific private paths into paper-facing documentation.

### Evidence Hierarchy

1. checked immutable artifact with validator output;
2. local execution log tied to SHA/config;
3. repository document summarizing checked evidence;
4. plan, scaffold, or future-work statement.

A lower evidence level cannot silently upgrade a claim.

## 17. Kaggle GPU Operating Protocol

Repository standing authorization covers validated non-locked-test Kaggle execution.

1. Prepare and security-scan the dataset package.
2. Compute the dataset inventory fingerprint.
3. Validate license, redistribution permission, visibility, and false locked-test flags.
4. Create or version the dataset under standing authorization.
5. Finalize and fingerprint the kernel against the remote dataset identity.
6. Push once per fingerprint, poll without duplicate submissions, and download expected outputs.
7. Validate downloaded artifacts locally before updating a gate or claim.

Changing package contents creates a new fingerprint. A runtime failure cannot be retried until a
relevant package change produces a new fingerprint. Locked-test access remains outside standing
authorization and requires a separate direct user command.

### Gate 5 Artifact Contract

- `environment.json`
- `resume_metadata.json`
- `protocol_audit.json`
- resolved run config: current code emits `run_config.json`; adopt
  `run_config.resolved.json` only with a versioned validator change
- `dataset_metadata.json`
- `training_metadata.json`
- `loss_history.json`
- `collapse_diagnostics.json`
- `checkpoint.sha256`

The strict validator must confirm CUDA, an advanced resumed epoch, matching config/data hashes,
matching checkpoint hash, finite non-empty loss history and collapse diagnostics, and false
locked-test flags in protocol and training metadata. If any requirement fails, Gate 5 remains
partial.

## 18. Locked-Test Release Protocol

Locked test is closed by default.

Preconditions:

- validation evidence names one model, checkpoint, preprocessing, scorer, aggregation, and
  threshold;
- the decision stores split/config/checkpoint hashes and claim scope;
- leakage and artifact-validation findings are resolved;
- the user explicitly approves the exact decision fingerprint.

Execution:

1. Verify approval and hashes.
2. Materialize only required test inputs.
3. Score exactly once.
4. Apply the frozen validation threshold unchanged.
5. Hash scores and metrics.
6. Update the claim registry and paper wording.

Never compare candidates, refit statistics, or tune thresholds on test. Any post-test tuning
invalidates the locked-test framing and must be disclosed.

## 19. Toolchain And Runtime Management

| Tool/runtime | Policy |
| --- | --- |
| Default Python | Python 3.10+ with `.[dev]`; current host baseline is 3.14.4 |
| LeWM runtime | isolated Python 3.10 with exact audited pins |
| uv | preferred environment manager; use lock/sync/frozen workflows when a maintained lock exists |
| pytest | required for behavioral and release verification |
| Ruff | required lint and formatting |
| pre-commit | required before commit when installed |
| release validator | required governance/artifact gate |
| claim validator | required paper-claim gate |
| doctor | required local environment/governance report |
| MLflow | optional local metadata index; `mlruns/` ignored |
| W&B | optional; network tracking and artifact upload require explicit privacy review |
| DVC | optional reproducibility layer; do not add raw datasets without license/storage review |

Do not add PyTorch, LeWM, OpenCV, Kaggle, or tracker dependencies to default CI. Change one
runtime boundary at a time and rerun strict checkpoint/interface tests.

Primary operational references:

- uv: `https://docs.astral.sh/uv/concepts/projects/sync/`
- MLflow Tracking: `https://mlflow.org/docs/latest/ml/tracking/`
- W&B Artifacts: `https://docs.wandb.ai/models/artifacts`
- DVC data versioning: `https://dvc.org/doc/start/data-management/data-versioning`
- pre-commit: `https://pre-commit.com/`

## 20. AI Agent Operating System

| Entry point | Purpose |
| --- | --- |
| `AGENTS.md` | compact project identity, contracts, gates, required commands |
| `RULES.md` | non-negotiable safety and scientific rules |
| `PLAYBOOK.md` | long-form project bible and current program state |
| `CLAUDE.md` | imports `AGENTS.md` and points Claude to this playbook |
| `.github/copilot-instructions.md` | Copilot repository instructions |
| `.github/instructions/` | path-scoped Copilot rules |
| `CONVENTIONS.md` | shared coding conventions |
| `.aider.conf.yml` | loads AGENTS/RULES/CONVENTIONS read-only |
| `.codex/skills/` | role-specific operating cards |

Every substantial task begins by reading `RULES.md`, `AGENTS.md`, this playbook, and the
relevant workflow/evidence files. Aider users must open this playbook for major project work
even though the compact policy files are the automatic read set.

## 21. Skills And Role Playbooks

| Skill | Mission / use when | Key files | Verification | Forbidden actions |
| --- | --- | --- | --- | --- |
| `research_integrity_reviewer` | audit claims and reports | claim registry, research docs | claim and release validators | promoting smoke evidence |
| `ml_research_engineer` | implement experiments/evaluation | scorers, protocol, tests | pytest and Ruff | test tuning or unapproved GPU |
| `lewm_integration_engineer` | maintain runtime/checkpoint/data/training contracts | `lewm_*`, reports 36-39 | focused LeWM tests | calling zero-action original LeWM |
| `dataset_protocol_engineer` | freeze leakage-safe datasets | protocol modules, report 40 | dataset/LeWM data tests | window-level random splits |
| `kaggle_gpu_operator` | package, approve, monitor, ingest | Kaggle scripts/workflows | Kaggle validation tests | implicit uploads/pushes |
| `locked_test_release_officer` | enforce one-time release | release workflow/script | locked-test tests | repeated test scoring |
| `paper_claim_auditor` | align title/tables/text with evidence | paper, claims, sources | table generator and claim check | SOTA or Gate 7/10 bypass |
| `security_artifact_guard` | keep secrets/artifacts out of Git | ignore rules, release validator | diff, validator, pre-commit | printing secrets |
| `fullstack_research_software_engineer` | deliver cross-layer tooling | src/scripts/tests/docs | full suite and doctor | unrelated refactors |

The complete mission, inputs, outputs, checks, and commands live in each matching
`.codex/skills/*.md` card.

## 22. Repository Map

```text
.
|-- AGENTS.md                    compact agent entry point
|-- RULES.md                     non-negotiable rules
|-- PLAYBOOK.md                  long-form operating reference
|-- src/glitch_detection/        reusable pipeline and LeWM integration code
|-- scripts/                     auditable CLI entry points and validators
|-- tests/                       default-environment test suite
|-- docs/research/               evidence, protocols, results, claims, ADRs
|-- docs/roadmap/                gate roadmap and historical planning
|-- docs/workflows/              focused operational procedures
|-- configs/                     experiment/runtime configuration
|-- kaggle/                      validation-only launch packages
|-- paper/                       provisional manuscript and generated tables
|-- external/                    audited upstream references/submodules
|-- data/                        ignored raw/processed artifacts
`-- outputs/                     ignored run artifacts and approvals
```

`external/` is reference code unless an integration task explicitly changes that boundary.
Never modify upstream code merely to make local tests pass.

## 23. Command Center

### Pre-Flight And Release Checks

```powershell
git status --short --branch
git rev-parse HEAD
python --version
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
pre-commit run --all-files
```

### Default Environment

```powershell
uv venv
uv pip install -e ".[dev]"
```

### Gate 5 Package Dry-Run

Use placeholders and reviewed ignored paths. This command must remain `--dry-run` during a
documentation task.

```powershell
python scripts/prepare_lewm_kaggle_package.py `
  --source-root <ignored-train-validation-root> `
  --output-root <ignored-package-root> `
  --dataset-slug <private-dataset-slug> `
  --kernel-slug <private-kernel-slug> `
  --dataset-id <dataset-id> `
  --action-mode zero_action `
  --train-dataset-name <train-lance-name> `
  --validation-dataset-name <validation-lance-name> `
  --dry-run
```

### Gate 5 Package Audit

Package validation and push preflight produce audit records under the repository standing
authorization. These checks do not materialize or score the locked test.

### Strict Downloaded Artifact Validation

```powershell
python scripts/validate_lewm_kaggle_artifacts.py `
  --artifacts-root <ignored-downloaded-artifacts-root> `
  --output <ignored-validation-report.json>
```

Live uploads and kernel pushes follow `docs/workflows/kaggle_automation_policy.md`. Public
publishing additionally requires the policy's license, redistribution, and locked-test guards.

## 24. Paper And Defense Strategy

### Venue Scope

FISAT 2026 currently requires an English anonymized PDF in Springer LNICST format through
Confy+. The current `paper/main.tex` uses IEEEtran and is provisional. Migrate format before the
PDF freeze and add descriptive text/alt text for figures and tables.

The serious LeWM paper may now cite the exact Gate 7-9 pilot, but the strongest defensible framing
remains reproducibility, protocol, calibration failure, and negative/limited results.

### 30-Second Pitch

Game glitches often appear as impossible transitions rather than strange single frames. This
project builds a reproducible, leakage-aware pipeline to test whether a JEPA-style latent world
model trained on normal gameplay assigns higher surprise to glitches. We have verified the
runtime, checkpoint, real-data conversion, CUDA training, and a one-buggy-episode evaluation.
Broader non-locked validation and threshold calibration are the next unresolved evidence gaps.

### One-Minute Pitch

Manual game QA misses rare temporal failures. We frame glitch detection as normal-dynamics
modeling: encode gameplay, predict the next latent representation, and score prediction error.
The repository preserves shared CSV/JSON interfaces across simple visual baselines, a lightweight
latent proxy, Conv3D, and LeWM. Current evidence includes a tightly qualified one-buggy-episode
window-level pilot, not broad detection performance. A gated protocol separates validation
evidence from a one-time locked test and keeps the failed LeWM P95 operating point visible.

### Three-Minute Defense Outline

1. Explain why temporal dynamics matter and why static frames are insufficient.
2. Define latent surprise and distinguish action-conditioned from zero-action LeWM.
3. Show leakage-safe dataset protocols and shared interfaces.
4. State current evidence: Gates 1-4, partial Gate 5.
5. State missing evidence before presenting any method claim.
6. Compare fairly against simple and learned baselines after Gate 7.
7. Close with limitations, fallback scope, and reproducibility artifacts.

### Safe English Wording

- "We verify checkpoint-level integration and data-contract feasibility."
- "The current LeWM gameplay evaluation is a one-buggy-episode window-level pilot."
- "Validation evidence does not support a superiority claim."
- "Binary video labels do not support temporal localization."

If LeWM is weak, frame the paper around protocol hardening, domain/action mismatch, label
granularity, negative results, and lessons for reproducible game-QA anomaly research.

## 25. Reviewer Defense Bank

| Reviewer question | Safe answer | Evidence needed | If missing |
| --- | --- | --- | --- |
| Why LeWM? | It directly models latent future prediction and supports surprise scoring. | upstream paper/audit and Gate 7 | call it motivation, not validated benefit |
| Why latent over pixel? | Latents may suppress nuisance detail; this is a hypothesis. | baseline comparison | avoid superiority language |
| Why zero-action? | TempGlitch lacks verified actions; zeros preserve an explicit MVP adapter. | action-mode metadata | do not call it original action-conditioned LeWM |
| Why WOB? | It provides controlled episodes and recorded actions. | report 40 and replay audit | retain synchronization caveat |
| Why TempGlitch? | It directly targets temporal gameplay glitches and has public binary video data. | source/protocol records | limit to binary detection |
| Why no locked test? | The validation pilot is too narrow and LeWM P95 calibration failed. | reports 49-50 | say Gate 10 is intentionally closed |
| Is this SOTA? | No. The project does not claim SOTA. | broad comparisons would be required | state limitation |
| Did you train on glitches? | The target protocol is train-normal only. | split/training audit | no claim if audit missing |
| Is SIGReg proven useful? | Not in this project yet. | Gate 9 ablation | describe only as a method component |
| Is localization proven? | No; current TempGlitch artifact is binary per-video. | verified spans and temporal metrics | report clip/video detection only |

## 26. Risk Register

| Risk | Probability | Impact | Early warning | Mitigation | Fallback |
| --- | --- | --- | --- | --- | --- |
| Kaggle quota/VRAM | medium | high | OOM or quota exhaustion | tiny batch, accumulation, reduced smoke config | CPU engineering only; no Gate 5 claim |
| CUDA resume failure | medium | high | epoch does not advance or hashes differ | checkpoint each epoch; strict validator | fix infrastructure before Gate 6 |
| WOB action sync unavailable | medium | high | replay mismatch or unclear semantics | replay-based audit | use zero-action/action-free scope |
| TempGlitch binary labels | high | medium | no span file | video-level metrics and aggregation | no localization claim |
| LeWM below baseline | medium | high | AUROC/PR-AUC weak | diagnostics and failure analysis | negative-results paper |
| Checkpoint domain mismatch | high | medium | strict load works but predictions meaningless | train from scratch or encoder-only ablation | integration-feasibility claim only |
| Paper time compression | medium | high | Gate 7 slips past late June | freeze scope early | reproducibility/negative paper |
| Overclaim | medium | critical | wording exceeds registry | claim audit and reviewer pass | remove claim |
| Artifact leakage | low | critical | staged data/checkpoint/secret | pre-commit, release validator, staged scan | rotate secret and purge before push |
| Dependency drift | medium | high | strict load or loader breaks | exact pins and isolated runtime | freeze known runtime |

## 27. Definition Of Done

### Done For Gate 5

- Kaggle CUDA is recorded in `environment.json`.
- Training metadata records device `cuda`.
- Checkpoint resume advances the completed epoch.
- Config, dataset, and checkpoint hashes agree.
- Losses and collapse diagnostics are finite.
- Locked-test flags are false.
- Strict local validator passes.

### Done For Gate 7

- A real gameplay LeWM checkpoint is frozen.
- Validation-only `scores.csv` is finite and reproducible.
- Metrics and uncertainty are recorded.
- Action mode and score aggregation are explicit.
- Checkpoint/config/scores/metrics hashes exist.
- Claim registry allows qualified LeWM wording.

### Done For Gate 10

- Exactly one validation-selected configuration is frozen.
- A separate direct user command authorizes the frozen locked-test decision.
- Locked test is scored once.
- Frozen threshold is applied unchanged.
- Scores and metrics are hashed.
- Any invalidation or post-test change is disclosed.

### Done For The FISAT Paper

- Scope matches the highest passed gate.
- Manuscript uses Springer LNICST and anonymized submission formatting.
- Every table/figure traces to an artifact.
- Negative results and limitations remain visible.
- Claim registry, references, alt text, PDF, and page count pass review.
- Submission occurs by the internal early date when feasible.

### Done For Repository Release

- Tests, Ruff, format, release validator, claim validator, doctor, and pre-commit pass.
- Git contains no prohibited artifacts or credentials.
- README, AGENTS, RULES, PLAYBOOK, roadmap, and claims agree.
- Branch/SHA and skipped checks are documented.

## 28. Next Actions

| Priority | Owner | Action | Files/commands | Acceptance criteria | Main risk |
| --- | --- | --- | --- | --- | --- |
| 1, complete | owner | Merge/push governance foundation | `main` at `0ceef40` | governance files are on `origin/main` | none |
| 2, complete | Kaggle GPU Operator | Complete Gate 5 CUDA smoke/resume | reports 41-44 | strict validator passes | none |
| 3, complete | Dataset protocol engineer | Audit Gate 6 normal-only pilot source | reports 40 and 45, frozen split | normal-only source/pair-disjoint Lance inventories | none |
| 4, complete | LeWM Integration + ML Research Engineers | Run standing-authorized Gate 6 pilot | config and reports 45-46 | gameplay checkpoint, reload, finite diagnostics, validation encoding | none |
| 5, complete | ML Research Engineers | Run Gates 7-9 non-locked evaluation | reports 47-50 | finite same-manifest scores and pilot metrics | none |
| 6, complete | Kaggle GPU + ML Research Engineers | Validate the exact 500-update non-locked GPU profile | Roadmap v3 R0-R1, profile package and validator | strict profile artifacts pass; resource envelope recorded | none |
| 7, complete | ML Research Engineers | Confirm artifact-backed R4 rerun seed43/44 training archives | report 67, local SHA256 verification, per-seed validator outputs | local hashes match and both validators pass | none |
| 8, complete | ML Research Engineers | Complete R5 identical-episode evaluation on the non-locked research MVP | Roadmap v3 R5, reports 67-69, scoring and evaluation scripts | frozen inputs, provenance-bound outputs, no locked-test access | none |
| 9, complete | ML Research Engineers | Execute and verify the Kaggle-native `WOB-P0` audit | Roadmap v3 WOB section, reports 40, 67-71, downloaded Kaggle audit bundle, claim registry, context docs | verified bundle reports `READY_FOR_WOB_P1`, 120/120 non-locked rows resolved, 59 locked rows skipped, locked test remains closed | none |
| 10 | ML Research Engineers | Prepare the `WOB-P1` seed42 real-action train-normal Kaggle runner | Roadmap v3 WOB section, verified WOB-P0 bundle, seed42 cloud package, artifact validator, context docs | one-section seed42 runner exists, train-normal/validation-normal only, validation-buggy excluded from fit/select, locked test closed | runtime or packaging drift |
| 11 | Locked Test Release Officer | Keep locked test closed pending a frozen validation decision and separate direct command | release workflow | no materialization/scoring before frozen decision | schedule pressure |

Current recommended task: use the verified Kaggle-native `WOB-P0` bundle to prepare the
seed42-only `WOB-P1` real-action training runner, using the one-section notebook entrypoint
`cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh`. Do not execute WOB evaluation or touch
locked test without a later explicit command. Open seed43/44 only after seed42 artifacts pass.

## 29. Maintenance Rules For This Playbook

- Update this file whenever a gate changes status.
- Update `docs/research/16_claim_registry.md` whenever paper-facing wording changes.
- Update README and AGENTS when the compact status summary changes.
- Date every status update and name its evidence cutoff.
- Never delete historical context silently; mark it superseded and link the replacement.
- Keep commands fail-closed and distinguish dry-run from live action.
- Recheck venue rules from the official page before submission.

### How To Update This Document

1. Read the newest gate artifact and validator output.
2. Change status, evidence, missing items, and paper impact together.
3. Search for conflicting wording across README, AGENTS, roadmap, claims, workflows, and paper.
4. Add or update a safe claim registry entry.
5. Run the complete verification suite.
6. Record branch/SHA and unresolved risks.

## 30. Appendix: Status Vocabulary

| Term | Meaning |
| --- | --- |
| `verified` | Supported by a checked artifact, repository document, or primary source. |
| `engineering-smoke` | Small-scale proof of code/runtime behavior, not performance evidence. |
| `validation-only` | Uses validation data for diagnosis/selection; no locked-test claim. |
| `experiment-pending` | Required experiment has not run. |
| `blocked` | Cannot proceed until a named prerequisite or approval exists. |
| `rejected` | Evidence contradicts the statement; do not state it positively. |
| `future-work` | Planned only, with no current execution evidence. |
| `locked-test-closed` | Test data is unmaterialized/unscored and release is not authorized. |
| `paper-safe` | Wording stays within verified evidence and stated limitations. |
| `paper-unsafe` | Wording exceeds evidence or bypasses a gate. |
