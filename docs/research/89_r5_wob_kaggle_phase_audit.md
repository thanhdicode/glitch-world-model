# 89 - R5-WOB Kaggle Phase Audit

Date: 2026-06-22
Status: `INFRASTRUCTURE_AUDIT_ONLY`

This note audits the repeated non-locked `R5-WOB` Kaggle failures as an engineering phase review.
It does not report new WOB metrics, does not open locked test, and does not expand claim scope.

## Purpose

Explain why the `R5-WOB` Kaggle path appeared to "keep failing", identify the real structural
causes across attempts, and document the hardening changes required before the next browser-driven
Kaggle run.

## Executive Summary

The failures were not one recurring bug. They were a sequence of hidden assumptions exposed one
layer at a time:

1. too little failure evidence in the old monolithic path;
2. staged Lance directory marker handling;
3. incompatible LanceDB / PyLance runtime pins;
4. repo-root import assumptions in notebook-style subprocess entrypoints.

Each fix was necessary but insufficient to expose the next latent assumption. The recurring
experience came from layered infrastructure fragility, not from a single unpatched line.

## Historical Failure Chain

### 1. Monolithic failure with insufficient debug evidence

- Earlier `R5-WOB` retries could fail before producing a useful debug payload.
- The downloaded failure archive was effectively empty.
- Result: failure class remained `UNKNOWN_NEEDS_MORE_LOGS`.

Mitigation that followed:

- Introduced the staged `R5-WOB` pipeline with per-stage markers and resumable phases.

### 2. `.lance` directories treated like regular files

- The staged path reached `materialize_lance`.
- Stage marker recording expected regular files, but Lance datasets are directories.
- Result: retry infrastructure failed while validating or recording `.lance` outputs.

Mitigation that followed:

- Added directory-aware marker hashing and stale-Lance cleanup tests.

### 3. Runtime contract mismatch: stable-worldmodel vs LanceDB/PyLance

- `stable-worldmodel==0.1.1` was paired with `lancedb==0.25.3` and `pylance==0.39.0`.
- The package metadata floor is higher than those pins.
- Result: `AttributeError: 'LanceDBConnection' object has no attribute 'list_tables'`.

Mitigation that followed:

- Raised pins to `lancedb==0.30.0` and `pylance==4.0.0`.
- Added tests to prevent regression below the metadata floor.

### 4. Notebook subprocess import-path failure

- The notebook verified imports in inline Python blocks and passed a Lance write/read smoke test.
- It then failed when invoking:
  `python scripts/run_r5_wob_stage.py --stage preflight ...`
- Error:
  `ModuleNotFoundError: No module named 'cloud'`

Root cause:

- `glitch_detection` lives under `src/` and is installed by the editable install.
- `cloud/` is a top-level repo directory and is not installed by `pyproject.toml`.
- Inline Python blocks ran with the repo root visible on `sys.path`, so `cloud.*` imports worked.
- Script entrypoints ran in a mode where only the script directory and installed packages were
  visible, so `cloud.*` was no longer importable.

This is the clearest example of why local tests stayed green while the notebook still failed.

## Why It Felt Like "It Keeps Failing"

Because every repaired outer layer allowed execution to reach the next hidden dependency:

- no logs -> cannot classify;
- staged logs available -> Lance directory contract exposed;
- Lance directory fixed -> dependency contract exposed;
- dependency contract fixed -> packaging/import-path contract exposed.

The phase was under-audited for environment boundaries. The codebase had reasonable unit coverage
for pure Python logic, but less coverage for the exact Kaggle entrypoint style used by notebook
cells and background jobs.

## Structural Weak Points Identified

1. `src/` code depended on top-level repo modules outside the installed package set.
2. Tests mostly imported modules directly instead of exercising script entrypoints in subprocesses.
3. Notebook guidance duplicated some shell-runner behavior, allowing drift between the two paths.
4. Kaggle runtime correctness depended on both package pins and execution context.

## Hardening Actions Required

### Packaging boundary fix

- Move reusable WOB Kaggle helpers into `src/glitch_detection/wob_kaggle_common.py`.
- Keep `cloud/wob_kaggle_native/common.py` as a compatibility shim only.
- Make `src/glitch_detection/r5_wob_staged.py` import from the installed `glitch_detection`
  package rather than from top-level `cloud/`.

### Entrypoint regression coverage

- Add subprocess tests that run:
  - `scripts/run_r5_wob_stage.py --help`
  - `scripts/validate_r5_wob_stage_outputs.py --help`
  - `scripts/assemble_r5_wob_from_stages.py --help`
- Force those subprocesses to use only `src` on `PYTHONPATH`, not the repo root.

This directly simulates the notebook/subprocess class of failures that slipped through before.

### Notebook operational rule

- Prefer a single-cell overnight path or the canonical staged shell script.
- If any notebook calls Python entrypoint scripts directly, ensure it does not rely on repo-root
  imports that are absent from the editable install.

## Claim Boundary

- This audit adds no WOB result.
- This audit adds no locked-test activity.
- This audit supports only infrastructure-readiness and failure-analysis wording.

## Next Safe Action

After the packaging-boundary fix and subprocess regression coverage both pass, reopen the Kaggle
run only through the hardened notebook or canonical staged shell path, then classify the next run
from its downloaded success or failure bundle rather than from notebook UI memory alone.
