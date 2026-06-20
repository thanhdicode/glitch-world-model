# 87 - R5-WOB Failure Audit and Retry Plan

Date: 2026-06-20
Status: `R5_WOB_STAGED_RETRY_READY`

Post-run update: commit `c13ae90` corrected the staged Lance integration to use the reusable
`glitch_detection.lewm_lance_eval` functions instead of private attributes on a CLI wrapper. The
current post-run intake and failure-classification workflow is documented in
[88_r5_wob_postrun_workflow.md](88_r5_wob_postrun_workflow.md). This is infrastructure evidence,
not a WOB result.

## Executive Summary

The previous Kaggle `R5-WOB` retry did not produce a valid evaluation bundle and the downloaded
failure archive was too small to contain diagnostic logs. Because the archive was SHA256-valid but
content-empty, the exact failing line is not recoverable from that run alone. The current
repository now adds a staged, resumable retry path so the next Kaggle attempt leaves enough
evidence to classify failures without reopening locked test or inventing results.

## Failure Classification

Primary class for the completed failed attempt:

- `UNKNOWN_NEEDS_MORE_LOGS`

Evidence:

- `C:\Users\ADMIN\Downloads\r5_wob_identical_episode_failure_debug.tar.gz` is only `88` bytes.
- The SHA256 sidecar matches the tarball hash `ac79e3cdf7e0fa8f48c494861953d700b64ce0937e1e65cc589f4575fce79596`.
- Listing the tarball contents returns no files, so there is no `runner.log`, no structured
  `failure_summary.json`, and no partial output tree to inspect.
- No local `r5_wob_retry.log` was available for this audit.

## Why The Old Path Was Fragile

The earlier `R5-WOB` path was structurally valid but operationally monolithic:

1. It materialized train, calibration-normal, and evaluation-buggy Lance datasets in one run.
2. It scored baselines and all three LeWM seeds in the same process.
3. It forced baseline batch size to `max(batch_size, 16)` inside the monolithic evaluator.
4. It did not emit per-stage success markers or restartable checkpoints between major phases.
5. It relied on a single end-to-end success path before writing final validator-backed outputs.
6. The earliest failure-debug archive was empty, so the first failure could not be localized.

These facts do not prove an OOM, CUDA, or dataset error by themselves. They do show that the old
path made early failure classification unnecessarily hard.

## Repository Audit Scope

Inspected implementation and control surface:

- `src/glitch_detection/r5_wob_eval.py`
- `src/glitch_detection/lewm_data.py`
- `src/glitch_detection/lewm_adapter.py`
- `src/glitch_detection/lewm_lance_eval.py`
- `scripts/run_r5_wob_identical_episode_evaluation.py`
- `scripts/validate_r5_wob_evaluation.py`
- `scripts/validate_wob_seed_artifacts.py`
- `cloud/wob_r5_eval/run_kaggle_r5_wob_eval.sh`
- `cloud/wob_r5_eval/README.md`
- `tests/test_r5_wob_eval.py`
- `tests/test_validate_r5_wob_evaluation.py`
- `tests/test_wob_r5_runner.py`

Inspected available failure evidence:

- `C:\Users\ADMIN\Downloads\r5_wob_identical_episode_failure_debug.tar.gz`
- `C:\Users\ADMIN\Downloads\r5_wob_identical_episode_failure_debug.tar.gz.sha256`

Unavailable for this audit:

- populated `r5_wob_retry.log`
- populated failure-debug archive from the latest retry
- validated success tarball

## New Staged Retry Design

The new staged path is intentionally restartable and claim-safe:

- `preflight`
  Detect Kaggle dataset roots, repack auto-extracted seed folders if needed, validate seed
  artifacts, verify lean runtime imports, and write `stage_preflight.json`.
- `materialize_lance`
  Build only the required non-locked Lance datasets and write `stage_materialize_lance.json`.
- `baseline_scores`
  Score named baselines with a separate conservative batch-size control and write
  `stage_baseline_scores.json`.
- `lewm_seed42`, `lewm_seed43`, `lewm_seed44`
  Score one seed per stage, validate alignment, write per-seed CSVs, and release memory between
  seeds.
- `aggregate_metrics`
  Assemble episode scores, comparison rows, metrics, provenance, and report from staged artifacts.
- `validate_package`
  Validate the full output directory and create the success tarball plus SHA256 sidecar.

Each stage:

- can skip itself when its marker and hashes remain valid;
- preserves `validation_buggy_used_for_fit_select=false`;
- preserves `locked_test_materialized=false`;
- preserves `locked_test_scored=false`.

## Code Changes

New or updated files:

- `src/glitch_detection/r5_wob_staged.py`
- `scripts/run_r5_wob_stage.py`
- `scripts/validate_r5_wob_stage_outputs.py`
- `scripts/assemble_r5_wob_from_stages.py`
- `cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh`
- `cloud/wob_r5_eval/README.md`
- `tests/test_r5_wob_stage.py`
- `tests/test_wob_r5_runner.py`

The original monolithic runner remains in the repo for forensic comparison, but the recommended
retry path is now the staged runner.

## New Kaggle Retry Procedure

Use the staged retry branch commit in the notebook cell. The cell must:

1. clone the repo at the staged-retry commit;
2. install the lean runtime only;
3. run `cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh`;
4. download either the success tarball pair or the failure-debug tarball pair.

Recommended runtime controls:

- baseline batch size: `4`
- LeWM batch size: `2`
- device: `cuda`

## Expected Failure Forensics After The Next Retry

If the next Kaggle run fails, the debug tarball should now include:

- `failure_summary.json`
- `working_logs/r5_wob_staged.log`
- stage marker JSON files
- any non-sensitive partial CSV/JSON outputs already written

That is sufficient to classify the next failure into runtime, dataset, conversion, CUDA, validator,
or packaging buckets without guessing.

## Expected Runtime / Resource Envelope

The exact wall-clock time still depends on Kaggle I/O and GPU availability. The staged design
reduces repeated work and lowers immediate memory pressure by:

- avoiding one giant all-seed process;
- separating baseline batch size from LeWM batch size;
- freeing GPU memory after each seed stage;
- allowing resume from the last completed stage within the same Kaggle session.

## Claim Safety

- No WOB AUROC, AUPRC, F1, or FPR@95TPR claim is added here.
- No cross-game claim is added here.
- No action-conditioning benefit claim is added here.
- No locked-test materialization or scoring is introduced here.
- Smoke mode, if used, is explicitly non-paper-valid and cannot be packaged as a final bundle.

## One Exact Next Human Action

Run the new staged Kaggle notebook cell from the staged retry branch commit, then download the
produced success pair or failure-debug pair without modifying locked-test access.
