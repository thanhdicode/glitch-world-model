# 99 - TempGlitch Follow-up Protocol

Date: 2026-06-24

## Executive Verdict

TempGlitch follow-up is the next main evidence lane.

It should proceed as a bounded non-locked TempGlitch follow-up built from the existing validated
`R5` TempGlitch artifact set, not from a new Kaggle run, not from retraining, and not from new
dataset access work.

This follow-up requires artifact-level recomputation only:

- reuse the existing `R5` raw score files and seed artifacts
- freeze a pair-disjoint calibration/evaluation split inside the already materialized validation
  pool
- recompute episode-level tables, metrics, confidence intervals, provenance, and a validator
  receipt

What remains blocked:

- no locked-test materialization or scoring
- no new LeWM training or Kaggle execution
- no temporal-localization claim
- no broad generalization, superiority, SIGReg-benefit, or SOTA claim

## Current Repository And Preflight State

- git commit inspected for this protocol freeze:
  `228f128559edb6154ff82143477b42f45fe84501`
- worktree status at protocol start:
  clean
- locked-test state:
  closed
- required safety flags confirmed from `outputs/r5_tempglitch_identical_episode/r5_metrics.json`
  and `outputs/r5_tempglitch_identical_episode/r5_provenance.json`:
  - `validation_buggy_used_for_fit_select=false`
  - `locked_test_materialized=false`
  - `locked_test_scored=false`

## Evidence Inventory

| Artifact | Path | Status | Notes |
| --- | --- | --- | --- |
| Train-normal Lance | `outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance` | present | Existing train-only fit source for LeWM and train-dependent baselines. |
| Validation-normal Lance | `outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance` | present | Contains the calibration/evaluation normal pool used by `R5`. |
| Validation-buggy Lance | `outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance` | present | Contains the buggy-positive evaluation pool used by `R5`. |
| Frozen `R5` manifest | `outputs/r5_tempglitch_identical_episode/r5_manifest.csv` | present | SHA256 `93327b661bd419944b57fb33112ec79264cb8a7b27708252c8507f3d3410f620`. |
| Manifest sidecar | `outputs/r5_tempglitch_identical_episode/r5_manifest.sha256` | present | Matches the frozen manifest receipt style. |
| Baseline raw scores | `outputs/r5_tempglitch_identical_episode/baseline_scores.csv` | present | Shared raw score file for `frame_diff` and `feature_distance`. |
| LeWM raw scores seed42 | `outputs/r5_tempglitch_identical_episode/lewm_scores_seed42.csv` | present | SHA256 recorded in `r5_metrics.json`. |
| LeWM raw scores seed43 | `outputs/r5_tempglitch_identical_episode/lewm_scores_seed43.csv` | present | SHA256 recorded in `r5_metrics.json`. |
| LeWM raw scores seed44 | `outputs/r5_tempglitch_identical_episode/lewm_scores_seed44.csv` | present | SHA256 recorded in `r5_metrics.json`. |
| Episode-level scores | `outputs/r5_tempglitch_identical_episode/episode_scores.csv` | present | Can be regenerated from the raw score files if needed. |
| Comparison table | `outputs/r5_tempglitch_identical_episode/r5_comparison.csv` | present | Support-matched across all recorded rows. |
| Metrics JSON | `outputs/r5_tempglitch_identical_episode/r5_metrics.json` | present | Complete status receipt for the validated `R5` family. |
| Provenance JSON | `outputs/r5_tempglitch_identical_episode/r5_provenance.json` | present | Captures hashes, seed artifacts, and environment. |
| Markdown report | `outputs/r5_tempglitch_identical_episode/R5_REPORT.md` | present | Human-readable summary of the non-locked `R5` family. |
| Seed metadata roots | `outputs/r5_tempglitch_identical_episode/_lewm_seed42/` through `_lewm_seed44/` | present | Gate 7 metadata receipts are retained per seed. |
| Gate 8 metadata | `outputs/r5_tempglitch_identical_episode/gate8_metadata.json` | present | Documents baseline fit provenance. |
| Dedicated TempGlitch validator receipt | none | missing | Next follow-up must add a cheap receipt or validator output. |
| Top-level command log for the `R5` family | none | missing | Next follow-up must emit an exact command log. |
| Precision / recall / balanced accuracy columns in `r5_comparison.csv` | absent | missing | Recompute from artifact-backed episode rows in follow-up outputs. |
| Phase 6D repeated-grouped artifacts | `outputs/tempglitch_phase6d/` | present, background only | Useful for protocol history, but not the primary next lane because it uses exposed sequential-subset test artifacts and legacy locked-test wording. |
| Phase 6D repeated summary status | `outputs/tempglitch_phase6d/phase6d_repeated_summary.json` | present, stale semantics | File reports `status: "dry-run only"` even though the directory also contains per-seed outputs; do not treat it as the main follow-up evidence receipt. |

## What This Follow-up Improves

Compared with the current bounded `R5-XGame` bundle, the TempGlitch follow-up is intended to
improve reviewer-facing evidence quality in four narrow ways:

1. It stays on the public TempGlitch benchmark lineage already documented in the repository.
2. It preserves a multi-category evaluation surface instead of the single-category `R5-XGame`
   field.
3. It can eliminate the current `R5` calibration/evaluation pair overlap without retraining or
   rescoring from scratch.
4. It can expand the reported metric surface and provenance receipts while keeping claim scope
   non-locked and bounded.

This follow-up is an evidence-quality upgrade, not a scientific reset and not a new model-training
lane.

## Current `R5` Split Caveat And Repair Decision

The validated `R5` manifest is source-disjoint by role, but its current calibration choice is not
fully pair-disjoint:

- current calibration episodes:
  - `Godot_Blinking_Normal_106`
  - `Godot_Animation_Platformer_Normal_18`
- observed cross-role pair overlap count in the current frozen manifest:
  `1`
- overlapping pair:
  `Stuck in Place/pair-environment:Platformer:index:18`

The existing validation pool already contains a repair path without new compute:

- pair-disjoint calibration-normal candidates available in the current artifact set:
  - `Godot_Blinking_Normal_106`
  - `Godot_Frozen_Animation_Platformer_Normal_107`

Freezing calibration to those two episodes yields:

- `2` calibration-normal episodes
- `12` evaluation normal-negative episodes
- `22` evaluation buggy-positive episodes
- `0` cross-role pair overlaps between calibration and evaluation

This pair-disjoint calibration freeze is the authoritative split decision for the next TempGlitch
follow-up.

## Frozen Follow-up Design

### Authoritative Inputs

The next follow-up must treat these as authoritative:

- `outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance`
- `outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance`
- `outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance`
- `outputs/r5_tempglitch_identical_episode/r5_manifest.csv`
- `outputs/r5_tempglitch_identical_episode/baseline_scores.csv`
- `outputs/r5_tempglitch_identical_episode/lewm_scores_seed42.csv`
- `outputs/r5_tempglitch_identical_episode/lewm_scores_seed43.csv`
- `outputs/r5_tempglitch_identical_episode/lewm_scores_seed44.csv`
- `outputs/r5_tempglitch_identical_episode/r5_metrics.json`
- `outputs/r5_tempglitch_identical_episode/r5_provenance.json`

Phase 6D outputs may inform protocol wording, but they are not the authoritative data surface for
this next main lane.

### Split And Leakage Policy

The follow-up must define three roles:

- `train_normal`: the existing train-normal Lance inventory only
- `calibration_normal`: exactly two validation-normal episodes
- `evaluation`: the remaining held-out validation-normal episodes plus all validation-buggy
  episodes

Required leakage contract:

- no overlap by `source`
- no overlap by `source_episode_id`
- no overlap by `pair_id`
- no overlap by video identity if a stable video identifier is available

Role-specific frozen rule:

- `train_normal` must remain separate from both calibration and evaluation
- calibration episodes must be selected from normal-only rows
- buggy rows must never be used for fitting or threshold selection
- evaluation metrics must be computed only on held-out evaluation rows

Frozen calibration decision for the next follow-up:

- `Godot_Blinking_Normal_106`
- `Godot_Frozen_Animation_Platformer_Normal_107`

Frozen evaluation support after that repair:

- total evaluation episodes: `34`
- normal-negative evaluation episodes: `12`
- buggy-positive evaluation episodes: `22`

### Metric Contract

Every compared row in the next follow-up must report:

- AUROC
- AUPRC
- F1
- precision
- recall
- balanced accuracy
- FPR@95TPR
- support counts:
  - calibration episode count
  - evaluation episode count
  - positive episode count
  - negative episode count
- confidence intervals when available

Confidence-interval rule:

- the primary grouped bootstrap key must be `pair_id`
- if a row lacks a usable `pair_id`, the implementation may fall back to `source_episode_id`
  only if the receipt records that fallback explicitly

### Method And Baseline Contract

Required compared families:

- `frame_diff`
- `feature_distance`
- LeWM seed `42`
- LeWM seed `43`
- LeWM seed `44`

Required aggregation surface for the immediate follow-up:

- `mean`
- `max`
- `top2_mean`

Support-matching rule:

- every compared row must be evaluated on the exact same frozen follow-up manifest
- every compared row must use the same calibration episodes
- every compared row must report the same evaluation support counts

`mini_latent` rule:

- not required for the immediate next main lane because there is no validated `R5`
  identical-manifest `mini_latent` result bundle in the current authoritative artifact set
- it may only be added later as an explicitly planned extension with the same split, support, and
  claim contract

### Artifact And Provenance Contract

The follow-up must emit a fresh, self-contained output directory, recommended as:

- `outputs/tempglitch_followup_pair_disjoint/`

Required output files:

- `followup_manifest.csv`
- `followup_manifest.sha256`
- `followup_episode_scores.csv`
- `followup_comparison.csv`
- `followup_metrics.json`
- `followup_provenance.json`
- `FOLLOWUP_REPORT.md`
- `followup_command.txt`
- `followup_validator_receipt.json`

Required provenance fields:

- manifest hash
- raw score hashes for every reused baseline and LeWM input file
- comparison hash
- metrics hash
- seed artifact hashes
- exact calibration episode IDs
- exact evaluation support counts
- exact command log
- validator receipt path or embedded validator payload
- `validation_buggy_used_for_fit_select=false`
- `locked_test_materialized=false`
- `locked_test_scored=false`

The validator receipt must fail closed on:

- manifest/score misalignment
- missing required methods
- role leakage by source, episode, or pair
- one-class evaluation
- missing metric fields
- any locked-test-looking path or true locked-test flag

## Claim Boundary

Allowed wording:

- "bounded non-locked TempGlitch follow-up"
- "within the frozen TempGlitch follow-up split"
- "supports further investigation"

Also allowed, if true after implementation:

- "artifact-only follow-up using existing validated R5 TempGlitch outputs"
- "pair-disjoint calibration repair"
- "support-matched comparison on the frozen follow-up manifest"

Forbidden wording:

- "LeWM detects glitches generally"
- "LeWM beats baselines" without an explicit frozen-split qualifier
- "SOTA"
- "generalizes across games"
- "locked-test performance"
- "SIGReg benefit"
- "temporal localization" unless explicitly evaluated

## Decision Gate

Chosen next single action:

- `Run bounded TempGlitch follow-up`

Why this option won:

- the authoritative `R5` TempGlitch artifact set is present
- the current follow-up can be frozen from already validated outputs
- a clean pair-disjoint calibration/evaluation split can be defined now
- no locked-test access is required
- no Kaggle launch, retraining, or new download is required

Execution scope of that next action:

- CPU-side artifact recomputation and validation only
- no new LeWM training
- no new Kaggle execution
- no new scientific claim outside the bounded non-locked follow-up split
