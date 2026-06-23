# LAST_HANDOFF.md

Last completed task: R5-XGame intake reconciliation plus bounded R6 evidence upgrade
Commit: pending task commit
Date: 2026-06-23

## What Changed

- Reconciled the `R5-XGame` intake contract so the checked-in frozen manifest remains
  authoritative across LF/CRLF checkouts by validating normalized CSV content rather than raw
  line-ending bytes.
- Added explicit reconciliation evidence in
  `docs/research/94_r5_xgame_intake_reconciliation.md`, including the original fail/pass matrix,
  raw versus normalized manifest hashes, line-ending evidence, and the legacy `stage_package.json`
  SHA caveat.
- Updated `scripts/validate_r5_xgame_output_bundle.py` to report raw-hash mismatch separately from
  normalized manifest equivalence and to surface legacy package-marker tarball metadata without
  treating it as authoritative.
- Added focused regression tests for line-ending-insensitive manifest validation and for the
  minimal `stage_package.json` snapshot contract.
- Completed bounded `R6` documentation from the validated bundle only:
  - `95_r6_xgame_error_analysis.md`
  - `96_r6_xgame_bounded_comparison.md`
  - `97_r6_xgame_ablation_summary.md`
  - `98_r6_limitations_and_next_benchmark_memo.md`
- Synchronized claim-control docs so the new bounded reconciliation and R6 findings are explicitly
  registered without widening claim scope.

## Evidence Confirmed

- Checked-in manifest role counts remain:
  `train_normal=36`, `calibration_normal=12`, `evaluation_normal_negative=12`,
  `evaluation_buggy_positive=60`
- Verified flags remain false:
  `validation_buggy_used_for_fit_select`, `locked_test_materialized`, `locked_test_scored`
- Output-dir validator status against checked-in manifest:
  `r5_xgame_output_validated`
- Tarball validator status against checked-in manifest:
  `r5_xgame_tarball_validated`
- Repaired tarball SHA256:
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`
- Raw manifest SHA mismatch is now documented as LF/CRLF-only:
  checked-in `4f4b0ca5fe6e7ea207dd5a8f4ec97a0d00af486a109d2f215e9c83880c89182c`
  versus bundle `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`
- Normalized manifest SHA matches:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`
- Best recorded bounded result remains:
  AUROC approximately `0.9097`, AUPRC approximately `0.9814`, F1 approximately `0.7921`,
  precision approximately `0.9756`, recall approximately `0.6667`, balanced accuracy
  approximately `0.7917`

## Main Bounded R6 Findings

- Best-row error analysis shows `20` false negatives and `1` false positive on the frozen
  72-episode evaluation, so the strongest row remains recall-limited rather than precision-limited.
- Within the frozen non-locked split, the best recorded baseline remains `feature_distance`
  (`AUROC 0.7681`) above `frame_diff` (`AUROC 0.7167`), while the best recorded LeWM row remains
  `0.9097`; this comparison remains split-bounded only.
- The validated `category` field is single-valued (`world_of_bugs`), so per-category comparison is
  limited to support-count confirmation rather than multi-category contrast.
- Recorded LeWM rows show stronger descriptive AUROC for `max` / `top2_mean` aggregation than for
  `mean`, with seed `44` providing the strongest recorded rows.

## Safety Status

- No LeWM retraining was launched.
- No new live Kaggle run was launched.
- Locked test remains closed.
- No raw data, tarballs, checkpoints, or credentials were added to Git.
- No raw scientific metrics were modified.
- No broad generalization, SOTA, SIGReg-benefit, temporal-localization, or locked-test claim was
  introduced.

## Checks Passed

- `python -m pytest tests/test_validate_r5_xgame_output_bundle.py tests/test_r5_xgame_runner.py`
  -> `18 passed`
- `python -m ruff check scripts/validate_r5_xgame_output_bundle.py`
- `python -m ruff check tests/test_validate_r5_xgame_output_bundle.py tests/test_r5_xgame_runner.py docs/research/16_claim_registry.md docs/research/70_paper_claim_map.md`
- `python -m ruff format --check scripts/validate_r5_xgame_output_bundle.py tests/test_validate_r5_xgame_output_bundle.py tests/test_r5_xgame_runner.py`
- `python scripts/check_claim_registry.py`

## Gate Status After Task

- Phase A / `R5-WOB`: unchanged; complete as positive-probe only.
- Phase B / `R5-XGame`: intake-reconciled and validator-green against the checked-in manifest.
- R6 / bounded evidence upgrade: completed from the validated bundle only.
- Locked test: still closed.

## Open Blockers

- `R5-XGame` remains non-locked and positive-heavy with only `12` normal-negative evaluation
  episodes.
- The validated bundle still contains legacy old-SHA fields inside `stage_package.json`; they are
  now explicitly documented as non-authoritative.
- `R5-WOB` remains positive-probe only and cannot be promoted into a binary-benchmark claim.

## Next Recommended Task

Freeze a bounded TempGlitch follow-up protocol that strengthens evidence quality without touching
locked test and without widening claims beyond validated non-locked evidence.

## Files Likely Relevant Next

- `docs/research/94_r5_xgame_intake_reconciliation.md`
- `docs/research/95_r6_xgame_error_analysis.md`
- `docs/research/96_r6_xgame_bounded_comparison.md`
- `docs/research/97_r6_xgame_ablation_summary.md`
- `docs/research/98_r6_limitations_and_next_benchmark_memo.md`
- `docs/context/NEXT_ACTION.md`
