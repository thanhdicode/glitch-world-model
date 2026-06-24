# MASTER ROADMAP V3 - Leakage-Aware LeWM Glitch Evaluation

Date: 2026-06-23
Target submission window: FISAT 2026 / Springer LNICST
Status: SUPERSEDED by `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md` (historical input only)

> NOTE: V3 closed the project at a bounded evaluation note (Path A, no Kaggle). V4 reopens the
> evidence lane and upgrades the project into a full empirical method paper (phases P1-P7).
> For all next actions read `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md` instead of this file.

Status (historical): canonical execution roadmap

## 1. Executive Position

The repository has crossed the engineering-completion threshold and is now in the scientific
discrimination stage. The safest paper framing is:

`a leakage-aware empirical evaluation of latent surprise for gameplay glitch detection`

Do not frame the project as:

- state of the art
- a fully solved gameplay QA system
- a cross-game generalized detector
- a temporal-localization system

## 2. Verified Scientific State

- TempGlitch Gates 1-8 are passed.
- TempGlitch Gate 9 completed as a limited non-locked validation family and remains bounded by its
  documented limitations.
- R5 TempGlitch remains the strongest verified binary-family evidence in the repository, but it is
  still non-locked and not a broad benchmark-superiority result.
- `R5-WOB` completed and was validated as a provenance-bound non-locked positive-probe /
  proof-of-execution bundle.
- `R5-WOB` demonstrates pipeline execution and class-conditional signal presence only.
- `R5-WOB` is not a valid binary benchmark because it contains zero
  `evaluation_normal_negative` episodes.
- The `R5-XGame` split, runner, package, and validator exist, and the downloaded bundle now passes
  local output-dir and tarball intake validation after a packaging-only repair.
- The repaired `R5-XGame` tarball SHA256 is
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`.
- `R5-XGame` now provides bounded non-locked binary validation evidence, with the best recorded
  configuration reaching AUROC approximately `0.91` on the frozen split.
- Locked test remains closed.

## 3. Claim Boundary

### Allowed now

- Engineering completion and auditability of the LeWM-based pipeline.
- The exact bounded TempGlitch Gate 7-9 and R5 family findings already registered in the claim
  registry.
- R5-WOB as a provenance-bound positive-probe bundle proving execution and signal presence under a
  normal-calibrated threshold.
- R5-XGame tooling readiness, manifest freeze, leakage audit, validated intake receipt, and the
  bounded non-locked AUROC approximately `0.91` summary on the frozen split.

### Forbidden until new evidence exists

- Any claim that `R5-WOB` is a valid binary benchmark.
- Any broad `R5-XGame` performance, generalization, or final-benchmark claim beyond the exact
  validated split.
- Broad glitch-detection superiority or state-of-the-art language.
- Cross-game generalization claims.
- Action-conditioning benefit claims.
- SIGReg benefit claims.
- Temporal-localization claims.
- Locked-test performance claims.

## 4. Canonical Phase Map

### Phase A - Evidence Stabilization / R5-WOB Freeze

Status: complete, with residual evidence gaps.

Meaning:

- Engineering success is verified.
- Positive-probe signal existence is verified.
- Binary discrimination is not established.

Required stance:

- Preserve the artifact inventory and validated intake receipts.
- Keep the zero-negative limitation explicit in every paper-facing summary.
- Use the following safe wording when needed:

`A provenance-bound non-locked positive-probe evaluation demonstrating pipeline execution and
class-conditional signal presence under a normal-calibrated threshold, but not yet a complete
binary benchmark.`

### Phase B - R5-XGame Binary Discrimination

Status: complete as an intake-validated non-locked bundle with bounded claim scope.

Purpose:

- Convert the project from proof-of-execution / proof-of-signal into proof-of-discrimination.

Frozen protocol:

- `train_normal`
- `calibration_normal`
- `evaluation_normal_negative`
- `evaluation_buggy_positive`

Claim rule:

- Treat only the locally validated bundle as evidence. The packaging repair that made the tarball
  intake-valid did not create a new scientific run.

Required metrics after successful validation:

- AUROC
- AUPRC
- F1
- precision
- recall
- balanced accuracy
- FPR@95TPR
- bootstrap confidence intervals
- per-seed reporting
- category breakdowns where supported

### Phase C - Target Benchmark Preparation

Status: parallel-prep only.

Priority order:

1. TempGlitch contract-check and smoke protocol for the next benchmark-quality lane.
2. VideoGlitchBench public-artifact and access verification as a stretch/public-access lane.
3. GlitchBench and related-work benchmark context as auxiliary documentation only.

Goal:

- Move from WOB-controlled evidence toward stronger gameplay-video benchmark relevance without
  opening new execution claims prematurely.

### Phase D - Baselines and Ablation

Status: design/prep only until Phase B validation succeeds.

Baseline plan must cover:

- `frame_diff`
- `feature_distance`
- video autoencoder
- temporal CNN / CNN-LSTM / ConvLSTM
- optional frozen VideoMAE or TimeSformer-small if protocol-compatible

Ablation plan must cover:

- score type
- aggregation
- threshold rule
- temporal smoothing
- calibration-size sensitivity
- seed stability
- action vs no-action where supported

Rule:

- No ablation result becomes empirical evidence before Phase B intake validation, unless the work is
  explicitly labeled smoke-only or design-only.

### Phase E - Paper Package

Status: scaffold/prep only.

Allowed now:

- introduction outline
- related-work update
- protocol/method section
- figure and table templates
- limitations skeleton
- reviewer FAQ
- FISAT/Springer submission memo

Blocked until validated metrics exist:

- final abstract
- final conclusion
- main results table
- superiority language
- stronger title wording

## 5. Parallel Work While Phase B Runs

The following lanes are allowed immediately:

- roadmap/docs cleanup
- claim registry synchronization
- current-state and paper-readiness updates
- TempGlitch contract-check planning
- VideoGlitchBench access-note planning
- baseline-suite design
- ablation-matrix design
- figure/table blueprints
- reviewer FAQ
- negative-result discussion skeleton
- FISAT/Springer submission memo

The following remain blocked:

- main binary results table
- final abstract and conclusion
- final paper claims
- cross-source comparison table
- Phase D metric conclusions
- locked-test access

## 6. Immediate Gate Logic

Phase B is complete only after all of the following are true:

1. `r5_xgame_outputs.tar.gz` is downloaded.
2. `r5_xgame_outputs.tar.gz.sha256` is downloaded.
3. `r5_xgame_staged.log` is retained.
4. `scripts/validate_r5_xgame_output_bundle.py` passes.
5. The claim registry and current-state docs are updated from the validated intake, not from remote
   status alone.

Status on 2026-06-23: satisfied by the repaired bundle with tarball SHA256
`65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`.

If a future bundle fails intake:

- keep it out of evidence
- preserve the log
- classify the failure
- patch only the direct cause

## 7. Paper Strategy

The paper should emphasize:

- leakage-aware evaluation discipline
- conservative claim control
- normal-only calibration
- binary discrimination once Phase B validates
- negative-result honesty where evidence is weak

The paper should not promise:

- a universal glitch detector
- temporal localization
- cross-game generalization
- locked-test readiness

## 8. Next Recommended Actions

1. Keep the canonical claim boundary synchronized across roadmap, current-state, and paper docs.
2. Wait for the staged Phase B Kaggle outputs to complete and be downloaded.
3. Validate the bundle locally before recording any metric.
4. Use the parallel-prep lanes to harden the eventual paper package without inventing unvalidated
   empirical claims.
