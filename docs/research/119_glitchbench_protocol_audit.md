# 119 - GlitchBench Protocol Audit

Date: 2026-06-24
Status: local P3 preparation complete; benchmark metrics still pending K2

## Source And Access

- Source dataset page: `https://huggingface.co/datasets/glitchbench/GlitchBench`
- Access path used locally: Hugging Face dataset viewer rows API for the public `validation` split
- Local ingestion script: `scripts/download_glitchbench_subset.py`
- Downloaded local subset for this preparation pass: `24` viewer rows, yielding `23` grouped
  `reddit_id` keys because one key repeated inside the sampled slice

## Observed Fields

The current public viewer path exposed the fields used by the local ingestion pipeline:

- `id`
- `reddit`
- `game`
- `glitch-type`
- `source`
- `image`

The benchmark artifact used here is image-level. The local pipeline materializes repeated-frame
clips from each static image and adds a paired synthetic-normal clip for train-normal support.

## Label Mapping

- Public downloaded rows are treated as `Buggy`.
- Synthetic reference clips are treated as `Normal`.
- The local protocol records this explicitly through `raw_label` and `mapped_label`.
- `synthetic_normal=true` is mandatory for every `Normal` row and forbidden for every `Buggy` row.

## Normal Construction Policy

- GlitchBench does not supply natural normal gameplay companions in the accessed public viewer path.
- This repo therefore constructs synthetic normal clips by repeating a fixed reference image from
  the checked-in WOB documentation assets.
- These rows are useful for a bounded train-normal protocol only.
- They must never be described as natural normal gameplay evidence.

## Leakage Risks And Grouping

- Primary grouping key: `reddit_id`
- Rationale: multiple viewer rows can come from the same public post/event, so the group key must
  be explicit and split-aware.
- Frozen local split result for the current preparation slice:
  - grouped keys observed: `23`
  - selected train-normal sources: `12`
  - selected validation-normal sources: `12`
  - selected validation-buggy sources: `12`
  - selected clip records: `36`
  - reported cross-split grouped leakage: `0`

## Temporal Labels

- No temporal span labels were observed in the accessed public viewer path.
- The local protocol therefore sets `temporal_label_available=false`.
- GlitchBench remains unsuitable for temporal-localization claims in this repo.

## K2 Can And Cannot Prove

K2 can support:

- a second bounded public benchmark table beyond TempGlitch
- a leakage-aware image-level comparison study under the repo's train-normal-only discipline
- honest reporting of how LeWM, simple baselines, and learned baselines behave on this static-image
  auxiliary benchmark

K2 cannot support:

- temporal localization
- natural normal gameplay performance
- cross-game generalization
- broad superiority or SOTA claims
- any locked-test result

## Current Local Artifact Status

- `scripts/freeze_glitchbench_split.py` produced a deterministic local freeze
- `scripts/build_k2_glitchbench_kaggle_dataset.py` produced a package zip
- local K2 input zip SHA256:
  `d2c6be8f83d99cb6a04578532f0f80d620c168342ff3e630b4e6b5389c62b038`
- `scripts/validate_glitchbench_bundle.py` validated the built package locally with false locked-test
  flags
