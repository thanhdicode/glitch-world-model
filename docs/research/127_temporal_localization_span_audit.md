# 127 - Temporal Localization Span Audit

Date: 2026-06-26
Status: completed

## Scope

This audit checks whether the current validated non-locked datasets and artifacts contain true
ground-truth temporal span annotations that would justify temporal localization metrics such as
temporal IoU or temporal AP.

Final decision:

`TEMPORAL_LOCALIZATION_METRICS_ALLOWED = false`

`K4_NOT_REQUIRED = true`

Reason:

- Current validated TempGlitch evidence uses binary video-level labels and a full-video positive
  interval proxy, not ground-truth glitch start/end annotations.
- Current validated R5-XGame and R5-WOB artifacts carry episode-level normal/buggy roles only.
- Current executable GlitchBench support is explicitly image-level and forces
  `temporal_label_available=false`.
- VideoGlitchBench appears span-rich on paper, but no public executable artifact is verified in
  this repository.

## Inspected Datasets And Artifacts

| Dataset / artifact | Classification | Evidence | Temporal-span verdict |
| --- | --- | --- | --- |
| TempGlitch follow-up | `BINARY_VIDEO_LABEL_ONLY` | [tempglitch.py](../../src/glitch_detection/tempglitch.py) writes full-video positive labels; [followup_manifest.csv](../../outputs/tempglitch_followup_pair_disjoint/followup_manifest.csv) has per-window metadata but no ground-truth start/end span columns; [101_tempglitch_followup_results.md](101_tempglitch_followup_results.md) states binary video labels only | No true spans |
| R5-XGame | `BINARY_VIDEO_LABEL_ONLY` | [r5_xgame_protocol.py](../../src/glitch_detection/r5_xgame_protocol.py) validates only `dataset_id/source/episode_id/pair_id/label/split/evaluation_role`; [r5_xgame_split.csv](../../configs/wob_protocol/r5_xgame_split.csv) has episode-level roles only; [r5_xgame_window_manifest.csv](../../outputs/r5_xgame/r5_xgame_window_manifest.csv) repeats episode labels per window without span boundaries | No true spans |
| R5-WOB | `BINARY_VIDEO_LABEL_ONLY` | [r5_wob_results_analysis.md](r5_wob_results_analysis.md) defines `R5-WOB` as a positive-probe bundle with episode-level normal/buggy roles and forbids temporal localization claims | No true spans |
| GlitchBench | `IMAGE_LEVEL_LABEL_ONLY` | [glitchbench_protocol.py](../../src/glitch_detection/glitchbench_protocol.py) requires `temporal_label_available=false` for every row and returns `image_level_only=true`; [119_glitchbench_protocol_audit.md](119_glitchbench_protocol_audit.md) states no temporal span labels were observed | No true spans |
| VideoGlitchBench / GliDe | `UNCLEAR_NEEDS_MANUAL_VERIFICATION` | [17_source_verification_log.md](17_source_verification_log.md) and [04_dataset_benchmark_map.md](04_dataset_benchmark_map.md) note temporal spans on paper but no verified public artifact or schema in this repo | Not executable here |
| Generic `LabelInterval` support | `NO_LABEL` for provenance by itself | [manifest.py](../../src/glitch_detection/manifest.py) defines `LabelInterval`, but the dataclass is only an interface and does not prove current artifacts carry true ground-truth spans | Interface only |

## Evidence By Dataset

### TempGlitch Follow-Up

- Code path: [tempglitch.py](../../src/glitch_detection/tempglitch.py)
- Relevant fields:
  - public metadata: `video`, `label`
  - local label CSV: `source,start_frame,end_frame,label`
- Critical evidence:
  - `write_tempglitch_full_video_labels()` computes one label interval per buggy video by taking the
    minimum and maximum manifest frame bounds for the entire source.
  - That conversion preserves CSV interfaces but does not recover true glitch onset or offset.
- Units:
  - frames/windows exist in manifests
  - ground truth remains binary at the video level

Conclusion:

`BINARY_VIDEO_LABEL_ONLY`

### R5-XGame

- Code path: [r5_xgame_protocol.py](../../src/glitch_detection/r5_xgame_protocol.py)
- Relevant fields:
  - `dataset_id`, `source`, `episode_id`, `pair_id`, `label`, `split`, `evaluation_role`
- Critical evidence:
  - The frozen split metadata contains episode-level roles only.
  - The materialized window manifest labels windows by episode role and episode label, not by
    verified glitch span boundaries.
- Units:
  - window indices are available
  - no ground-truth glitch start/end frames or timestamps are available

Conclusion:

`BINARY_VIDEO_LABEL_ONLY`

### R5-WOB

- Evidence note: [r5_wob_results_analysis.md](r5_wob_results_analysis.md)
- Relevant fields:
  - positive-probe episode roles only
- Critical evidence:
  - The validated bundle demonstrates class-conditional signal presence under a normal-calibrated
    threshold, but not a temporal span protocol.
  - The note explicitly forbids temporal localization claims.
- Units:
  - episode-level only in the validated result note

Conclusion:

`BINARY_VIDEO_LABEL_ONLY`

### GlitchBench

- Code path: [glitchbench_protocol.py](../../src/glitch_detection/glitchbench_protocol.py)
- Relevant fields:
  - `image_path`, `mapped_label`, `temporal_label_available`
- Critical evidence:
  - `validate_glitchbench_manifest()` raises if any row has `temporal_label_available=true`.
  - The local bounded protocol is image-level, with synthetic-normal counterparts.
- Units:
  - images only

Conclusion:

`IMAGE_LEVEL_LABEL_ONLY`

### VideoGlitchBench / GliDe

- Evidence notes:
  - [17_source_verification_log.md](17_source_verification_log.md)
  - [04_dataset_benchmark_map.md](04_dataset_benchmark_map.md)
- Critical evidence:
  - The paper describes temporal spans.
  - No verified public code/data release is available in this repository.
- Units:
  - unknown in executable artifact form here

Conclusion:

`UNCLEAR_NEEDS_MANUAL_VERIFICATION`

### `LabelInterval` As A Repository Structure

- Code path: [manifest.py](../../src/glitch_detection/manifest.py)
- Critical evidence:
  - The dataclass stores `source`, `start_frame`, `end_frame`, `label`.
  - Actual validated artifact rows still need provenance for those boundaries.
  - Current TempGlitch conversion uses full-video bounds derived from manifests, not verified
    temporal event boundaries.

Conclusion:

`NO_LABEL` as a provenance claim by itself

## Why Metrics Are Not Allowed

Temporal localization metrics require real ground-truth event boundaries. The current validated
artifacts provide:

- binary video or episode labels;
- per-window model outputs;
- per-window metadata indexes;
- interval-capable repository interfaces.

They do not provide:

- verified glitch onset/offset frames;
- verified event timestamps in seconds;
- a validated benchmark file that binds model windows to true temporal spans.

Window-level LeWM surprise series therefore remain useful for qualitative inspection only.

## K4 Decision

`K4_NOT_REQUIRED = true`

Reason:

- Metrics are not allowed because true spans are absent.
- Window-level LeWM score series already exist locally under the validated non-locked TempGlitch
  artifact family, so no extra Kaggle re-scoring is needed to produce qualitative timelines.
