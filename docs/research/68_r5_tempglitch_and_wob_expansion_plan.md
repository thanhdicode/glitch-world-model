# R5 TempGlitch And WOB Controlled Expansion Plan

Date: 2026-06-17

Status: planning-only; do not execute R5 or WOB without an explicit command

## 1. Current Verified State

- Gates 1-8 passed at their documented engineering or evaluation level.
- Gate 9 completed as a limited validation-only, one-buggy-episode window pilot.
- The non-locked TempGlitch research MVP source is ready with 36 train-normal, 14
  validation-normal, and 22 validation-buggy episodes across all five categories.
- The exact 500-update LeWM GPU profile completed as engineering evidence only.
- R4 rerun seed43 and seed44 are artifact-backed after local SHA256 verification and per-seed
  validator passes.
- R5 identical-episode evaluation has not started.
- World of Bugs expansion has not started.
- Locked test remains closed, unmaterialized, and unscored.

## 2. R5 TempGlitch Goal

Freeze and execute one non-locked identical-episode evaluation family that compares LeWM with the
selected baselines on the same TempGlitch episode manifest and writes provenance-bound scores and
metrics.

## 3. R5 Inputs

- R3/R4 seed artifacts, with seed43 and seed44 now artifact-backed and seed42 remaining separately
  documented.
- The research MVP TempGlitch Lance inventories for train-normal, validation-normal, and
  validation-buggy.
- The frozen non-locked TempGlitch protocol and claim-boundary documents.
- No locked-test inputs.

## 4. R5 Methods

- LeWM latent surprise.
- `frame_diff`.
- Train-normal-fitted `feature_distance`.
- Conv3D autoencoder if the Phase 6E runner and artifacts remain protocol-compatible.
- Frozen video-representation baseline only if its optional dependency path is promoted into a
  protocol-compatible execution flow.

## 5. Metrics

- Primary: AUROC.
- Primary: AUPRC.
- Secondary: F1 at a normal-calibrated threshold.
- Secondary: FPR@95TPR if supported in the final reporting path.
- Uncertainty target: grouped episode-bootstrap confidence intervals.

## 6. Fairness Rules

- Every method must use the identical episode manifest and labels.
- Train-dependent methods fit on allowed train-normal data only.
- Thresholds and configuration choices stay on non-locked validation only.
- Ranking metrics and thresholded operating-point metrics are reported separately.
- Validation-buggy episodes are not used for training or checkpoint selection.

## 7. Exit Gate

- Chosen checkpoints reload successfully.
- The frozen identical-episode manifest is recorded.
- Score files and metrics files exist with hashes and provenance.
- Claim registry updates occur only after real R5 outputs exist.
- Locked test remains untouched.

## 8. WOB Expansion Gate

World of Bugs opens only after all of the following are true:

- R4 seed43 and seed44 remain artifact-backed.
- R5 TempGlitch identical-episode evaluation is complete.
- All R5 table cells trace to artifact hashes.
- No unresolved leakage or artifact-integrity issue remains.
- Claim registry wording is aligned to the actual TempGlitch evidence.
- Enough GPU budget exists for a controlled post-R5 run family.
- Locked test remains closed.

## 9. WOB Expansion Stages

- `R3-WOB`: materialize and train WOB real-action normal-only checkpoints.
- `R5-WOB`: run an identical-episode WOB evaluation family.
- `R5-XGAME`: compare TempGlitch and WOB under matched reporting rules.
- `R6-WOB`: run zero-action versus real-action/action-conditioning ablations.
- `R8`: upgrade paper positioning only if the combined evidence supports it.

## 10. Safe Claims And Forbidden Claims

Safe now:

- R4 seed43/44 rerun artifacts are local SHA256-verified and pass per-seed validators.
- R5 and WOB remain planning-only.

Forbidden now:

- Any R5 metric claim.
- Any WOB result claim.
- Broad LeWM glitch-detection, superiority, SOTA, SIGReg-benefit, temporal-localization, or
  locked-test claim.

## 11. Prompt-Ready Next Commands And TODO

Actual currently available commands and checks:

```powershell
python scripts/run_gate7_lance_scoring.py --help
python scripts/run_gate7_lewm_evaluation.py --help
python scripts/run_gate8_baselines_from_lance.py --help
python scripts/run_gate9_ablations.py --help
python scripts/plan_frozen_video_representation_baseline.py --help
python scripts/freeze_wob_protocol.py --help
```

Observed implementation gap:

- There is no single dedicated R5 orchestration command on `main` that freezes one identical
  episode manifest, runs LeWM plus all selected baselines, and emits one provenance-bound result
  bundle.
- There is no dedicated WOB training/evaluation orchestration family on `main`; only the protocol,
  reduced conversion, and planning-level components are present.

Required next work before execution:

1. Freeze the exact TempGlitch R5 manifest and output layout.
2. Decide whether Conv3D and frozen video representation are in or out for the first R5 run.
3. Define the exact score-merging and metric-reporting sequence.
4. If one-command orchestration is desired, implementation required.
