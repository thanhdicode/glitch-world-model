# Paper Claim Map

Date: 2026-06-18

Status: active paper-writing control document

## Purpose

This document is the paper-writing control surface for the Springer/LNICST scaffold. A sentence is
paper-safe only if it is covered here or by a later verified update.

## Paper-Facing Claim Classification

| Claim | Status | Evidence | Allowed wording | Forbidden overclaim |
| --- | --- | --- | --- | --- |
| The repository contains a provenance-bound, non-locked, validation-only R5 TempGlitch identical-episode evaluation bundle. | allowed now | `docs/research/69_r5_tempglitch_identical_episode_results.md` | "provenance-bound non-locked R5 TempGlitch validation-only family" | "final test-set result" |
| The frozen R5 family uses LeWM artifact-backed checkpoints for seed42, seed43, and seed44, plus `frame_diff` and train-normal-fitted `feature_distance` baselines. | allowed now | `docs/research/69_r5_tempglitch_identical_episode_results.md` | "within the frozen R5 family" | "complete benchmark comparison" |
| Thresholds are derived from the 95th percentile of two calibration-normal episode scores. | allowed now | `docs/research/69_r5_tempglitch_identical_episode_results.md` | "normal-calibrated threshold in this validation family" | "deployment-calibrated detector" |
| Primary metrics are AUROC and AUPRC; secondary metrics are F1 at the calibrated threshold and FPR@95TPR. | allowed now | `docs/research/69_r5_tempglitch_identical_episode_results.md` | "reported metrics for R5" | "all metrics needed for deployment" |
| The best observed AUROC and AUPRC rows in the frozen R5 family come from seed44 LeWM variants. | allowed now | `docs/research/69_r5_tempglitch_identical_episode_results.md` | "best observed rows in this frozen family" | "LeWM is broadly superior" |
| The strongest bounded F1 row in the frozen R5 family comes from `frame_diff` with mean episode aggregation. | allowed now | `docs/research/69_r5_tempglitch_identical_episode_results.md` | "strongest F1 row in this frozen family" | "baseline proves LeWM fails generally" |
| `locked_test_materialized = false`. | allowed now; required flag | `docs/research/16_claim_registry.md`, `docs/research/69_r5_tempglitch_identical_episode_results.md` | exact flag value | any locked-test result |
| `locked_test_scored = false`. | allowed now; required flag | `docs/research/16_claim_registry.md`, `docs/research/69_r5_tempglitch_identical_episode_results.md` | exact flag value | any locked-test score |
| `validation_buggy_used_for_fit_select = false`. | allowed now; required flag | `docs/research/69_r5_tempglitch_identical_episode_results.md` | exact flag value | validation-buggy used for threshold or fit |
| World of Bugs is a controlled expansion track and is not part of the current bounded results section. | allowed now | `PLAYBOOK.md`, `docs/research/16_claim_registry.md` | "status-only controlled expansion track" | WOB training/evaluation result |
| The repository provides a non-locked `R5-WOB` runner/validator bundle, but no validated WOB evaluation outputs exist yet in the current paper state. | allowed now | `docs/research/82_r5_wob_nonlocked_evaluation_pipeline.md` | "pipeline-ready controlled expansion track" | any WOB metric or outcome statement |
| Final FISAT abstract. | pending evidence | final claim audit, source matrix, validated manuscript compile | TODO only | final performance summary before evidence freeze |
| Ablation results. | pending evidence | future validated ablation artifacts | TODO only | ablation effect, SIGReg benefit, or causal mechanism claim |
| WOB-P1 seed42 results. | pending evidence | future seed42 artifact bundle and validator | separate empirical gate only | WOB evaluation or multi-seed result |

## Forbidden Claim Surfaces

- LeWM is state of the art.
- LeWM is broadly superior.
- The repository contains a locked-test result.
- The current paper includes WOB training or WOB evaluation performance.
- The current evidence demonstrates SIGReg benefit.
- The current evidence demonstrates real-time capability.
- The current evidence demonstrates temporal localization.
- The current evidence demonstrates cross-game generalization beyond the bounded family.

## Evidence Anchors

- [docs/research/16_claim_registry.md](<C:/Users/ADMIN/Desktop/glitch-world-model/docs/research/16_claim_registry.md>)
- [docs/research/69_r5_tempglitch_identical_episode_results.md](<C:/Users/ADMIN/Desktop/glitch-world-model/docs/research/69_r5_tempglitch_identical_episode_results.md>)
- [PLAYBOOK.md](<C:/Users/ADMIN/Desktop/glitch-world-model/PLAYBOOK.md>)
- [paper/main.tex](<C:/Users/ADMIN/Desktop/glitch-world-model/paper/main.tex>)
- [paper/references.bib](<C:/Users/ADMIN/Desktop/glitch-world-model/paper/references.bib>)

## Usage Rule

When a section is expanded, update this file first if the new prose adds any claim not already
covered above.
