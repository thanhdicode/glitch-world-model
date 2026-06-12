# LeWM Research MVP Source Audit

Status date: 2026-06-12
Result: `research_mvp_source_ready`

The Gate 6 checkpoint remains an engineering smoke artifact. A separate research MVP source was
audited and materialized from every locally available TempGlitch video that belongs to the frozen
non-locked train or validation partitions.

## Audited Scope

- 36 train-normal episodes and 34,844 four-step windows.
- 14 validation-normal episodes and 12,825 four-step windows.
- 22 validation-buggy episodes and 17,724 four-step windows.
- All five TempGlitch categories represented in validation.
- Zero source overlap and zero heuristic-pair overlap between train and validation.
- Zero test materialization and zero test scoring.

Lance inventory fingerprints:

- train-normal:
  `e6c48a35eef32edf43a6c78db37c52adcbbe656f47b2e453e1917365355f3aa1`;
- validation-normal:
  `bb89e66c6afa5d3af7728be8efd0bacbf49cfedca6704fd27cc6178f27e556e6`;
- validation-buggy:
  `02c2417579bb25cd683738106d0603c5ed7a70fb6f3271716f9c23b95bae10f1`.

A two-update CPU contract check verified the new research runtime controls and artifact metadata.
That check is not model-performance evidence. The next experiment is a 500-update Kaggle GPU
profile, followed by a frozen multi-seed main run only after throughput and memory are measured.

## Claim Boundary

This audit supports only the statement that a broader, leakage-checked, non-locked research MVP
source is ready. It does not support LeWM detection performance, convergence, superiority,
SIGReg benefit, temporal localization, or state of the art.
