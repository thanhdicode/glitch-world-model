# NEXT_ACTION.md

Last updated: 2026-06-22T16:26:17+00:00
Commit: `c33ff95f52354095e74d5f10e4c47f2882f76fa3`

## Current Priority
Wait for the staged non-locked R5-WOB Kaggle run to finish, then take exactly one offline intake
path below. The repository has no validated WOB evaluation result yet. Keep R5-XGAME, WOB R6,
and locked test closed until the named prerequisites pass.

## Success Next Action
1. Download `r5_wob_identical_episode_outputs.tar.gz` and its `.sha256` sidecar.
2. Run `scripts/verify_r5_wob_upload.py` with an empty `--extract-dir` outside the repository.
3. Require `VALID_OUTPUT_BUNDLE`, a direct `validate_r5_wob_evaluation.py` pass, and the generated
   `r5_wob_validation_receipt.json` before summarizing metrics or updating claims.
4. Only then prepare a separately authorized R5-XGAME run using the validated metrics and receipt.

## Failure Next Action
1. Download `r5_wob_identical_episode_failure_debug.tar.gz` and its `.sha256` sidecar plus the
   Kaggle console tail if available.
2. Run `scripts/verify_r5_wob_upload.py` with `--failure-debug-tarball` and
   `--failure-debug-sha256-file`.
3. Record `failed_stage`, `failure_class`, and the last completed stage marker.
4. Patch and test only the direct cause; do not reuse partial outputs as evidence.

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
- Keep TempGlitch CPU-safe R6 items at `PREPARABLE_NOT_RUN` and every WOB R6 item at
  `BLOCKED_R5_WOB_VALIDATION`.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family. R5-WOB remains unverified until a downloaded
success bundle passes SHA256, safe extraction, and the frozen validator. Without that receipt,
R5-XGAME, all WOB ablations, WOB paper metrics, and WOB performance claims remain blocked. A
failure bundle opens only a minimal repair/retry path, not a result path. Locked test stays closed.
