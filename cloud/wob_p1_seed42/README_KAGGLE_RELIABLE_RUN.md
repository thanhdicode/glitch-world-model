# WOB-P1 Seed42 — Reliable Kaggle Run Guide

This guide replaces the original one-cell approach with an interruption-safe runner.

## Required Kaggle Datasets

Attach these datasets to the notebook:

- `benedictwilkinsai/world-of-bugs-normal`
- `benedictwilkinsai/world-of-bugs-test`

## Kaggle Notebook Cell

Paste this as a single code cell. It is safe to re-run after interruption.

```bash
%%bash
set -Eeuo pipefail

REPO_URL="https://github.com/thanhdicode/glitch-world-model.git"
REPO_REF="main"
REPO_DIR="/kaggle/working/glitch-world-model"

# --- Safe repo setup: pull if exists, clone if not ---
if [[ -d "$REPO_DIR/.git" ]]; then
  echo "[REPO] Updating existing clone..."
  cd "$REPO_DIR"
  git fetch origin
  git checkout "$REPO_REF"
  git reset --hard "origin/$REPO_REF"
else
  echo "[REPO] Cloning fresh..."
  git clone "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
  git checkout "$REPO_REF"
fi

echo "[REPO] SHA: $(git rev-parse HEAD)"

# --- Run the hardened runner ---
bash cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_robust.sh
```

## What This Does

1. **Safe repo update** — Does not destroy existing outputs with `rm -rf`.
2. **Stage-level resume** — Completed stages (setup, preflight, lance build) are skipped
   on rerun.
3. **Training resume** — If a checkpoint exists from a previous interrupted run, training
   resumes from the last saved checkpoint.
4. **Heartbeat logging** — Prints a timestamped heartbeat every 2 minutes to prevent
   Kaggle from killing the session for inactivity.
5. **Log capture** — All stdout/stderr are saved to
   `/kaggle/working/wob_p1_seed42_logs/`.
6. **Preflight checks** — Verifies CUDA, VRAM, disk space, imports, and dataset
   availability before starting expensive operations.
7. **Fail-closed safety** — Refuses to touch locked-test paths or run evaluation.
8. **Artifact finalization** — Writes a manifest JSON with SHA256 hashes of all outputs.

## Expected Outputs

- `/kaggle/working/wob_outputs/wob_seed42/` — training outputs
- `/kaggle/working/wob_p1_metadata/` — run metadata
- `/kaggle/working/wob_p1_seed42_logs/` — logs and environment snapshots
- `/kaggle/working/wob_seed42_artifacts.tar.gz` — packaged artifacts
- `/kaggle/working/wob_seed42_artifacts.tar.gz.sha256` — tarball hash
- `/kaggle/working/wob_seed42_failure_debug.tar.gz` — on failure only

## Troubleshooting

### "Failed to save draft"

This is a known Kaggle issue when outputs change rapidly. The hardened runner mitigates
this by writing checkpoints at controlled intervals rather than continuously. If it
persists, the training will still complete — the draft-save failure does not affect the
actual computation.

### Session disconnected

Simply re-run the cell. The runner will:
- Skip already-completed stages
- Resume training from the last checkpoint
- Continue to validation and artifact packaging

### Disk space warning

The preflight check will warn if less than 5 GB is available. If disk is critically low,
consider cleaning old output tarballs:

```bash
ls -la /kaggle/working/*.tar.gz
```

### Training did not complete

Check the logs in `/kaggle/working/wob_p1_seed42_logs/` for error messages. The failure
handler will have packaged partial outputs into the debug tarball.

## Safety Notes

- Seed42 only.
- Real-action mode only.
- Validation-buggy stays excluded from fit and checkpoint selection.
- Locked test stays closed.
- Do not run seed43/44 yet.
- Do not run WOB evaluation yet.
