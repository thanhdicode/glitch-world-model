# LAST_HANDOFF.md

Last completed task: TempGlitch evidence registration and paper-readiness package
Commit: starting point `1509d1ccf97dc568fede9667d2bd6f30d59efbe6`; package commit recorded in final handoff
Date: 2026-06-24

## What Changed

- Revalidated the local gitignored TempGlitch follow-up bundle with status
  `followup_validated`.
- Registered the pair-disjoint support, metrics, uncertainty, leakage checks, flags, and exact
  artifact hashes in `docs/research/101_tempglitch_followup_results.md`.
- Added paper table, readiness, outline, and Kaggle-gate plans in reports 102-105.
- Added claims C-090 through C-092 and synchronized the paper claim map.
- Updated the manuscript scaffold with a main TempGlitch follow-up table and a separate bounded
  R5-XGame table.
- Kept all generated evidence artifacts uncommitted per repository policy.

## Evidence Summary

- Calibration normals: `2`.
- Evaluation: `12` normal-negative and `22` buggy-positive episodes.
- Cross-role `source_episode_id`, `pair_id`, and `source` overlap: `0`.
- Best LeWM: seed44 `lewm_l2_max` + episode `mean`, AUROC `0.7159`, AUPRC `0.8026`,
  F1 `0.7143`, AUROC CI `[0.5349, 0.8770]`.
- Best baseline AUROC: `feature_distance` + `top2_mean`, AUROC `0.6136`, AUPRC `0.7310`,
  F1 `0.1600`, AUROC CI `[0.4636, 0.7545]`.
- Best LeWM FPR@95TPR: `0.7500`; AUROC intervals overlap.

## Safety Status

- No training, Kaggle launch, new dataset download, new scoring, or locked-test access occurred.
- `validation_buggy_used_for_fit_select=false`.
- `locked_test_materialized=false` and `locked_test_scored=false`.
- No raw data, outputs, checkpoints, caches, or credentials were added to Git.

## Checks Passed

- Dedicated TempGlitch follow-up validator: `followup_validated`.
- Full tests, lint, format, release, claim, doctor, context, and pre-commit checks are required at
  close-out and recorded in the final handoff.

## Gate Status After Task

- TempGlitch follow-up: validated bounded pair-disjoint non-locked evidence.
- R5-XGame: unchanged bounded non-locked secondary evidence.
- R5-WOB: unchanged positive-probe only.
- Locked test: closed, unmaterialized, and unscored.

## Claim Boundary

Allowed: within the frozen non-locked TempGlitch follow-up split, the best LeWM configuration
shows stronger same-support separation than the recorded simple baselines, with small support,
wide/overlapping AUROC intervals, and high FPR stated beside the result.

Forbidden: broad superiority, SOTA, cross-game generalization, temporal localization, SIGReg or
action-conditioning benefit, WOB binary-benchmark performance, or locked-test performance.

## Open Blockers

- Small evaluation/calibration support, wide uncertainty, and high TempGlitch FPR@95TPR.
- No exact-support learned baseline or controlled SIGReg/action ablation.
- Official Springer-kit compile and final paper audit remain pending.

## Next Recommended Task

Build the first paper draft from the bounded TempGlitch and R5-XGame evidence package.

## Files Likely Relevant Next

- `docs/research/101_tempglitch_followup_results.md`
- `docs/research/102_paper_results_table_plan.md`
- `docs/research/104_paper_outline_lnicst_fisat.md`
- `docs/research/70_paper_claim_map.md`
- `paper/main.tex`
