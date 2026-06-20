# 88 - R5-WOB Post-Run Workflow

Date: 2026-06-20
Status: `PREPARED_AWAITING_KAGGLE_OUTPUT`

## Scope

This is an offline intake workflow for the staged non-locked R5-WOB run. It does not run
R5-XGAME, R6, or another WOB evaluation. It does not contain WOB metrics. Locked test remains
unmaterialized and unscored.

## Success Path

Required downloads:

- `r5_wob_identical_episode_outputs.tar.gz`
- `r5_wob_identical_episode_outputs.tar.gz.sha256`

Use an empty local directory outside the repository for ingestion:

```powershell
python scripts/verify_r5_wob_upload.py `
    --tarball "<download-dir>\r5_wob_identical_episode_outputs.tar.gz" `
    --sha256-file "<download-dir>\r5_wob_identical_episode_outputs.tar.gz.sha256" `
    --extract-dir "<local-intake-dir>"
```

PASS requires all of the following:

- the SHA256 sidecar matches the downloaded tarball;
- safe extraction accepts only regular files/directories and writes no file outside the destination;
- all seven canonical R5-WOB files exist;
- `validate_r5_wob_evaluation.py` passes the frozen readiness manifest;
- seeds 42/43/44 and both named baselines are present;
- fit/select leakage is false;
- locked-test materialization and scoring are false;
- `r5_wob_validation_receipt.json` is written inside the validated output directory.

The intake script runs the validator. A direct audit rerun is:

```powershell
python scripts/validate_r5_wob_evaluation.py `
    --output-dir "<local-intake-dir>\r5_wob_identical_episode"
```

Only after both commands pass:

1. Summarize the rows already present in `r5_wob_comparison.csv` and the protocol metadata in
   `r5_wob_metrics.json`; do not recompute or infer missing values.
2. Record the bundle hash, output hashes, exact Kaggle commit, and validator receipt in a new
   evidence note.
3. Update `docs/research/16_claim_registry.md` with narrow validation-only wording.
4. Replace paper TODO values only with validated values and keep the non-locked qualification.
5. Update context state to `R5_WOB_VALIDATED`.
6. R5-XGAME may then be considered separately; it remains fail-closed without the receipt.

Prepared, but not authorized for execution in this task:

```powershell
python scripts/run_r5_xgame_comparison.py `
    --tempglitch-metrics "outputs\r5_tempglitch_identical_episode\r5_metrics.json" `
    --wob-metrics "<validated-output-dir>\r5_wob_metrics.json" `
    --wob-validation-receipt "<validated-output-dir>\r5_wob_validation_receipt.json" `
    --output-dir "outputs\r5_xgame_comparison"
```

## Failure Path

Required downloads after failure:

- `r5_wob_identical_episode_failure_debug.tar.gz`
- `r5_wob_identical_episode_failure_debug.tar.gz.sha256`
- Kaggle console tail if the archive is missing or incomplete

Run only the offline inspector:

```powershell
python scripts/verify_r5_wob_upload.py `
    --failure-debug-tarball "<download-dir>\r5_wob_identical_episode_failure_debug.tar.gz" `
    --failure-debug-sha256-file `
        "<download-dir>\r5_wob_identical_episode_failure_debug.tar.gz.sha256"
```

The JSON response reports `failed_stage`, `failure_class`, and `minimal_fix`. Inspect in this
order:

1. `failure_summary.json`: commit, stage, exit code, failed command, locked-test flags.
2. `working_logs/r5_wob_staged.log`: final traceback and direct error.
3. completed `stage_*.json` markers: last valid restart point.
4. partial non-sensitive CSV/JSON outputs: presence only; they are not paper evidence.

Classify the failure as one of: CUDA OOM, environment dependency, artifact integrity, missing
input, validator failure, data materialization, training/scoring runtime, timeout, or unknown.
Patch only the direct cause, add a focused regression test, preserve completed stage markers, and
retry only after the fix passes repository validation. Never convert a partial bundle into an
evaluation claim.

## R6 Queue

`configs/r6_ablation_queue.json` is the prepared dependency record:

- TempGlitch CPU-safe A1-A4: `PREPARABLE_NOT_RUN`;
- TempGlitch GPU A5-A6: blocked by validated R5-XGAME and a separate GPU execution decision;
- WOB A7-A11: `BLOCKED_R5_WOB_VALIDATION`.

No R6 item was executed while preparing this workflow.

## Claim Boundary

- No WOB performance claim.
- No cross-game generalization claim.
- No action-conditioning or SIGReg benefit claim.
- No locked-test claim.
- No paper metric until a downloaded success bundle passes both SHA256 and the repository
  validator.
