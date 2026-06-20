# WOB-P1 Runtime Reliability Audit

**Date**: 2026-06-18
**Repo SHA**: pre-fix audit base `50c671cdbf4c8af7832f63d40363a5c66240c3fe`
**Branch**: main
**Auditor**: Junie (automated)

## 1. Current WOB-P1 Command

```bash
bash cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh
```

The runner executes six sequential stages:
1. `setup_runtime.sh` — pip install dependencies
2. `preflight.sh` — GPU check, split CSV validation, config generation
3. `prepare_wob_train_root.sh` — symlink WOB episodes into train root
4. `build_wob_lance_train_seed42.sh` — build Lance datasets
5. `run_wob_seed42_train.sh` — run LeWM training (15,000 optimizer updates)
6. `validate_wob_seed42_artifacts.sh` — validate outputs

## 2. Required Kaggle Inputs

| Dataset | Expected Mount Path |
|---------|-------------------|
| `benedictwilkinsai/world-of-bugs-normal` | `/kaggle/input/world-of-bugs-normal` |
| `benedictwilkinsai/world-of-bugs-test` | `/kaggle/input/world-of-bugs-test` |

Detection is handled by `cloud.wob_kaggle_native.common.detect_kaggle_roots()`.

## 3. Required Kaggle Outputs

| Artifact | Path |
|----------|------|
| Training outputs | `/kaggle/working/wob_outputs/wob_seed42/` |
| Metadata | `/kaggle/working/wob_p1_metadata/` |
| Train root (symlinks) | `/kaggle/working/wob_p1_root/` |
| Lance datasets | `/kaggle/working/wob_lance/` |
| Final tarball | `/kaggle/working/wob_seed42_artifacts.tar.gz` |
| Tarball hash | `/kaggle/working/wob_seed42_artifacts.tar.gz.sha256` |
| Failure debug | `/kaggle/working/wob_seed42_failure_debug.tar.gz` only when the run fails |

## 4. Idempotency Assessment

**NOT IDEMPOTENT.** The original Kaggle cell runs `rm -rf "$REPO_DIR"` on every
execution, which destroys the cloned repo including any in-progress configuration.
Output directories are created with `mkdir -p` (safe), but the training script starts
from update 0 every time — there is no resume logic in the update-based training path.

## 5. Resume Safety Assessment

**NOT RESUME-SAFE.** The update-based training path (`_train_lewm_by_updates` in
`lewm_training.py`) saves periodic checkpoints to `checkpoint_weights.pt` containing
model state, optimizer state, global_step, config_hash, and dataset_hashes. However:
- The runner script `run_wob_seed42_train.sh` never passes `--resume`.
- The `_train_lewm_by_updates` function does not implement resume (unlike the
  epoch-based path which does).
- Training always starts from update 0 regardless of existing checkpoints.

## 6. Partial Output Handling

**DELETES PARTIAL OUTPUTS.** The Kaggle cell template uses `rm -rf "$REPO_DIR"` which
destroys the cloned repo on every rerun. While output directories under
`/kaggle/working/wob_outputs/` are not explicitly deleted by the runner, they are
overwritten without backup.

## 7. Heartbeat Logging

**MINIMAL.** The training loop prints a log line at update 1 and every 100 updates.
At ~13 updates/second, this means output every ~7.7 seconds during training. However:
- Setup, preflight, data preparation, and Lance build stages have NO periodic output.
- Pip install can be silent for minutes.
- Lance dataset build can be silent for minutes.
- Validation epochs within training produce no heartbeat.

## 8. Log Capture

**NOT CAPTURED.** stdout and stderr are not saved to log files. If the Kaggle notebook
loses connection or fails to save, all diagnostic output is lost.

## 9. Periodic Checkpoints

**YES, during training.** Checkpoints are saved every 500 optimizer updates (configured
via `checkpoint_interval_updates`). However, checkpoints are never used for resume.

## 10. Artifact Verification

**YES, post-training.** `validate_wob_seed42_artifacts.sh` runs a validator that checks
required files, metadata consistency, and training completion. However, the main runner
does not verify intermediate stage outputs before proceeding.

## 11. Root-Cause Hypotheses for Repeated Interruption

### H1: Kaggle "Failed to save draft" (HIGH CONFIDENCE)
Kaggle notebooks auto-save drafts. When outputs under `/kaggle/working/` are large or
changing rapidly (e.g., checkpoint writes during training), draft-save can fail. This is
a known Kaggle issue. The user sees "Failed to save draft" messages.

### H2: Long silent periods trigger Kaggle timeout (MEDIUM CONFIDENCE)
Kaggle may disconnect notebooks that produce no stdout for extended periods. The pip
install, Lance build, and validation evaluation stages can be silent for minutes.

### H3: Rerun destroys state, causing infinite restart loop (HIGH CONFIDENCE)
When the user reruns after an interruption, `rm -rf "$REPO_DIR"` destroys the repo,
and training starts from scratch. This creates a loop: interrupt → rerun → clean →
restart from 0 → interrupt again.

### H4: Disk quota exhaustion (MEDIUM CONFIDENCE)
Kaggle provides ~20GB of working disk. WOB Lance datasets + checkpoints + outputs may
approach this limit, especially if old outputs accumulate across reruns.

### H5: Session timeout (LOW-MEDIUM CONFIDENCE)
Kaggle GPU sessions have a 12-hour limit. At ~13 updates/sec, 15,000 updates take
~19 minutes of pure training. With data preparation overhead, the total should be
well within limits. However, if Lance build is slow, this could be a factor.

## 12. Recommended Fix List

1. **Replace `rm -rf` with safe repo update**: Use `git pull` if repo exists, clone only
   if absent.
2. **Add resume support to update-based training**: Load checkpoint if present and skip
   completed updates.
3. **Pass `--resume` flag in runner**: Enable checkpoint resume by default.
4. **Add heartbeat logging**: Wrap all long stages with periodic timestamp output.
5. **Capture logs to files**: Tee stdout/stderr to timestamped log files.
6. **Add comprehensive preflight**: Check CUDA, VRAM, disk, Python, imports, datasets.
7. **Add environment snapshot**: Save GPU info, disk info, pip list before training.
8. **Add artifact finalization**: Write manifest JSON with SHA256 hashes of all outputs.
9. **Add fail-closed safety**: Refuse locked-test paths, evaluation commands, missing data.
10. **Add disk space monitoring**: Check available disk before and during training.
11. **Add stage-level progress markers**: Write stage completion files so resume can skip
    completed stages.

## 13. Next Command for User

See `cloud/wob_p1_seed42/README_KAGGLE_RELIABLE_RUN.md` for the exact Kaggle cell to
paste after the hardening changes are applied.

## 14. 2026-06-18 Seed42 Artifact And Stale Debug Update

The downloaded seed42 success bundle was verified separately from the failure-debug archive:

- Success artifact SHA256:
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`
- Validator status: `wob_seed42_validated`
- Updates completed: `4000`
- Best update: `1500`
- Best validation-normal loss: `0.6093359693480057`
- `validation_buggy_used_for_fit_select=false`
- `locked_test_materialized=false`
- `locked_test_scored=false`
- `evaluation_run=false`

The accompanying failure-debug archive is classified as `STALE_DEBUG_FALSE_POSITIVE`. Its robust
preflight report failed because CUDA inspection referenced `total_mem` on
`torch._C._CudaDeviceProperties`, while the success bundle later recorded CUDA training and a
passed validator. The debug archive also detected the nested official Kaggle dataset roots that
the earlier shallow input check rejected.

Follow-up hardening:

- robust preflight now reads `total_memory` with a compatibility fallback;
- robust preflight uses the shared Kaggle root detector for nested official dataset mounts;
- finalization removes a stale failure-debug tarball after a successful training and validator
  pass;
- the tarball validator can validate the downloaded bundle directly from the tarball plus SHA256
  sidecar without extracting raw data into the repository.
