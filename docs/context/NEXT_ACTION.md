# NEXT_ACTION.md

Last updated: 2026-06-20T00:00:00+00:00

## Current Priority

Two parallel tracks:

**Track A — R5-WOB Kaggle retry (external, highest priority):**
Wait for the staged non-locked R5-WOB Kaggle run to finish on the latest `main` commit
(which includes the Lance directory marker fix). Take exactly one offline intake path below.
The repository has no validated WOB evaluation result yet.

**Track B — R6 TempGlitch CPU-safe ablations (local, unblocked):**
The R6 CPU-safe ablation runner (A1–A4) is now implemented and tested.
Execute it once the R5 TempGlitch output directory is locally present.

---

## Track A — R5-WOB

### Success Next Action
1. Download `r5_wob_identical_episode_outputs.tar.gz` and its `.sha256` sidecar.
2. Run `scripts/verify_r5_wob_upload.py` with an empty `--extract-dir` outside the repository.
3. Require `VALID_OUTPUT_BUNDLE`, a direct `validate_r5_wob_evaluation.py` pass, and the
   generated `r5_wob_validation_receipt.json` before summarizing metrics or updating claims.
4. Only then prepare a separately authorized R5-XGAME run using the validated metrics and receipt.
5. Only after R5-WOB validates: execute R6 WOB CPU ablations (A7–A10).

### Failure Next Action
1. Download `r5_wob_identical_episode_failure_debug.tar.gz` and its `.sha256` sidecar plus the
   Kaggle console tail if available.
2. Run `scripts/verify_r5_wob_upload.py` with `--failure-debug-tarball` and
   `--failure-debug-sha256-file`.
3. Record `failed_stage`, `failure_class`, and the last completed stage marker.
4. Patch and test only the direct cause; do not reuse partial outputs as evidence.

---

## Track B — R6 TempGlitch CPU-Safe Ablations

### How to Execute (requires R5 output dir locally present)
```bash
python scripts/run_r6_tempglitch_cpu_ablations.py \
    --r5-output-dir outputs/r5_tempglitch_identical_episode \
    --output-dir outputs/r6_tempglitch_ablations \
    --ablation all
```

### How to Validate
```bash
python scripts/validate_r6_ablations.py \
    --output-dir outputs/r6_tempglitch_ablations
```

### Current Blocker for Track B
The R5 TempGlitch output directory (`outputs/r5_tempglitch_identical_episode/`) is not
present locally. The Kaggle execution produced this output; download it or re-run.

---

## Success Criteria (both tracks)
- Preserve the completed R5 manifest, score, metric, and provenance hashes.
- Keep local `WOB-P0` status aligned to `BLOCKED_MISSING_INPUTS`.
- Preserve WOB-P1 artifact hashes:
  - seed42: `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`
  - seed43: `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88`
  - seed44: `c5b3178cdb75a0c1f9bcca78eba8beaaf21ffa703917a3f42c476563849fd041`
- Keep the seed42 non-locked WOB evaluation manifest, reporting paths, and claim boundary frozen.
- Use Kaggle-mounted official WOB inputs for real `R5-WOB` execution.
- Keep locked-test materialization/scoring false.
- Make no WOB performance, cross-game, action-conditioning, or SIGReg-benefit claim until the
  corresponding evaluation or ablation artifacts exist.
- R6 WOB items (A7–A11) remain at `BLOCKED_R5_WOB_VALIDATION`.

## Current Known Blockers
- R5-WOB: unverified until a downloaded success bundle passes SHA256, safe extraction, and the
  frozen validator. A failure bundle opens only a minimal repair/retry path.
- R6 TempGlitch CPU (A1–A4): runner is implemented; blocked only on local R5 output files.
- R5-XGAME, WOB ablations, WOB paper metrics: blocked on validated R5-WOB receipt.
- Locked test: stays closed.
