# 128 - Temporal Localization Future Work

Date: 2026-06-26
Status: active limitation and future-work note

The current validated artifacts support binary episode/video discrimination, not temporal
localization metrics.

Window-level LeWM surprise timelines can be generated as qualitative illustrations, but cannot be
evaluated with temporal IoU or temporal AP without true ground-truth span annotations.

Temporal localization remains future work pending a benchmark with frame-level or time-span
annotations.

For this repository state, the safe interpretation is:

- qualitative LeWM surprise timelines may illustrate where surprise rises or falls within an
  episode;
- those figures do not validate glitch onset, offset, duration, or event-level recall;
- no temporal-localization claim may enter the paper until a validated artifact exposes real spans
  and a fail-closed metric pipeline is artifact-backed.

The current best future path is to adopt a benchmark whose public artifact verifiably contains
frame-level or time-span labels, then evaluate localization on a frozen non-locked split before
considering any broader claim.
