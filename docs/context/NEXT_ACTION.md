# NEXT_ACTION.md

Last updated: 2026-06-20T13:30:00+00:00
Commit: current task commit

## Current Priority
The first R5-WOB non-locked Kaggle attempt stopped before producing an evaluation output bundle.
Its downloaded failure-debug archive was SHA256-verified but empty, so it does not identify the
root cause. Retry only with commit `2fb87f0c744a35cec3858faf36da52037bcf14a3`, which records a
runner log and structured failure summary in every future debug archive. Keep the locked test
closed throughout.

## Sequenced Steps
1. Retry the frozen non-locked R5-WOB Kaggle evaluation at commit `2fb87f0c744a35cec3858faf36da52037bcf14a3`.
2. On success, download `r5_wob_identical_episode_outputs.tar.gz` + `.sha256` sidecar.
3. On failure, download `r5_wob_identical_episode_failure_debug.tar.gz` + `.sha256` sidecar.
4. Run `python scripts/verify_r5_wob_upload.py` only when the main output bundle exists.
4. If VALID_OUTPUT_BUNDLE: ingest results, update claims, run R5-XGAME comparison.
5. Run CPU-safe R6 ablations (aggregation, distance, calibration, failure-mode).
6. If GPU budget permits: run Kaggle-required R6 ablations (SIGReg, action-conditioning).
7. R7 validation decision and locked-test go/no-go recommendation.
8. R8 paper completion with all evidence-backed tables.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Preserve the verified WOB-P1 seed42 training artifact hash
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
- Preserve the verified WOB-P1 seed43 training artifact hash
  `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88`.
- Preserve the verified WOB-P1 seed44 training artifact hash
  `c5b3178cdb75a0c1f9bcca78eba8beaaf21ffa703917a3f42c476563849fd041`.
- Keep the seed42 non-locked WOB evaluation manifest, reporting paths, and claim boundary frozen
  during evaluation execution.
- Use Kaggle-mounted official WOB inputs for real `R5-WOB` execution because the current local
  machine lacks the full raw tar coverage required for a valid run.
- Keep locked-test materialization/scoring false.
- Make no WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until the
  corresponding evaluation or ablation artifacts exist.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family and the WOB evaluation-readiness gate is
frozen. The Kaggle-native `WOB-P0` bundle and the WOB-P1 seed42/seed43/seed44 training artifacts
are validator-backed, and the `R5-WOB` runner/validator bundle is prepared. The current blocker is
environmental: the local workstation still lacks the full raw WOB tar coverage required for a
valid real run. The first Kaggle attempt stopped early with an empty debug archive, so the retry
must use the diagnostics-preserving runner; neither attempt justifies opening the locked test.
