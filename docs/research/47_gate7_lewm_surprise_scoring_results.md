# Gate 7 LeWM Surprise Scoring

Status date: 2026-06-12
Result: `gate7_passed_local_cpu`

Gate 7 produced real per-window LeWM scores from the frozen Gate 6 v8 best weights. Local
scoring succeeded, so no Kaggle scoring fallback or new remote infrastructure was required.

## Frozen Inputs

- Best-weights SHA-256:
  `3feefb1d1001f53ec659b45e7f47cfbc6418f56ea763513f970ec5b333119dbe`.
- Model-config SHA-256:
  `edd8cc37fbe9af514e45f7a8ce1862977bf5ab390fb7546adee26bff255ba972`.
- Normal-validation Lance fingerprint:
  `63402e1e2f41bd49ba02de0a0dd9d7ac89f4c68d9f4e86c0c24c5f3b510a2d7d`.
- Non-locked buggy-probe Lance fingerprint:
  `3d931a6942457bd5a3ed1c8ddcdcbf6da0947211cb5054a09ed266f6b4018aea`.
- Evaluation code Git SHA: `f22e1be92fed098752069616deb7ed2b26b8fcc1`.

## Canonical Manifest

The manifest contains 10,081 four-frame windows:

- 8,993 normal windows from 10 normal episodes;
- 1,088 buggy windows from one non-locked buggy episode;
- 1,553 normal windows from two deterministically selected episodes reserved for threshold
  calibration;
- 8,528 evaluation windows: 7,440 normal and 1,088 buggy.

Calibration episodes:

- `Godot_Animation_Platformer_Normal_18`
- `Godot_Blinking_Normal_106`

Manifest SHA-256:
`c1b2971d259cf0cdc495c9b7b171d1bcb9f34d2c6c073e4bdd51cb60fcb00003`.

## Scoring Result

The isolated LeWM runtime used Python 3.10.12, PyTorch 2.12.0 CPU,
stable-worldmodel 0.1.1, and Lance 7.0.0. Every window has three MSE and three L2 transition
scores. All values are finite and preserve exact manifest order.

Score SHA-256:
`b68f1be33b9410db22a855082eb61dcab74abdd23571b361ce6219ca5289eefa`.

Metadata SHA-256:
`7021dce9f3825fec5e1bbe3b9fbeb502c327b96e4059bf3736cbf47b28a92d8b`.

Gate 7 verifies frozen-checkpoint gameplay scoring only. It does not establish robust glitch
detection, temporal localization, superiority, SIGReg benefit, or locked-test performance.
Locked test was neither materialized nor scored.
