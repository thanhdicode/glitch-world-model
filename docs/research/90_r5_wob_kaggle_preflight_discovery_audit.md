# 90 - R5-WOB Kaggle Preflight Discovery Audit

Date: 2026-06-22
Status: `R5_WOB_DISCOVERY_HARDENED`

This note records an infrastructure-only audit of the staged `R5-WOB` Kaggle path after the
latest notebook log advanced past installation and then appeared to stall at `preflight`.

## Observed Symptom

- The downloaded Kaggle log reached `=== 2. Preflight ===` and then emitted no further stage
  output before the user stopped or timed out the run.
- This behavior differed from the earlier failures:
  - not the old empty debug bundle;
  - not the `.lance` stage-marker contract bug;
  - not the LanceDB/PyLance runtime mismatch;
  - not the notebook `ModuleNotFoundError: cloud` packaging break.

## Root Cause

The staged path was not necessarily crashing at `preflight`; it was doing too much silent
discovery work under a misleadingly small label.

The specific bottleneck was the combination of:

- recursive Kaggle root detection over the whole mounted input tree;
- recursive search for each seed tarball and sidecar under the whole mounted input tree;
- no progress logging between the start of `preflight` and the end-of-stage JSON print.

With large World of Bugs raw mounts attached, those recursive scans could walk substantial
irrelevant directory trees before reaching the small seed-artifact dataset. From the notebook UI,
that looked indistinguishable from a hang.

## Hardening Applied

- Replaced recursive whole-tree discovery in `src/glitch_detection/wob_kaggle_common.py` with
  bounded dataset-root inspection over the Kaggle mount layout.
- Added explicit environment override support for:
  - `NORMAL_INPUT_ROOT`
  - `TEST_INPUT_ROOT`
  - `WOB_SEED42_TARBALL` / `WOB_SEED42_SHA256` / `WOB_SEED42_EXTRACTED_ROOT`
  - `WOB_SEED43_TARBALL` / `WOB_SEED43_SHA256` / `WOB_SEED43_EXTRACTED_ROOT`
  - `WOB_SEED44_TARBALL` / `WOB_SEED44_SHA256` / `WOB_SEED44_EXTRACTED_ROOT`
- Added `discover_r5_wob_input_overrides()` so the staged shell runner resolves and prints the
  exact mounted inputs before `preflight`.
- Added progress prints inside staged `preflight` for:
  - readiness and manifest validation;
  - split loading;
  - normal/test root resolution;
  - per-seed input location;
  - per-seed artifact validation and extraction;
  - train/eval coverage checks;
  - final stage-marker write.

## Regression Coverage

- `test_detect_kaggle_roots_exact_match_avoids_recursive_scan`
- `test_detect_kaggle_roots_prefers_environment_overrides`
- `test_discover_r5_wob_input_overrides_reports_direct_seed_tarballs`
- `test_resolve_seed_inputs_direct_tarball_avoids_recursive_scan`

These are infrastructure guards only. They do not add any WOB metric, claim, or paper result.

## Claim Safety

- No new WOB AUROC, AUPRC, F1, or FPR@95TPR claim is added here.
- No cross-game, action-conditioning, superiority, or locked-test claim is added here.
- This is a Kaggle reliability and observability hardening change only.
