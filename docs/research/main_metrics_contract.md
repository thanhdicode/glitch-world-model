# R5-XGame Main Metrics Contract

## Frozen Semantics

- Unit of analysis: episode, after pre-specified window-to-episode aggregation.
- Threshold: selected only from `calibration_normal` episode scores; no evaluation row may influence it.
- Evaluation labels: `evaluation_normal_negative=0` and `evaluation_buggy_positive=1`.
- Report AUROC, AUPRC, F1, precision, recall, FPR@95TPR, and balanced accuracy only when both evaluation classes are present.
- Report all seeds 42, 43, and 44; do not select a best seed for the headline result.
- Report per-category buggy-positive results where labels are available, with support counts.
- Bootstrap confidence intervals resample episodes, retain the frozen threshold, and use a documented deterministic seed.

## BLOCKED

No metric may be reported until the frozen split is materialized and scored. The existing metric guard rejects one-class evaluation.
