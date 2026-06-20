# 86 — Kaggle R5-WOB Success/Failure Playbook

Date: 2026-06-20
Status: `AWAITING_KAGGLE_OUTPUT`

## Purpose

Step-by-step decision tree for handling the Kaggle R5-WOB evaluation output, whether it succeeds
or fails. This playbook does not contain empirical results, does not fabricate metrics, and does
not touch locked test.

## If Kaggle Run Succeeds

### What to Download

1. **Main output tarball**: `r5_wob_identical_episode_outputs.tar.gz`
2. **SHA256 sidecar**: `r5_wob_identical_episode_outputs.tar.gz.sha256`
3. **Kaggle kernel log** (optional, for audit trail)

### Exact Verification Command

```powershell
python scripts/verify_r5_wob_upload.py `
    --tarball path\to\r5_wob_identical_episode_outputs.tar.gz `
    --sha256-file path\to\r5_wob_identical_episode_outputs.tar.gz.sha256
```

### After VALID_OUTPUT_BUNDLE

1. Record tarball SHA256 under the next available claim-registry ID.
2. Ingest metrics into `docs/research/` as a new results note.
3. Update `paper/tables/r5_wob_results.tex` with validated numbers only.
4. Run R5-XGAME comparison: `python scripts/run_r5_xgame_comparison.py`.
5. Update `docs/context/PROJECT_STATE.md` and `NEXT_ACTION.md`.
6. Proceed to R6 CPU-safe ablations.

## If Kaggle Run Fails

### What to Download

1. **Failure-debug tarball** (if produced): `r5_wob_identical_episode_failure_debug.tar.gz`
2. **Kaggle kernel log**: full stderr/stdout
3. **Partial output tarball** (if produced)

### Exact Verification Command (with debug bundle)

```powershell
python scripts/verify_r5_wob_upload.py `
    --tarball path\to\r5_wob_identical_episode_outputs.tar.gz `
    --sha256-file path\to\r5_wob_identical_episode_outputs.tar.gz.sha256 `
    --failure-debug-tarball path\to\r5_wob_identical_episode_failure_debug.tar.gz
```

## Failure Classification

| Failure Class | Symptoms | Next Action |
|---|---|---|
| **OOM** | `CUDA out of memory` or `RuntimeError: CUDA error` in logs | Reduce batch size in eval config; retry on Kaggle |
| **Missing runtime** | `ModuleNotFoundError`, `ImportError`, missing pip packages | Fix package list in Kaggle notebook setup cell; retry |
| **Missing artifact** | `FileNotFoundError` for checkpoint `.pt` files or seed artifacts | Verify seed artifact dataset is mounted correctly on Kaggle |
| **Missing WOB rows** | Validator reports fewer than 72 evaluation rows resolved | Check Kaggle WOB dataset mount; verify tar file coverage |
| **Validator fail** | `validate_r5_wob_evaluation.py` returns errors | Inspect specific validator errors; may need manifest fix |
| **Metric file missing** | Output tarball exists but `r5_wob_metrics.json` is absent | Check if evaluation completed partially; inspect logs |
| **Locked-test contamination** | Validator reports locked rows scored or materialized | CRITICAL: discard output entirely; audit notebook code |
| **Timeout** | Kaggle kernel exceeded time limit (9h for GPU) | Split evaluation into smaller batches or optimize scoring |
| **Data decode error** | `lance` or `tarfile` errors during data loading | Verify WOB Lance dataset integrity on Kaggle |
| **Checkpoint load error** | `RuntimeError` during `torch.load` or state dict mismatch | Verify seed artifact hashes match expected values |
| **Unknown** | Unclassified error | Capture full traceback; classify manually before retry |

## Decision Tree

```
Kaggle R5-WOB completes
├── Output tarball exists?
│   ├── YES → Download tarball + SHA256 sidecar
│   │   ├── SHA256 matches? → Run verify_r5_wob_upload.py
│   │   │   ├── VALID_OUTPUT_BUNDLE → Ingest results (see above)
│   │   │   ├── VALIDATOR_FAILURE → Classify failure (see table)
│   │   │   └── INCOMPLETE_KAGGLE_OUTPUT → Check logs for partial failure
│   │   └── SHA256 mismatch → Re-download from Kaggle
│   └── NO → Download failure-debug bundle + logs
│       ├── Classify failure (see table)
│       └── Fix and retry on Kaggle
└── Kaggle kernel still running after 9h
    └── Check Kaggle dashboard for status
        ├── OOM → Reduce batch size, retry
        └── Timeout → Optimize or split evaluation
```

## Retry Policy

- Maximum 3 retry attempts per failure class.
- Each retry must have a changed fingerprint (different config, batch size, or fix).
- Do not retry with the same configuration that failed.
- Record each attempt in `docs/research/` with the failure class and fix applied.
- If 3 retries of the same class fail, escalate to manual investigation.

## Safety Invariants (all retries)

- [ ] Locked test remains unmaterialized and unscored.
- [ ] No WOB performance claim until VALID_OUTPUT_BUNDLE.
- [ ] No fabricated metrics in any update.
- [ ] Kaggle commit SHA matches `fb0f06bcb7c22628ef4ee0200185bf1fd772198c`.
- [ ] All retry attempts are recorded with failure classification.
