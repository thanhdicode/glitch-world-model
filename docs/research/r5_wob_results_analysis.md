# R5-WOB Results Analysis

## VERIFIED

- Artifact intake: `VALID_OUTPUT_BUNDLE`; the validated extraction and receipt remain outside Git-tracked paths.
- Core files received: manifest, baseline scores, episode scores, comparison, metrics, provenance, and report. Raw per-seed score files, stage markers, `gate8_metadata.json`, and materialization telemetry are not present in the tarball.
- The Kaggle log reports preflight, Lance materialization, baseline scoring, three LeWM seeds, aggregation, package validation, and stage-marker validation as complete.
- Protocol: 48 train-normal episodes, 12 calibration-normal episodes, 60 buggy probe episodes, 303,211 windows, and zero evaluation normal negatives. The frozen manifest hash is `f7dbd85876809a1c2437cf5827ce4c27f289078ca0904ed70c1d75908a1bcec6`.
- The highest observed calibrated positive-probe F1 row is LeWM seed43 / `lewm_mse_mean` / max episode aggregation: 0.9474 (bootstrap CI 0.8991 to 0.9831).

## INFERRED

- The observed spread between seed43 and seed44 means checkpoint/seed stability remains a material uncertainty.

## BLOCKED

- No normal-negative evaluation set exists. AUROC and FPR@95TPR are undefined; AUPRC=1 reflects a positive-only evaluation and must not be used as a binary classification result.
- F1 is only calibrated buggy-probe detection under a normal-calibrated threshold, not full binary benchmark evidence.

## Safe Claim Boundary

The non-locked R5-WOB pipeline completed and produced provenance-bound baseline and three-seed LeWM episode outputs. It does not establish broad glitch-detection performance, superiority, cross-game generalization, or any locked-test result.
