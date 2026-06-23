# NEXT_ACTION.md

Last updated: 2026-06-23T04:56:29+00:00
Commit: `b6e2b906a34cae35bd20d8907ffe17af8ce4ac51`

## Current Priority
Complete or monitor the staged non-locked R5-XGame Kaggle operation, then validate the downloaded
success bundle locally before recording any metric. The repository has no validated R5-XGame
result yet. Keep WOB R6 and locked test closed until the named prerequisites pass.

## Kaggle Run Next Action
1. If the notebook is not already running, open Kaggle with GPU enabled.
2. Attach `benedictwilkinsai/world-of-bugs-normal` and `benedictwilkinsai/world-of-bugs-test`.
3. Run `bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh` from the repository root.
4. Download `r5_xgame_outputs.tar.gz`, `r5_xgame_outputs.tar.gz.sha256`, and the Kaggle log.

## Intake Next Action
1. Run `scripts/validate_r5_xgame_output_bundle.py` with the downloaded tarball, sidecar, and
   `configs/wob_protocol/r5_xgame_split.csv`.
2. Require `r5_xgame_tarball_validated` before summarizing metrics or updating claims.
3. On failure, keep the bundle out of evidence, preserve the Kaggle log, classify the failed stage,
   and patch only the direct cause.

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
- Use Kaggle-mounted official WOB inputs for real `R5-XGame` execution because the current local
  machine lacks the full raw tar coverage required for a valid run.
- Keep locked-test materialization/scoring false.
- Make no R5-XGame/WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until
  the corresponding evaluation or ablation artifacts exist.
- Keep TempGlitch CPU-safe R6 items at `PREPARABLE_NOT_RUN` and every WOB R6 item at
  `BLOCKED_R5_XGAME_VALIDATION`.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family, and R5-WOB is validated as positive-probe
evidence only. R5-XGame remains unverified until the Kaggle success bundle passes SHA256, safe
extraction, and the frozen validator. Without that receipt, all WOB ablations, WOB paper metrics,
and WOB/R5-XGame performance claims remain blocked. A failure bundle opens only a minimal
repair/retry path, not a result path. Locked test stays closed.
