# R5-XGame - Cross-Game / Cross-Source Evaluation with Held-Out Normal Negatives

## Purpose

Convert the R5-WOB positive-probe evaluation into a valid non-locked binary protocol without changing R5-WOB labels or opening the locked test.

## PLANNED Protocol

- Freeze one manifest containing `train_normal`, `calibration_normal`, `evaluation_normal_negative`, and `evaluation_buggy_positive` rows.
- Reject zero negatives, zero positives, calibration/evaluation episode or pair overlap, buggy calibration rows, and every `test` or `locked_test` row.
- Reuse metadata-only Lance manifest construction and emit the planned manifest, window-manifest, baseline/seed score files, episode scores, comparison, metrics, report, provenance, stage markers, and success tarball with SHA256.
- Report episode-level AUROC, AUPRC, F1, precision, recall, FPR@95TPR, balanced accuracy where applicable, category breakdowns, and bootstrap confidence intervals.

## VERIFIED Preparation

`src/glitch_detection/r5_xgame_protocol.py` validates the split contract and `src/glitch_detection/r5_xgame_metrics.py` rejects one-class metric evaluation. `scripts/run_r5_xgame_staged.py --smoke` reports the awaiting-manifest state without scoring or creating experiment artifacts.

## BLOCKED

No source-disjoint R5-XGame manifest has been frozen and no R5-XGame run has occurred. The empty `configs/wob_protocol/r5_xgame_split.csv` is a schema template, not dataset evidence.
