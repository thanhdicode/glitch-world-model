# LAST_HANDOFF.md

Last completed task: Fix K-C/WOB binary protocol to include held-out normal evaluation episodes
Commit: pending
Date: 2026-07-01T21:32:22+07:00

## What Changed

- Re-froze `configs/wob_protocol/wob_expansion_eval_manifest.csv` as a true binary validation
  manifest: 6 `calibration_normal`, 6 `evaluation_normal`, and 60 `evaluation_buggy` rows.
- Regenerated `configs/wob_protocol/wob_expansion_readiness.json`; the frozen manifest SHA256 is
  `38f2e0a686600914d841b5f2a63740b9f4b33d3e4d31f2b70d1f02c4243179c1`.
- Updated shared manifest validation to support explicit WOB/XGame evaluation roles while keeping
  TempGlitch's generic `evaluation` role compatible.
- Updated WOB non-staged and K-C staged materialization so normal Lance datasets include both
  calibration-normal and evaluation-normal rows, and window manifests preserve roles from the
  frozen eval manifest.
- Updated episode evaluation so AUROC/FPR are computed from held-out normal and buggy evaluation
  episodes, not from calibration rows.
- Hardened WOB/K-C validators to reject positive-only bundles: comparison rows must have 66
  evaluation episodes, 60 positives, 6 negatives, and nonblank AUROC/FPR.
- Added `--dry-run` to `scripts/validate_kc_wob_binary_output.py` for readiness-level preflight.
- Packaged staged K-C success tarballs with stage marker JSON files so downloaded bundles can pass
  local K-C intake after extraction.
- Updated tests and claim registry C-072 to reflect the new WOB readiness split.

## Checks Passed

- `python -m pytest -q`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/validate_research_release.py --ci`
- `python scripts/check_claim_registry.py`
- `python scripts/validate_wob_expansion_readiness.py`
- `python scripts/validate_kc_wob_binary_output.py --dry-run`

## Safety Status

- No GPU training, Kaggle launch, window rescoring, locked-test materialization, or locked-test
  scoring was performed.
- No WOB binary result is claimed yet; this is a protocol/tooling fix plus frozen-manifest update.
- The previous R5-WOB success bundle remains a positive-probe artifact only because it had zero
  held-out normal evaluation episodes.
- Locked test remains closed.
- Output artifacts, checkpoints, Lance datasets, caches, credentials, and Kaggle files remain
  uncommitted.
- The existing `_kaggle_upload/` directory remains untracked and uncommitted.

## Gate Status After Task

- K-C/WOB binary is ready for a new Kaggle rerun from the fixed commit once pushed.
- Expected K-C manifest shape after rerun: 6 calibration-normal, 6 evaluation-normal, 60
  evaluation-buggy episodes.
- A valid K-C result must report true binary metrics, including AUROC and FPR@95TPR, with
  `negative_episode_count=6`.
- Locked test remains closed.

## Open Blockers

- K-C output cannot be claimed until the rerun tarball plus `.sha256` are downloaded and pass
  local intake.
- The next Kaggle run must use a commit containing this binary-manifest fix; rerunning older
  commits will reproduce the positive-only WOB bundle problem.
- Any paper wording must keep old R5-WOB positive-probe evidence separate from future K-C binary
  metrics.

## Next Recommended Task

- Commit and push the WOB binary protocol fix.
- Rerun the K-C WOB binary Kaggle notebook from the pushed commit.
- Download `kc_wob_binary_outputs.tar.gz` and `.sha256`, extract/validate locally, then update
  claims and paper only if the validator passes.

## Files Likely Relevant Next

- `configs/wob_protocol/wob_expansion_eval_manifest.csv`
- `configs/wob_protocol/wob_expansion_readiness.json`
- `src/glitch_detection/lewm_lance_eval.py`
- `src/glitch_detection/r5_wob_staged.py`
- `src/glitch_detection/r5_wob_eval.py`
- `src/glitch_detection/r5_tempglitch_eval.py`
- `scripts/validate_kc_wob_binary_output.py`
- `scripts/validate_r5_wob_evaluation.py`
- `kaggle/kc_wob_binary/KAGGLE_K_C_WOB_BINARY.md`
