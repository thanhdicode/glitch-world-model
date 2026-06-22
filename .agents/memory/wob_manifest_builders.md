---
name: WOB/Gate7 window-manifest builders
description: Window-manifest construction is triplicated and diverges on calibration count; changes must stay in lockstep and keep memory + protocol constraints.
---

# Window-manifest construction is triplicated

Three independent builders construct the canonical Gate 7 / R5-WOB window manifest, and they
**diverge on calibration-count semantics**, so a change to one almost always needs the same change
in the others. The active Kaggle path derives the expected calibration count from the eval rows; the
R5-WOB eval path hardcodes 12; the gate7 path defaults to 2. Search for the builders by name rather
than trusting a remembered file path.

**Why:** the `materialize_lance` stage OOM-killed on Kaggle (exit 120, no traceback) because a
builder decoded full window rows (image tensors), re-read each window once per metadata key, and held
both datasets plus both sample lists plus the full row list at once.

**How to apply:** manifests are metadata only — never decode pixels/action. Read each window exactly
once (do not add a separate "probe" read that re-reads index 0). Process the two datasets
sequentially, releasing each before opening the next, and stream/release rather than retaining the
full row list. Keep invariant: locked/test rows rejected, buggy never calibration, exact field order,
and the verbatim error strings the regression tests match on. A native `lance` column scan is not a
valid substitute for the windowed `LanceDataset`, because window ids/indices come from the
num_steps/frameskip windowing and must match the scorer.
