# 84 — R5-WOB Result Intake Template

Date: 2026-06-20
Status: `AWAITING_KAGGLE_OUTPUT`

Canonical command checklist: [R5-WOB post-run workflow](88_r5_wob_postrun_workflow.md).

## Purpose

This document provides the step-by-step procedure for ingesting, verifying, and recording the
R5-WOB Kaggle output after the human downloads it. It does not contain empirical results. It does
not fabricate metrics. It does not touch locked test.

## Expected Kaggle Outputs

| File | Required | Description |
|---|---|---|
| `r5_wob_identical_episode_outputs.tar.gz` | YES | Main output bundle |
| `r5_wob_identical_episode_outputs.tar.gz.sha256` | YES | SHA256 sidecar |
| `r5_wob_identical_episode_failure_debug.tar.gz` | NO | Failure-debug bundle (if Kaggle run had partial failures) |

## Expected Contents Inside the Main Tarball

- `r5_wob_metrics.json` — episode-level AUROC, AUPRC, F1, FPR@95TPR per method/seed/aggregation
- `r5_wob_comparison.csv` — cross-method comparison table
- `r5_wob_provenance.json` — artifact hashes, git SHA, manifest hash, config hashes
- `episode_scores.csv` — per-episode aggregated scores
- `lewm_scores_seed42.csv`, `lewm_scores_seed43.csv`, `lewm_scores_seed44.csv` — per-seed raw
  window scores (optional)
- `r5_wob_manifest.csv` — the evaluation manifest used

## Step-by-Step Intake Procedure

### 1. Download from Kaggle

```
# Download the output tarball and SHA256 sidecar from Kaggle kernel output
# Place them in a local directory (e.g., ~/Downloads/)
```

### 2. Verify the Upload

```powershell
python scripts/verify_r5_wob_upload.py `
    --tarball path/to/r5_wob_identical_episode_outputs.tar.gz `
    --sha256-file path/to/r5_wob_identical_episode_outputs.tar.gz.sha256 `
    --extract-dir path/to/empty/local/intake
```

### 3. Interpret the Result

| Status | Meaning | Next Action |
|---|---|---|
| `VALID_OUTPUT_BUNDLE` | SHA256 matches, extraction and validator pass, receipt written | Proceed to evidence intake |
| `HASH_MISMATCH` | SHA256 does not match sidecar | Re-download from Kaggle |
| `VALIDATOR_FAILURE` | Extracted output fails R5-WOB validator | Inspect validator errors; check for missing rows, manifest mismatch, or locked-test contamination |
| `INCOMPLETE_KAGGLE_OUTPUT` | Missing expected files (metrics, comparison, provenance) | Check Kaggle logs for runtime errors |
| `MISSING_TARBALL` | Tarball file not found at specified path | Check download location |
| `MISSING_SHA256` | SHA256 sidecar not found | Re-download sidecar from Kaggle |
| `EXTRACTION_OR_INTAKE_FAILED` | Bundle, sidecar, or extraction destination is invalid | Inspect the exact detail; re-download if corrupted |

### 4. Ingest Results (only after VALID_OUTPUT_BUNDLE)

```powershell
# Keep the validated extraction outside Git-tracked paths.
# Do NOT commit raw outputs or the validation receipt — record hashes only.

# Record the tarball SHA256 in the claim registry
# Update docs/research/ with the actual results note
# Update paper/tables/r5_wob_results.tex with validated numbers
# Update docs/context/PROJECT_STATE.md
```

### 5. Update Claim Registry

Add the next available claim-registry ID recording:
- The exact R5-WOB evaluation commit reported by the validated provenance
- The tarball SHA256
- The number of evaluation episodes scored
- The methods evaluated (LeWM seeds 42/43/44, frame_diff, feature_distance)
- The locked-test status (unmaterialized, unscored)

### 6. Update Paper Table

Replace the TODO placeholder in `paper/tables/r5_wob_results.tex` with validated numbers only.
Do not infer, extrapolate, or fabricate any metric value.

## Failure-Debug Bundle

If the Kaggle run produced a failure-debug bundle:

1. Download `r5_wob_identical_episode_failure_debug.tar.gz` separately.
2. Pass it with its sidecar via `--failure-debug-tarball` and
   `--failure-debug-sha256-file` to the verification script.
3. Inspect the debug logs for:
   - OOM errors
   - Missing WOB data rows
   - Checkpoint loading failures
   - Runtime errors
4. Classify the failure using `docs/research/86_kaggle_r5_wob_success_failure_playbook.md`.

## Safety Checklist

- [ ] SHA256 verified
- [ ] Validator passed
- [ ] No locked-test rows scored
- [ ] No locked-test rows materialized
- [ ] Manifest matches the frozen 72-row evaluation manifest
- [ ] All three seeds (42/43/44) produced outputs
- [ ] Baselines (frame_diff, feature_distance) produced outputs
- [ ] Provenance JSON records the correct commit SHA
- [ ] No fabricated metrics in any update
- [ ] Claim registry updated with narrow evidence-backed wording only
