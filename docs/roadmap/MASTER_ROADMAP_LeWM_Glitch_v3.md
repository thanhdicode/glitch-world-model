# MASTER ROADMAP V3 - Paper-Grade LeWM Glitch Detection

Date: June 13, 2026
Target submission deadline: July 20, 2026
Primary topic: **Latent World Models for Video Game Glitch Detection: A JEPA-based Approach**
Status: execution roadmap; unexecuted experiments remain `experiment-pending`.

## 1. Executive Decision

The project will pursue a real LeWM, normal-only, episode-level glitch-detection study. The
shortest credible path is not to add more speculative models. It is to complete one auditable
research track end to end:

1. profile the current LeWM training path on GPU;
2. freeze a feasible training schedule;
3. train three seeds on the leakage-checked non-locked research MVP;
4. evaluate all methods on identical non-locked episodes;
5. run only decision-relevant ablations;
6. freeze one validation decision;
7. write a paper whose claims match the resulting evidence.

The paper can remain scientifically useful if LeWM underperforms. A well-controlled negative
result about latent-surprise ranking and normal-only calibration is preferable to an unsupported
superiority claim.

## 2. Verified Starting Point

As of Git commit `e3ba66b`:

- Gates 1-8 passed.
- Gate 9 is a limited validation-only pilot using one buggy episode and correlated windows.
- Real LeWM CUDA training, checkpoint reload, surprise scoring, and same-manifest baseline
  comparison have engineering evidence.
- The research MVP source contains 36 train-normal, 14 validation-normal, and 22
  validation-buggy TempGlitch episodes across five categories.
- The research MVP has zero selected source/pair overlap between train and validation.
- TempGlitch uses zero actions and supports binary episode-level evaluation in this repository.
- World of Bugs provides a future real-action controlled path.
- The exact 500-update GPU profile harness and paper-grade multi-seed run are not complete on
  `main`.
- Locked test is closed, unmaterialized, and unscored.

## 3. Research Questions

### Primary

**RQ1.** Does a lightweight LeWM trained only on normal gameplay assign higher latent-transition
surprise to unseen non-locked buggy episodes than to unseen normal episodes?

### Secondary

**RQ2.** How does LeWM latent surprise compare with frame difference, train-normal feature
distance, Conv3D autoencoding, and a frozen video-representation baseline under identical
episode-level evaluation?

**RQ3.** Does normal-only threshold calibration produce a usable operating point, even when
ranking metrics are above chance?

**RQ4.** Which components materially change the result: SIGReg, surprise distance, temporal
aggregation, training budget, and action conditioning in a controlled World of Bugs study?

## 4. Claim Scope

### Allowed Before New Experiments

- Reproducible LeWM engineering integration.
- Bounded normal-only CUDA training and strict artifact validation.
- Exact qualified Gate 7-9 pilot findings and limitations.
- Research MVP source readiness.

### Candidate Claims After Validation Evidence

- LeWM latent surprise was evaluated for binary episode-level gameplay glitch detection.
- Under the frozen non-locked protocol, LeWM achieved the exact reported ranking and calibrated
  operating-point metrics.
- Specific ablation effects may be reported only when repeated-seed evidence supports them.

### Forbidden Without New Direct Evidence

- State of the art or broad superiority.
- Temporal localization or temporal IoU from TempGlitch.
- Real-time operation.
- SIGReg benefit.
- Action-conditioned TempGlitch LeWM.
- Neural locked-test performance.

## 5. Critical Path

```text
R0 protocol freeze
  -> R1 exact 500-update GPU profile
  -> R2 freeze main-run schedule
  -> R3 seed 42 end-to-end validation
  -> R4 seeds 43 and 44
  -> R5 identical-episode baselines and grouped evaluation
  -> R6 minimal ablations and failure analysis
  -> R7 validation decision and locked-test go/no-go
  -> R8 paper, artifacts, and defense package
```

Only R7 may propose locked-test release. It still requires a separate direct user command.

## 6. Stage R0 - Protocol And Package Freeze

**Objective:** ensure the profile package is executable and immutable before spending GPU time.

### Required Work

- Confirm the current research config and dataset inventory hashes.
- Implement update-based training control; `500 optimizer updates` must not mean epochs or
  dataloader batches skipped by accumulation.
- Add fail-closed rejection of validation-buggy and locked-test inputs in the profile path.
- Ensure Kaggle packaging is idempotent and cannot collide with pre-existing materialization
  directories.
- Run local package dry-run, credential scan, license/protocol checks, and focused tests.

### Exit Gate

- Exact launch package and validator exist on a clean Git SHA.
- No live retry is made against a known packaging/materialization failure.
- Research config, package inventory, and expected artifacts are frozen.

## 7. Stage R1 - Exact 500-Update GPU Engineering Profile

**Objective:** measure feasibility, not detection performance.

### Fixed Protocol

- Exactly 500 optimizer updates.
- Train-normal only for optimization.
- Eight validation-normal batches for pipeline verification only.
- Initial batch size 8 with AMP enabled; OOM fallback changes the fingerprint.
- No validation-buggy scoring.
- No AUROC, AUPRC, detection claim, or research conclusion.

### Required Pre-Run Metadata

- Git SHA and branch.
- Dataset manifest/inventory hashes.
- Config hash.
- Batch size and AMP state.
- Python, CUDA, PyTorch, GPU, and Kaggle runtime information.
- Unique immutable run fingerprint.

### Required Logs

- Start/end timestamps and wall-clock runtime.
- Updates completed and updates/second.
- Peak VRAM and average VRAM when available.
- Checkpoint save/reload timestamps.
- Failed-attempt logs, tracebacks, fingerprints, and retry history.

### Required Validation

- Model weights reload.
- Optimizer state reload.
- Scheduler state reload if present.
- Resumed update count equals the expected count.
- All required artifact hashes verify.

### Required Deliverables

- `PROFILE_REPORT.md`
- `profile_metadata.json`
- `artifact_manifest.json`
- `environment_snapshot.json`
- `checkpoint_hashes.json`
- `retry_history.json`
- `validator_report.json`

### Exit Gate

- Local strict validator passes the downloaded profile artifacts.
- A feasible batch size, throughput estimate, VRAM envelope, evaluation interval, checkpoint
  interval, and projected main-run budget are recorded.

## 8. Stage R2 - Freeze Main-Run Schedule

**Objective:** convert profile evidence into one predeclared training protocol.

### Frozen Decisions

- Batch size, AMP, workers, pin-memory, and gradient clipping.
- Target optimizer updates, initially 15,000 unless profile evidence requires a documented
  revision.
- Full validation-normal evaluation interval.
- Checkpoint interval and resume policy.
- Early stopping after five non-improving full validation-normal evaluations.
- Seeds 42, 43, and 44.
- Best checkpoint selected by validation-normal prediction loss only.

### Exit Gate

- One config family is frozen before main training.
- Any change after freeze creates a new experiment family and is disclosed.

## 9. Stages R3-R4 - Paper-Grade Multi-Seed Training

**Objective:** produce three independently validated LeWM checkpoints.

### Run Order

1. Run seed 42 end to end.
2. Download and validate every artifact locally.
3. Repair protocol/infrastructure defects before launching more seeds.
4. Run seeds 43 and 44 only after seed 42 passes.

### Required Per-Seed Evidence

- Immutable fingerprint and complete environment snapshot.
- Full loss history and collapse diagnostics.
- Best and latest checkpoint hashes.
- Model/optimizer/scheduler reload validation.
- Resume evidence.
- Exact update count and early-stop state.
- False locked-test flags.

### Abort Conditions

- Non-finite loss or latent diagnostics.
- Dataset/config hash mismatch.
- Invalid resume count.
- Validation-buggy or locked-test access during fitting/selection.
- Repeated failure with no changed fingerprint or diagnosis.

## 10. Stage R5 - Identical-Episode Evaluation

**Objective:** compare methods fairly on the same non-locked validation episodes.

### Evaluation Unit

- Primary: episode/video.
- Diagnostic only: windows/transitions.

### Methods

- LeWM latent surprise.
- Frame difference.
- Train-normal-fitted feature distance.
- Conv3D autoencoder.
- One frozen video-representation baseline.
- CNN-LSTM or VideoMAE only if protocol-compatible implementation is completed without delaying
  the critical path.

### Metrics

- Primary: AUROC and AUPRC.
- Secondary: F1 at a normal-calibrated threshold and FPR at 95% TPR.
- Uncertainty: 95% grouped episode-bootstrap intervals.
- Report per-category results with small-sample cautions.

### Fairness Rules

- Identical episode manifest and labels for every method.
- Train-dependent methods fit on train-normal only.
- Configuration and threshold selection use non-locked validation only.
- Ranking and threshold-calibration outcomes are reported separately.
- No cherry-picking across seeds, aggregations, or checkpoints.

### Exit Gate

- Every table cell traces to a score/metric hash and config fingerprint.
- Calibration failures and negative results remain visible.

## 11. Stage R6 - Minimal Decision-Relevant Ablations

Run ablations only after the main three-seed result exists.

| Priority | Ablation | Question | Minimum Evidence |
| --- | --- | --- | --- |
| P0 | SIGReg default vs zero | Does SIGReg change collapse/ranking? | repeated seeds |
| P0 | mean vs max vs top-2 aggregation | Is anomaly evidence sparse? | identical scores/manifests |
| P1 | MSE/L2 vs cosine surprise | Is ranking distance-sensitive? | frozen checkpoints |
| P1 | reduced vs full training budget | Does additional optimization help? | predeclared budgets |
| P2 | zero-action vs real-action WOB | Does action conditioning matter? | controlled WOB protocol |

Stop adding ablations when they no longer change the paper's main conclusion.

## 12. Stage R7 - Validation Decision And Locked-Test Go/No-Go

### Go Criteria

- Three seed checkpoints and scores pass strict validation.
- Episode-level metrics and uncertainty are complete.
- One configuration, checkpoint-selection rule, aggregation, and threshold rule are frozen.
- The claim registry names the exact allowed claim scope.
- No unresolved leakage, artifact-integrity, or calibration defect remains.

### No-Go Criteria

- Ranking remains indistinguishable from chance with wide uncertainty.
- Normal-only calibration remains unusable and the paper cannot frame it honestly.
- Results depend on one category, one episode, one seed, or post-hoc selection.
- Protocol or artifact integrity is unresolved.

### Locked-Test Rule

Even after a Go decision, do not materialize or score locked test without a separate direct user
command naming the frozen configuration and claim scope. One score only; no post-test tuning.

## 13. Stage R8 - Paper And Defense Package

### Paper Positioning

Preferred evidence-backed title:

> Latent World Models for Video Game Glitch Detection: A Leakage-Aware Evaluation of JEPA-Based
> Latent Surprise

If performance is weak, use:

> Evaluating Latent-Surprise World Models for Video Game Glitch Detection: Protocol, Calibration,
> and Failure Modes

### Required Tables

1. Dataset provenance and split audit.
2. Main episode-level results with uncertainty.
3. Normal-calibrated operating-point results.
4. Minimal ablation results.
5. Runtime, throughput, VRAM, and parameter count.
6. Failure-mode and per-category analysis.

### Required Figures

1. End-to-end method and evaluation protocol.
2. Training/validation loss plus collapse diagnostics.
3. Episode score distributions.
4. Representative success and failure timelines, clearly labeled diagnostic.
5. Calibration/ranking trade-off visualization.

### Submission Requirements

- English, anonymized Springer LNICST manuscript.
- Reproducible commands and artifact hashes.
- Accessibility text for figures/tables.
- Negative results and limitations visible.
- No claims beyond the registry.

## 14. Execution Calendar

The calendar is aggressive and assumes available GPU quota and prompt turnaround.

| Date | Milestone | Deliverable |
| --- | --- | --- |
| Jun 13-15 | R0 | profile harness/package/validator ready on clean SHA |
| Jun 15-16 | R1 | validated 500-update profile and frozen resource envelope |
| Jun 16-17 | R2 | main-run schedule frozen |
| Jun 17-20 | R3 | seed 42 completed and validated |
| Jun 20-25 | R4 | seeds 43 and 44 completed and validated |
| Jun 25-30 | R5 | identical-episode baseline/evaluation table |
| Jun 30-Jul 5 | R6 | minimal ablations and failure analysis |
| Jul 5-7 | R7 | validation decision; locked test remains separately gated |
| Jul 7-14 | R8 | manuscript, figures, tables, artifact index |
| Jul 14-18 | Internal review | claim audit, reproducibility rehearsal, defense |
| Jul 18-20 | Submission buffer | format, anonymization, accessibility, upload |

## 15. Compute Strategy

- Use Kaggle T4/P100 or equivalent cloud GPU for profile and main runs.
- Prefer sequential seed execution until seed 42 validates.
- Parallelize independent baselines and paper generation only after the main protocol freezes.
- Preserve resumable checkpoints and immutable evidence for every attempt.
- Additional compute does not justify uncontrolled search; predeclare experiment families.

## 16. Root Causes Of Prior Execution Friction

The project has experienced avoidable delay for identifiable engineering reasons:

1. **Profile implementation and live execution were mixed too early.** A remote run reached a
   Lance materialization collision before the profile harness had a fully validated clean-main
   implementation.
2. **A directory-copy operation was not idempotent.** Retrying against an existing destination
   produced `FileExistsError` before training.
3. **The operational state was split across main, an isolated worktree, local ignored artifacts,
   and chat context.** A GitHub-only agent cannot infer those uncommitted fixes.
4. **Full validation was sometimes repeated during exploration.** Focused tests should be used
   while iterating; the full release suite belongs at the final gate.
5. **Task switching interrupted the remote-training loop.** Long-running live execution needs one
   explicit terminal condition and preserved handoff evidence.
6. **Old roadmap documents contained optimistic assumptions and unsafe draft claims.** They made
   the true next action less obvious.

Roadmap v3 addresses these by separating package freeze, profile, schedule freeze, multi-seed
training, evaluation, and paper gates.

## 17. Definition Of Done

The project is ready for a genuine paper submission when:

- the main LeWM method has validated multi-seed episode-level evidence;
- all required baselines use an identical leakage-checked protocol;
- uncertainty, calibration, ablations, and failure analysis are complete;
- every result traces to immutable artifacts and hashes;
- claims match the registry;
- locked-test use, if any, followed the separate one-time release rule;
- the manuscript, figures, tables, code, and reproducibility instructions pass internal review.
