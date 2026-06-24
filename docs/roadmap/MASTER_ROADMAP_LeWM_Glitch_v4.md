# MASTER ROADMAP V4 - Full Method-Paper Upgrade For Topic A

Date: 2026-06-24
Target submission window: FISAT 2026 / Springer LNICST
Status: CANONICAL execution roadmap (supersedes V3 for all next actions)
Supersedes: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md` (now historical input only)

## 0. Why V4 Exists

V3 closed the project at a bounded leakage-aware evaluation note with Path A ("finalize locally,
no Kaggle needed"). That framing is scientifically honest but contributes too little for a
conference that rewards substantial scientific contribution. V4 deliberately reopens the evidence
lane and upgrades the project from a *bounded evaluation note* into a *full empirical method paper*
for Topic A:

`Latent World Models for Video Game Glitch Detection: A JEPA-based Approach`

V4 does NOT relax the anti-overclaim rules. Every new claim still requires a validated artifact
before it may appear in the paper. The difference is that V4 actively builds the missing evidence
instead of documenting its absence.

## 1. Topic A Contract

- Proposed title: Latent World Models for Video Game Glitch Detection: A JEPA-based Approach.
- Main datasets: VideoGlitch / TempGlitch, GlitchBench, World of Bugs. Atari/Procgen auxiliary only.
- Hypothesis: gameplay glitches create abnormal latent dynamics versus normal gameplay; latent
  prediction error / surprise should separate buggy from normal videos.
- Method: train/adapt LeWM on normal gameplay; compute latent prediction error; threshold or a
  lightweight classifier flags glitches.
- Baselines: frame difference, feature distance, video autoencoder, CNN-LSTM, TimeSformer/
  VideoMAE-small, optional VLM detector.
- Strategic strength: aligned with game testing, public benchmarks, demo potential.

## 2. Starting Point (HEAD)

- Two validated non-locked binary families exist: TempGlitch pair-disjoint follow-up
  (12 normal-negative / 22 buggy-positive, 2 calibration normals) and R5-XGame
  (12 normal-negative / 60 buggy-positive).
- Only simple baselines (`frame_diff`, `feature_distance`) are scored on the exact support.
- No learned video baseline on exact support, no controlled SIGReg/action ablation, no public
  benchmark scoring, no temporal-localization metrics.
- Locked test remains closed.
- The Conv3D `video_autoencoder.py` and `run_kaggle_video_autoencoder.py` are complete but not yet
  run on the frozen follow-up support.

## 3. Upgrade Phases (P1-P7)

Each phase: objective, file-level tasks, Kaggle gate, output estimate, definition of done.
Codex executes ALL local research/code/paper work. The user only operates the Kaggle gates
(K1-K4) and submits the paper.

### Phase P1 - Statistical & Support Hardening (LOCAL, no Kaggle)

Objective: remove the statistical weaknesses reviewers will attack before spending GPU.

Tasks:
- `src/glitch_detection/statistics.py`: add `delong_auroc_test`, `paired_bootstrap_delta`; extend
  `_metric` for `auprc`, `balanced_accuracy`, `mcc`.
- `src/glitch_detection/analysis.py` (or new `seed_aggregation.py`): add `aggregate_seed_metrics`
  to report mean +/- std across seed42/43/44 instead of best-row.
- `src/glitch_detection/tempglitch_followup.py` + `scripts/freeze_tempglitch_protocol.py`: raise
  calibration normals 2 -> 4, use all 14 validation-normal episodes; keep leakage = 0; name episodes.
- `scripts/validate_tempglitch_followup.py`: enforce `calibration_normal_count >= 4`.
- Tests: `tests/test_statistics.py` (DeLong known-answer, paired bootstrap), `tests/test_seed_aggregation.py`.
- Register the paired delta-AUROC claim as `experiment-pending` in the claim registry.

Kaggle: none. Output: new statistics + tests pass; no new numbers yet (await P2 rerun).
DoD: full check suite green; commit `P1: add DeLong/paired-bootstrap stats, multi-seed aggregation, balanced calibration`.

### Phase P2 - Learned Baselines (LOCAL code + KAGGLE K1)

Objective: fill the biggest reviewer gap - no learned video baseline on exact support.

Tasks (local):
- Reuse `video_autoencoder.py` (complete) via `run_kaggle_video_autoencoder.py`; add a
  `--follow-up-manifest` path to score the P1 frozen split.
- New `src/glitch_detection/cnn_lstm.py`: per-frame CNN encoder + LSTM next-frame prediction;
  score = prediction MSE. Mirror the `VideoAutoencoderConfig` / `train_model` /
  `score_records_with_checkpoint` / `write_scores` interface.
- New `src/glitch_detection/video_transformer.py`: VideoMAE-small wrapper (pinned `transformers`);
  score = reconstruction/feature distance; guard `VideoTransformerUnavailableError`.
- Register all three in `src/glitch_detection/score_clips.py` `available_scorers()` (pluggable).
- New `scripts/run_kaggle_learned_baselines.py`: train+score the three baselines on the SAME
  train-normal manifest; per-baseline `scores.csv` + metadata + `.sha256`.
- New `scripts/validate_learned_baselines.py`: fit-on-train-normal-only, score alignment,
  leakage = 0, false locked-test flags.
- Tests (CPU-mock): `tests/test_cnn_lstm.py`, `tests/test_video_transformer.py`,
  `tests/test_learned_baselines_runner.py`.

Kaggle K1 (user): one notebook training+scoring AE, CNN-LSTM, VideoMAE on the frozen follow-up
train-normal and scoring the 14-normal + 22-buggy validation set.

Output estimate (do not pre-claim):
- AE / CNN-LSTM AUROC ~0.55-0.72; VideoMAE-small ~0.6-0.78 on small support.
- Scenario A: LeWM >= learned baselines but delta-AUROC CI overlaps -> "competitive/stronger
  observed, not significant".
- Scenario B: a learned baseline >= LeWM -> honest comparison study; still publishable, with the
  contribution shifting to the leakage-aware protocol plus a complete comparison.
DoD: full check suite green; commit `P2: add CNN-LSTM, VideoMAE baselines + unified Kaggle runner/validator`; print exact K1 inputs/command/expected outputs/acceptance criteria for the user.

### Phase P3 - GlitchBench Public Benchmark (LOCAL code + KAGGLE K2)

Objective: external validity and a published benchmark.

Tasks (local):
- Complete `scripts/download_glitchbench_subset.py`: full ingestion + Lance materialization.
- New `src/glitch_detection/glitchbench_protocol.py`: `validate_glitchbench_manifest` (fail-closed,
  mirror `r5_xgame_protocol.py`); binary label mapping; explicit image-level -> frame-level limit.
- New `scripts/freeze_glitchbench_split.py` + `scripts/validate_glitchbench_bundle.py`.
- Tests: `tests/test_glitchbench_protocol.py`.

Kaggle K2 (user): score LeWM (3 seeds) + 3 learned baselines + 2 simple baselines on the
GlitchBench subset, full metric suite + bootstrap CI.

Output estimate: a second independent public-benchmark table. GlitchBench is image-level and may be
harder; report honestly. If LeWM keeps its rank on both benchmarks the contribution is materially
stronger.
DoD: full check suite green; commit `P3: GlitchBench ingestion, protocol, frozen split, cross-benchmark scoring`; print exact K2.

### Phase P4 - SIGReg + Action-Conditioning Ablation (LOCAL code + KAGGLE K3)

Objective: unlock mechanistic claims that are currently forbidden.

Tasks (local):
- New `scripts/run_lewm_sigreg_ablation.py`: train LeWM SIGReg-ON vs SIGReg-OFF across
  seed42/43/44, same data/updates, using the `_sigreg` toggle in `lewm_training.py`.
- Action ablation: `ActionMode.ZERO_ACTION` vs `ActionMode.REAL` on the same split.
- Extend `scripts/validate_r6_ablations.py`: controlled-pair check (exactly one variable changed),
  same-data hash, false locked-test flags.
- Tests: `tests/test_sigreg_ablation.py`.

Kaggle K3 (user): one job training the SIGReg on/off x 3 seeds plus action variants; score
validation; output controlled comparison + delta-CI + DeLong from P1.

Output estimate:
- SIGReg-ON > OFF with delta-CI excluding 0 -> "SIGReg improves detection on this split" (verified).
- Otherwise -> "no measurable SIGReg benefit observed" (a valued honest negative result).
DoD: full check suite green; commit `P4: controlled SIGReg and action-conditioning ablations`; print exact K3.

### Phase P5 - Temporal Localization (LOCAL code + KAGGLE K4 optional)

Objective: address "glitches unfold over time".

Tasks (local):
- Determine whether WOB/GlitchBench expose true temporal spans; record the finding under `docs/research/`.
- If yes: new `src/glitch_detection/temporal_localization.py` converting `score_record_series`
  window surprise into predicted intervals; temporal IoU and temporal AP; reuse
  `scripts/plot_lewm_surprise_timeline.py`; tests `tests/test_temporal_localization.py`.
- If no: emit qualitative timeline figures only and label localization as future-work; do NOT claim
  localization metrics.

Kaggle K4 (optional): only if window-level re-scoring is required.
DoD: full check suite green; commit `P5: temporal localization metrics or documented future-work`.

### Phase P6 - Demo + Reproducibility (LOCAL, no Kaggle)

Objective: practical game-testing value.

Tasks:
- New `demo/run_glitch_demo.py` (built on `run_synthetic_demo.py`): run LeWM surprise on a sample
  gameplay video; emit a timeline + highlighted frames.
- `demo/README.md`; update `docs/research/15_reproducibility_checklist.md`.
DoD: full check suite green; commit `P6: reproducible glitch-detection demo`.

### Phase P7 - Full Paper Rewrite + Submission (LOCAL)

Objective: rewrite from bounded note to a full method paper using only artifact-validated numbers.

Tasks:
- `scripts/make_paper_tables.py`: regenerate `paper/tables/*.tex` from P2-P5 artifacts.
- Rewrite `paper/sections/04_method.tex`, `07_experiments.tex`,
  `08_results_bounded.tex` -> `08_results.tex`, `09_limitations.tex`, abstract/conclusion in `main.tex`.
- Rerun claim audit (`docs/research/106_first_bounded_paper_claim_audit.md`), reference/bib audit
  (110), anonymization (111), similarity (112).
- Build with the official Springer `llncs` kit on Overleaf (user uploads).
DoD: full check suite green + Overleaf-ready package; commit `P7: full method-paper rewrite + submission package`; print final submission checklist.

## 4. Kaggle Gate Summary (user actions only)

| Job | Phase | Content | Batched |
|---|---|---|---|
| K1 | P2 | Train + score AE, CNN-LSTM, VideoMAE | one run |
| K2 | P3 | Score LeWM + baselines on GlitchBench | one run |
| K3 | P4 | SIGReg on/off x action ablation, 3 seeds | one run |
| K4 | P5 | (Optional) window-level temporal re-score | optional |

All other work in P1, P2-local, P3-local, P4-local, P5-local, P6, P7 is LOCAL and autonomous for
Codex. Codex commits and pushes after each coherent phase and stops only at the Kaggle gates.

## 5. Claim Policy Under V4

- No new performance, superiority, SIGReg-benefit, action-benefit, cross-game, localization, or
  locked-test claim may appear in the paper until its supporting artifact is validated.
- After validation, claims expand strictly to match the validated numbers and their uncertainty.
- Locked test stays closed and still requires a separate direct user command plus a frozen
  validation decision.
- Negative results are reported honestly and count as contributions.

## 6. Definition Of Topic-A Completion

Topic A is complete for a bounded FISAT/Q3-level submission when:
- Learned baselines are scored on at least the TempGlitch follow-up support (P2).
- At least one public benchmark beyond TempGlitch is scored under a leakage-aware protocol (P3).
- A controlled SIGReg or action ablation exists, with an honest positive or negative readout (P4).
- Temporal localization is either measured or explicitly scoped as future-work (P5).
- The paper is rewritten as a method paper mapped to the claim registry (P7).
