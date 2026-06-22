---
name: WOB/Gate7 window-manifest builders
description: The three divergent window-manifest builders and the memory + protocol constraints any change must keep in lockstep.
---

# Window-manifest builders are triplicated

There are three independent `_build_window_manifest`/`build_canonical_manifest` copies that
construct the canonical Gate 7 / R5-WOB window manifest, and they diverge on calibration-count
semantics. A change to one almost always needs the same change in the others:

- `r5_wob_staged.py` — the **active Kaggle path**. Expected calibration count is derived:
  `len(calibration_episodes)` from the eval rows. Streams rows to CSV; returns `(row_count, fingerprints)`.
- `r5_wob_eval.py` — keeps a **hardcoded `expected_calibration_episode_count=12`** plus a
  `role_by_episode` membership check. Returns `(rows, fingerprints)`.
- `lewm_lance_eval.build_canonical_manifest` (gate7) — defaults to `calibration_episode_count=2`.

**Why:** the `materialize_lance` stage OOM-killed on Kaggle (exit 120, no traceback) because the
builder loaded full window rows (`pixels`/`action` tensors), re-read each window once per metadata
key, and held both datasets + both sample lists + the full row list at once.

**How to apply:** manifests need metadata only — never decode `pixels`/`action`. Use
`open_metadata_dataset()` + `iter_metadata_samples()` (single read per window), process normal then
buggy **sequentially** with `del` + `gc.collect()` between them, and stream/release rather than
retaining the full row list. Must stay invariant: locked/test rows rejected, buggy never calibration,
exact `MANIFEST_FIELDS` order, and the verbatim error strings ("invalid calibration episode count",
"duplicate window_id", "locked-test rows") that regression tests match on.

A native `lance` column scan is NOT a valid substitute for `swm.data.LanceDataset`: `window_id` /
`dataset_window_index` come from the `num_steps`/`frameskip` windowing and must match `_score_dataset`.
