# 92 - R5-WOB `materialize_lance` Window-Manifest Memory Crash Analysis

Date: 2026-06-22
Status: `R5_WOB_MATERIALIZE_LANCE_MEMORY_FIX_READY`

## Executive Summary

The Kaggle `R5-WOB` staged run crashed inside the `materialize_lance` stage while building the
canonical window manifest. The kernel reported exit code `120` with no Python traceback, which
Kaggle classifies as `possible_resource_exhaustion`. This document records the confirmed root cause,
the memory-bounded fix that was applied to all three divergent manifest builders, the resource
telemetry artifact added for future runs, and the protocol-safety confirmation that the fix changes
no evaluation semantics.

Claims below are tagged `VERIFIED` (established from the repository source) or `INFERRED` (a
reasoned conclusion that was not independently reproduced in this environment, because the isolated
LeWM runtime — `stable_worldmodel`, `lance`, `psutil` — is not installed here).

## Failure Classification

- `RESOURCE_EXHAUSTION_MEMORY` (manifest construction phase).

Evidence:

- Exit code `120` with no traceback and Kaggle's `possible_resource_exhaustion` marker. `INFERRED`
  that the process was killed (OOM-style) rather than raising, because a Python exception would have
  produced a traceback and a non-`120` exit.
- The crash occurred in `materialize_lance`, after Lance datasets are written and before scoring.
  `VERIFIED` that the window-manifest build is the memory-heaviest step in that stage.

## Confirmed Root Cause

The window-manifest builder loaded full window rows, including the `pixels` and `action` image
tensors, and held multiple large in-memory copies simultaneously.

`VERIFIED` from the pre-fix source:

1. The manifest builder opened each dataset with `_lance_dataset(..., include_metadata=True)`, whose
   `keys_to_load` always included `pixels` and `action` in addition to the metadata columns. Every
   window therefore decoded its image tensors even though the manifest only needs metadata.
2. Each window was read once per metadata key via
   `{key: str(dataset[index][key]) for key in METADATA_KEYS}`. With seven metadata keys this indexed
   (and re-materialized) the same window seven times.
3. The builder constructed both `normal_samples` and `buggy_samples` lists in full, then built a
   combined `manifest_rows` list, then validated it, then wrote it — so the normal dataset, the buggy
   dataset, both sample lists, and the full row list were all alive at the same time.

Together these multiply peak resident memory far beyond what the manifest content requires. On the
constrained Kaggle kernel this is sufficient to trigger an OOM kill. `INFERRED` that the pixel/action
decode is the dominant term, since metadata strings are small relative to image tensors.

## The Fix

A metadata-only, single-read, sequential, streaming manifest builder, applied consistently across
all three previously divergent copies so the pipeline does not regress through a forgotten path.

`VERIFIED` changes:

1. **Metadata-only reader.** `lewm_lance_eval._lance_dataset` gained a `metadata_only` parameter that
   sets `keys_to_load` to the metadata columns only (no `pixels`/`action`).
   `open_metadata_dataset(path)` requests that projection, probes the metadata keys on the first
   window to confirm support, and returns `(dataset, metadata_only_flag)`. If the isolated runtime
   raises `RuntimeError` (the LeWM runtime is missing) the error is re-raised unchanged; any other
   failure to honor the metadata-only projection falls back to the full `keys_to_load`, recording
   `metadata_only=False`. Both paths still go through `swm.data.LanceDataset` on purpose: `window_id`
   and `dataset_window_index` are defined by the `num_steps`/`frameskip` windowing and must match
   `_score_dataset`. A native `lance` column scan iterates raw rows that do not align with that
   windowing, so it is intentionally not used. `INFERRED` that `stable_worldmodel.data.LanceDataset`
   honors a metadata-only `keys_to_load`; the fallback exists precisely because that could not be
   verified in this environment.
2. **Single read per window.** `iter_metadata_samples(dataset)` reads each window exactly once and
   yields a metadata dict, replacing the seven-reads-per-window comprehension.
3. **Sequential datasets with explicit release.** The normal dataset is opened, drained, then
   `del`-eted with `gc.collect()` before the buggy dataset is opened, so the two datasets are never
   resident together.
4. **Streaming to CSV (staged path).** The active Kaggle staged builder
   (`r5_wob_staged._build_window_manifest`) now streams rows straight to `_window_manifest.csv` via
   `csv.DictWriter` and returns a row count plus fingerprints, instead of materializing and returning
   the full row list. Its caller `run_materialize_lance` consumes the count for the
   `window_row_count` payload field.

## Resource Telemetry

`VERIFIED`: `ResourceTelemetry` and `capture_resource_usage()` were added. The staged manifest build
records bounded RSS snapshots at `start`, per-dataset `open`/`done`, and `complete` checkpoints and
writes `resource_telemetry_materialize_lance.json` next to the manifest output. `capture_resource_usage`
uses `psutil` when present and degrades to the stdlib `resource.getrusage` `ru_maxrss` fallback when
`psutil` is unavailable, so the artifact is produced even on minimal kernels.

## Protocol-Safety Confirmation

`VERIFIED` that the fix changes no evaluation semantics:

- Locked-test guard preserved: rows whose split contains `locked` or equals `test` still raise
  "Canonical Gate 7 manifest must not contain locked-test rows."
- Buggy rows are never used for calibration: a buggy label with a non-`evaluation` role still raises,
  and calibration role is only assigned to normal-labeled windows whose episode is in the calibration
  set.
- WOB calibration episode count is still validated against the eval-row count (the staged path uses
  `expected_calibration_episode_count=len(calibration_episodes)`; the `r5_wob_eval` path keeps the
  hardcoded `12`), with the original "invalid calibration episode count" and "duplicate window_id"
  messages preserved verbatim.
- `MANIFEST_FIELDS` order is unchanged; the CSV header and row shape are byte-identical to the prior
  builder output.

## Verification Performed Here

`VERIFIED`: New unit tests use an in-memory fake dataset that records key access and read order. They
assert the builders never touch `pixels`/`action`, read each window exactly once, process datasets
sequentially, stream the expected row count to CSV, and emit the telemetry artifact. The full local
test suite passes. `INFERRED`: the end-to-end memory reduction on the real Kaggle kernel, which can
only be confirmed by a subsequent staged run with the new telemetry artifact attached.
