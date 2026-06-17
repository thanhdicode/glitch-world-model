# R5 Identical-Episode Evaluation Plan

Date: 2026-06-17

Status: planning-only; do not execute without an explicit command

This narrower TempGlitch-only planning note is complemented by
`docs/research/68_r5_tempglitch_and_wob_expansion_plan.md`, which records the controlled post-R5
World of Bugs gate and expansion sequence.

## Goal

Prepare the non-locked R5 identical-episode evaluation for LeWM and the comparable baselines under
one frozen manifest and one frozen reporting flow.

## Planned Inputs

- Artifact-backed R4 rerun checkpoints for seed43 and seed44.
- The existing seed42 artifact root once its local archive provenance is confirmed acceptable for
  the frozen evaluation family.
- The non-locked research MVP source and Lance inventories.
- The frozen non-locked protocol and claim boundary docs already recorded in the repository.

## Planned Methods

- LeWM latent surprise.
- Frame difference.
- Train-normal-fitted feature distance.
- Conv3D autoencoder if the existing Phase 6E artifacts and protocol remain compatible with the
  identical-episode manifest.
- Frozen video-representation baseline only if the current planning script is promoted into a
  protocol-compatible execution path.

## Planned Metrics

- Primary: AUROC.
- Primary: AUPRC.
- Secondary: F1 at a normal-calibrated threshold.
- Secondary: FPR@95TPR if the reporting path supports it cleanly.

## Safety

- Validation-only and non-locked.
- No validation-buggy data may be used for training or checkpoint selection.
- Locked test remains unmaterialized and unscored.
- No paper-facing detection-performance claim may be added until real R5 outputs exist.

## Current Building Blocks

- `scripts/run_gate7_lance_scoring.py --help`
- `scripts/run_gate7_lewm_evaluation.py --help`
- `scripts/run_gate8_baselines_from_lance.py --help`
- `scripts/plan_frozen_video_representation_baseline.py --help`
- `src/glitch_detection/video_eval.py`

## Current Gap

There is no single dedicated `R5` orchestration script on `main` that freezes the identical
episode manifest, runs LeWM plus all selected baselines, and emits one provenance-bound results
package. R5 execution should therefore freeze the exact command sequence before running.

## Acceptance Criteria

- All chosen checkpoints reload successfully.
- The exact non-locked identical-episode manifest is frozen before scoring.
- Every train-dependent baseline fits on allowed train-normal data only.
- Scores and metrics are written with provenance and hashable outputs.
- Claim registry updates wait until real R5 artifacts exist.

## Human Commands To Run Next

These are preparation-oriented command entry points only. Do not run them as part of this task.

```powershell
python scripts/run_gate7_lance_scoring.py --help
python scripts/run_gate7_lewm_evaluation.py --help
python scripts/run_gate8_baselines_from_lance.py --help
python scripts/plan_frozen_video_representation_baseline.py --help
```
