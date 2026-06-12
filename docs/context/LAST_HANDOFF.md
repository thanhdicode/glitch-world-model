# LAST_HANDOFF.md

Last completed task: Gate 7-9 non-locked LeWM evaluation pilot
Commit: evaluation code `f22e1be92fed098752069616deb7ed2b26b8fcc1`
Date: 2026-06-12

## What Changed

- Built a canonical 10,081-window manifest from Gate 6 validation-normal and non-locked buggy
  Lance datasets.
- Generated finite MSE/L2 transition scores from the frozen Gate 6 v8 best weights.
- Scored frame-difference and train-normal-fitted feature-distance baselines on the exact same
  ordered `window_id` rows.
- Evaluated AUROC/AUPRC and grouped normal-P95 F1 for six LeWM aggregations and two baselines.
- Updated evidence reports, claim boundaries, roadmap, playbook, README, and context generation.

## Checks Passed

- Gate 7 artifact validation: 10,081 ordered finite score rows and matching hashes.
- Gate 8 artifact validation: 10,081 same-manifest finite baseline rows.
- Gate 9 artifact validation: eight finite metric rows with calibration-only thresholds.
- Research release, claim registry, and context cache validators passed before final full-suite
  verification.

## Safety Status

- All evaluation used validation-only, non-locked Lance datasets.
- Locked test was not materialized or scored.
- Kaggle fallback was unnecessary because local CPU scoring succeeded.
- No data, outputs, Lance datasets, checkpoints, caches, or credentials are tracked.

## Gate Status After Task

- Gates 1-8 passed.
- Gate 9 passed as a limited one-buggy-episode window-level pilot.
- Gate 10 remains closed.

## Open Blockers

- Evaluation contains one buggy episode and correlated windows.
- Every LeWM grouped normal-P95 threshold produced zero recall and F1 despite finite AUROC/AUPRC.
- Broad LeWM superiority, SIGReg benefit, temporal localization, and locked-test claims remain
  unsupported.

## Next Recommended Task

- Broaden non-locked buggy validation coverage and investigate robust validation-only threshold
  calibration before any Gate 10 decision.

## Files Likely Relevant Next

- `docs/research/47_gate7_lewm_surprise_scoring_results.md`
- `docs/research/48_gate8_same_manifest_baseline_comparison.md`
- `docs/research/49_gate9_minimal_ablation_results.md`
- `docs/research/50_results_claim_boundary.md`
- `scripts/run_gate7_lance_scoring.py`
- `scripts/run_gate8_baselines_from_lance.py`
- `scripts/run_gate9_ablations.py`
