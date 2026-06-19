# NEXT_ACTION.md

Last updated: 2026-06-19T04:11:06+00:00
Commit: `d8419ee446900a401ffedf6bdf0346b43915bec6`

## Current Priority
Open the controlled World of Bugs expansion implementation path under Ambitious Plan A. The
seed42 non-locked WOB evaluation-readiness gate is now frozen and validated locally; the next
experimental step is WOB seed43/44 real-action training, then the R5-WOB non-locked evaluation.
Keep the locked test closed throughout.

## Sequenced Steps
1. Freeze WOB seed42 evaluation-readiness (manifest path, calibration/evaluation role split,
   reporting paths, recorded artifact hashes, claim boundary) via
   `scripts/prepare_wob_expansion_readiness.py` + `scripts/validate_wob_expansion_readiness.py`.
2. Complete WOB seeds43/44 real-action train-normal-only training (Kaggle GPU; human-run) after a
   separate GPU-budget confirmation, then verify uploaded artifacts.
3. Run the R5-WOB non-locked identical-episode evaluation on the frozen manifest.
4. Keep the locked test closed; locked-test access still needs a separate direct user command.

## Success Criteria
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS` while treating the verified
  Kaggle-native `WOB-P0` bundle as the WOB entry checkpoint.
- Preserve the verified WOB-P1 seed42 training artifact hash
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
- Keep the seed42 non-locked WOB evaluation manifest, reporting paths, and claim boundary frozen
  before any evaluation execution.
- Do not run WOB evaluation yet; do not start seed43/44 training before GPU-budget confirmation.
- Keep locked-test materialization/scoring false.
- Make no WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until the
  corresponding evaluation or ablation artifacts exist.

## Current Known Blocker
R5 is complete for the non-locked TempGlitch family and the WOB evaluation-readiness gate is
frozen. Local `WOB-P0` remains blocked because the attached root is incomplete, while the
Kaggle-native `WOB-P0` bundle and the WOB-P1 seed42 training artifact are both validator-passed.
The next experimental step (WOB seed43/44 training) needs human Kaggle GPU execution; it still
does not justify opening the locked test or running WOB evaluation before its inputs are ready.
