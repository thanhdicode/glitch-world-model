# WOB R5 Staged Evaluation — Kaggle Notebook Runbook

**Protocol:** `wob_identical_episode_nonlocked`
**Shell runner:** `cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh`
**Last verified:** 2026-06-22 (Task #7 audit)

This runbook describes the 9 cell groups for the WOB R5 Kaggle notebook. Each cell includes its
purpose, exact code, expected output, and how to recognize success or failure.

---

## Required Datasets (attach before running)

| Slot | Dataset slug | Contents |
|---|---|---|
| 1 | `thanhdicode/world-of-bugs-normal` | WOB normal episodes with `NORMAL-TRAIN/` subdirectory |
| 2 | `thanhdicode/world-of-bugs-test` | WOB test episodes with `TEST/` subdirectory |
| 3 | `thanhdicode/wob-seed42-artifacts` | `wob_seed42_artifacts.tar.gz` + `.sha256` |
| 4 | `thanhdicode/wob-seed43-artifacts` | `wob_seed43_artifacts.tar.gz` + `.sha256` |
| 5 | `thanhdicode/wob-seed44-artifacts` | `wob_seed44_artifacts.tar.gz` + `.sha256` |

Accelerator: **GPU T4 x2** (T4 or better; P100 is blocked — sm_60 is below cu128 compute floor).

---

## Cell Group 1 — GPU + Environment Check

**Purpose:** Confirm GPU type, CUDA version, compute capability ≥ sm_70, and Python version.

```python
import subprocess, sys, torch

print(f"Python {sys.version}")
print(f"PyTorch {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    cc_major, cc_minor = torch.cuda.get_device_capability()
    device_name = torch.cuda.get_device_name(0)
    print(f"Device: {device_name}")
    print(f"Compute capability: sm_{cc_major}{cc_minor}")
    assert cc_major >= 7, f"STOP: compute capability sm_{cc_major}{cc_minor} is below sm_70. Request a T4 or A100 GPU."
print("GPU check passed.")
```

**Expected output:**
```
Python 3.10.x ...
PyTorch 2.x.x+cu...
CUDA available: True
Device: Tesla T4
Compute capability: sm_75
GPU check passed.
```

**Failure signals:**
- `AssertionError: STOP: compute capability sm_60` → Stop. Change accelerator to T4/A100.
- `CUDA available: False` → GPU not allocated. Check Kaggle settings → Accelerator.

---

## Cell Group 2 — Clone Repository

**Purpose:** Clone the latest `main` commit of the research repo into `/kaggle/working/`.

```python
import subprocess, os

REPO_URL = "https://github.com/thanhdicode/glitch-world-model.git"
REPO_DIR = "/kaggle/working/glitch-world-model"
TARGET_SHA = "REPLACE_WITH_LATEST_MAIN_SHA"  # e.g. "3cc0929..."

result = subprocess.run(
    ["git", "clone", "--depth", "1", REPO_URL, REPO_DIR],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)
assert result.returncode == 0, f"Clone failed: {result.stderr}"

# Verify SHA
sha = subprocess.run(
    ["git", "-C", REPO_DIR, "rev-parse", "HEAD"],
    capture_output=True, text=True, check=True
).stdout.strip()
print(f"Cloned commit: {sha}")
if TARGET_SHA != "REPLACE_WITH_LATEST_MAIN_SHA":
    assert sha.startswith(TARGET_SHA[:8]), f"SHA mismatch: got {sha}, expected {TARGET_SHA}"
print("Clone OK.")
```

**Expected output:**
```
Cloning into '/kaggle/working/glitch-world-model'...
Cloned commit: <sha>
Clone OK.
```

**Failure signals:**
- `Clone failed` → Check internet access (Kaggle must have internet enabled).
- SHA mismatch → Clear `TARGET_SHA` or update it to match the current `main`.

---

## Cell Group 3 — List Attached Datasets

**Purpose:** Confirm all 5 required datasets are mounted at `/kaggle/input/`.

```python
import os
from pathlib import Path

input_root = Path("/kaggle/input")
for child in sorted(input_root.iterdir()):
    if child.is_dir():
        top_level = sorted(p.name for p in child.iterdir())[:8]
        print(f"  {child.name}/  →  {top_level}")
```

**Expected output (dataset names may vary by slug):**
```
  wob-seed42-artifacts/  →  ['wob_seed42_artifacts.tar.gz', 'wob_seed42_artifacts.tar.gz.sha256']
  wob-seed43-artifacts/  →  ['wob_seed43_artifacts.tar.gz', ...]
  wob-seed44-artifacts/  →  ['wob_seed44_artifacts.tar.gz', ...]
  world-of-bugs-normal/  →  ['NORMAL-TRAIN']
  world-of-bugs-test/    →  ['TEST']
```

**Failure signals:**
- Missing slug → Attach the corresponding dataset in Kaggle → Data → Add Data.
- `NORMAL-TRAIN` absent → Wrong dataset slug for the normal episodes.
- `TEST` absent → Wrong dataset slug for the test episodes.

---

## Cell Group 4 — Verify Seed Artifact Datasets

**Purpose:** Confirm each seed tarball is present and optionally verify SHA256.

```python
import hashlib, sys
from pathlib import Path

input_root = Path("/kaggle/input")

def find_seed_artifacts(seed):
    tar_name = f"wob_seed{seed}_artifacts.tar.gz"
    sha_name = f"{tar_name}.sha256"
    for child in sorted(input_root.iterdir()):
        if not child.is_dir():
            continue
        tar = child / tar_name
        sha = child / sha_name
        if tar.is_file() and sha.is_file():
            return tar, sha
    raise FileNotFoundError(f"seed{seed}: could not find {tar_name} in {input_root}")

for seed in (42, 43, 44):
    tar, sha_file = find_seed_artifacts(seed)
    expected_sha = sha_file.read_text().split()[0]
    actual_sha = hashlib.sha256(tar.read_bytes()).hexdigest()
    match = "✅" if actual_sha == expected_sha else "❌ MISMATCH"
    size_mb = tar.stat().st_size / 1_048_576
    print(f"seed{seed}: {tar.name}  {size_mb:.1f} MB  SHA={match}")
    if actual_sha != expected_sha:
        print(f"  expected: {expected_sha}")
        print(f"  actual:   {actual_sha}")
```

**Expected output:**
```
seed42: wob_seed42_artifacts.tar.gz  XX.X MB  SHA=✅
seed43: wob_seed43_artifacts.tar.gz  XX.X MB  SHA=✅
seed44: wob_seed44_artifacts.tar.gz  XX.X MB  SHA=✅
```

**Failure signals:**
- `FileNotFoundError` → Dataset not attached or tarball filename mismatch.
- `SHA=❌ MISMATCH` → Corrupted upload. Re-upload the dataset.

---

## Cell Group 5 — Run Staged WOB R5 via Shell Runner

**Purpose:** Execute the full 8-stage pipeline (preflight → validate_package) via the shell runner.
This is the main execution cell and will take the majority of notebook wall-clock time (~2–4 hours).

```python
import subprocess, os

REPO_DIR = "/kaggle/working/glitch-world-model"
RUNNER = f"{REPO_DIR}/cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh"

env = os.environ.copy()
env.update({
    "REPO_DIR": REPO_DIR,
    "R5_WOB_DEVICE": "cuda",
    "R5_WOB_BASELINE_BATCH_SIZE": "4",
    "R5_WOB_LEWM_BATCH_SIZE": "2",
    "R5_WOB_N_BOOTSTRAP": "1000",
    "R5_WOB_SMOKE": "0",    # set "1" for a fast smoke check first
    "R5_WOB_FORCE": "0",    # set "1" to re-run completed stages
})

result = subprocess.run(
    ["bash", RUNNER],
    env=env,
    capture_output=False,  # stream to notebook output
    text=True,
)
print(f"\nRunner exit code: {result.returncode}")
if result.returncode != 0:
    print("RUNNER FAILED — see Cell Group 6 for log and Cell Group 9 for classification.")
```

**Expected terminal output (abbreviated):**
```
=== 1. Install lean staged R5-WOB runtime ===
=== 2. Detect mounted inputs ===
NORMAL_INPUT_ROOT=/kaggle/input/world-of-bugs-normal
TEST_INPUT_ROOT=/kaggle/input/world-of-bugs-test
WOB_SEED42_TARBALL=/kaggle/input/wob-seed42-artifacts/wob_seed42_artifacts.tar.gz
...
=== 3. Preflight ===
[r5_wob] preflight: validating frozen readiness ...
[r5_wob] preflight: resolving Kaggle normal/test dataset roots
...
=== 10. Validate and package ===
=== 11. Validate stage markers ===
=== DOWNLOAD SUCCESS FILES ===
/kaggle/working/r5_wob_identical_episode_outputs.tar.gz
/kaggle/working/r5_wob_identical_episode_outputs.tar.gz.sha256

Runner exit code: 0
```

**Failure signals:**
- Non-zero exit code → Check Cell Group 6 (log) and Cell Group 9 (classification).
- Stall after `=== 2. Detect mounted inputs ===` → Discovery issue; check Cell Group 6 for errors.
- `AttributeError: 'LanceDBConnection' has no attribute 'list_tables'` → LanceDB pin mismatch.
- `ModuleNotFoundError: No module named 'stable_worldmodel'` → Install step failed.

---

## Cell Group 6 — Tail Log

**Purpose:** Read the last 100 lines of the shell runner's persistent log to debug any failure.

```python
from pathlib import Path

log_path = Path("/kaggle/working/r5_wob_staged.log")
if log_path.exists():
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"=== {log_path} ({len(lines)} lines total) ===")
    print("\n".join(lines[-100:]))
else:
    print("Log file not found — runner may have failed during initialization.")
```

**Expected output on success:** Last lines show `=== DOWNLOAD SUCCESS FILES ===` and the tarball path.

**Failure signals:**
- Log absent → `exec > >(tee ...)` redirect failed; check runner initialization.
- Last line shows stage name + Python traceback → Identify the failing stage from `CURRENT_PHASE`.

---

## Cell Group 7 — List Success / Failure Artifacts

**Purpose:** Confirm which output files are present; determine success vs failure download path.

```python
import os
from pathlib import Path

working = Path("/kaggle/working")
success_tar = working / "r5_wob_identical_episode_outputs.tar.gz"
success_sha = Path(str(success_tar) + ".sha256")
failure_tar = working / "r5_wob_identical_episode_failure_debug.tar.gz"
failure_sha = Path(str(failure_tar) + ".sha256")

def show(path):
    if path.exists():
        size_mb = path.stat().st_size / 1_048_576
        return f"PRESENT  {size_mb:.2f} MB"
    return "ABSENT"

print(f"SUCCESS tarball:     {show(success_tar)}")
print(f"SUCCESS sha256:      {show(success_sha)}")
print(f"FAILURE debug tar:   {show(failure_tar)}")
print(f"FAILURE debug sha:   {show(failure_sha)}")

if success_tar.exists():
    print("\n→ Download SUCCESS pair and run offline intake validator.")
elif failure_tar.exists():
    print("\n→ Download FAILURE pair and classify per Cell Group 9.")
else:
    print("\n→ No output tarballs found. Check Cell Group 6 log.")
```

**Expected output on success:**
```
SUCCESS tarball:     PRESENT  XX.XX MB
SUCCESS sha256:      PRESENT  0.00 MB
FAILURE debug tar:   ABSENT
FAILURE debug sha:   ABSENT

→ Download SUCCESS pair and run offline intake validator.
```

---

## Cell Group 8 — Download Instructions

**Purpose:** Remind the user of the exact local steps after downloading from Kaggle.

```python
print("""
=== POST-DOWNLOAD INTAKE (run locally, NOT in Kaggle) ===

1. Download from Kaggle Output tab:
   - r5_wob_identical_episode_outputs.tar.gz
   - r5_wob_identical_episode_outputs.tar.gz.sha256

2. Run offline intake validator:
   python scripts/verify_r5_wob_upload.py \\
     --tarball path/to/r5_wob_identical_episode_outputs.tar.gz \\
     --sidecar path/to/r5_wob_identical_episode_outputs.tar.gz.sha256

3. If intake passes → metrics are now verified. Record in claim registry.

4. If intake fails → do NOT record any metric. Classify the failure and apply
   the minimum necessary fix before the next retry.

SAFETY:
- Do NOT commit the tarball or sidecar to git.
- Do NOT claim any WOB evaluation metric until verify_r5_wob_upload.py passes.
- Do NOT open R5-XGAME or R6 WOB ablations until intake passes.
""")
```

---

## Cell Group 9 — Failure Classification

**Purpose:** Parse the failure debug bundle and classify the failed stage against the known failure
mode registry for the next fix decision.

```python
import json, tarfile
from pathlib import Path

failure_tar = Path("/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz")
if not failure_tar.exists():
    print("No failure debug bundle found — run was successful or failed during initialization.")
else:
    with tarfile.open(failure_tar, "r:gz") as tar:
        try:
            member = tar.getmember("failure_debug/failure_summary.json")
            f = tar.extractfile(member)
            summary = json.loads(f.read().decode())
            print(json.dumps(summary, indent=2))
        except KeyError:
            print("failure_summary.json not found in bundle. Contents:")
            for m in tar.getmembers():
                print(" ", m.name)

    # Classification guide:
    print("""
=== FAILURE CLASSIFICATION GUIDE ===
phase = "install_runtime"  → Package install failed. Check pin versions.
phase = "detect_inputs"    → discover_r5_wob_input_overrides failed. Check attached datasets.
phase = "preflight"        → Seed artifact or dataset root missing. Check Cell Group 3/4.
phase = "materialize_lance"→ Lance build failed. Check LanceDB version match.
phase = "baseline_scores"  → Gate8 baselines failed. Likely data or manifest issue.
phase = "lewm_seed*"       → LeWM adapter or GPU error. Check CUDA and checkpoint SHA.
phase = "aggregate_metrics"→ Metric assembly failed. Check prior stage score CSVs.
phase = "validate_package" → Validator rejected outputs. Check r5_wob_metrics.json.

Exit code 1 = Python exception. Exit code 137 = OOM kill. Exit code 143 = timeout.
""")
```

**Expected output on failure:**
```json
{
  "schema_version": 1,
  "failure_class": "UNKNOWN_NEEDS_MORE_LOGS",
  "phase": "<stage_name>",
  "exit_code": <N>,
  "line_number": "<N>",
  "failed_command": "<cmd>",
  "git_sha": "<sha>",
  "output_dir_exists": true,
  "locked_test_materialized": false,
  "locked_test_scored": false
}
```

---

## Smoke Mode (Optional Pre-Check)

Before running the full pipeline, you can run smoke mode to verify the pipeline reaches all stages
on a tiny subset (2 calibration + 3 buggy windows, skips validate_package):

In Cell Group 5, set `"R5_WOB_SMOKE": "1"`. Expected terminal:
```
=== SMOKE MODE COMPLETE ===
/kaggle/working/.../r5_wob_identical_episode
```

Smoke outputs are **not paper-valid**. They confirm the pipeline runs end-to-end without errors.
Run full mode (`R5_WOB_SMOKE=0`) for paper-valid results.

---

## Troubleshooting Quick Reference

| Symptom | Likely cause | Action |
|---|---|---|
| Stall at `=== 2. Detect mounted inputs ===` | Discovery issue | Check that `NORMAL-TRAIN/` and `TEST/` exist in their dataset roots |
| `AttributeError: 'LanceDBConnection'` | LanceDB version mismatch | Verify shell runner installs `lancedb==0.30.0` |
| `ModuleNotFoundError: cloud` | Repo root not on PYTHONPATH | Should not happen; verify `REPO_DIR` is set and shell runner line 7 runs |
| `ModuleNotFoundError: stable_worldmodel` | Install step failed | Re-run Cell Group 5; check pip output |
| `AssertionError: compute capability sm_60` | P100 GPU assigned | Change Kaggle accelerator to T4 or A100 |
| `FileNotFoundError: seed* tarball` | Dataset not attached | Attach the missing seed dataset in Kaggle Data panel |
| `SHA256 mismatch` in Cell Group 4 | Corrupted upload | Re-upload the affected seed dataset |
| Exit code 137 | OOM kill | Reduce `R5_WOB_LEWM_BATCH_SIZE` to 1; reduce `R5_WOB_BASELINE_BATCH_SIZE` to 2 |
