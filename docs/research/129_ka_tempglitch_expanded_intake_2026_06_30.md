# K-A TempGlitch Expanded Intake 2026-06-30

## Status

The user-downloaded K-A TempGlitch expanded output is locally intake-reviewed as a
non-locked, pair-disjoint validation artifact. The artifact should be treated as
auxiliary support-expansion evidence, not as the headline result.

Local source folder retained outside Git:

`C:\Users\ADMIN\Downloads\results (3)`

No raw videos, Lance datasets, checkpoints, Kaggle credentials, or output bundles are
committed to the repository.

## Expanded Input Summary

Source file:

`C:\Users\ADMIN\Downloads\results (3)\tempglitch_expanded\expanded_inputs_summary.json`

Recorded values:

| Field | Value |
|---|---:|
| Status | `expanded_inputs_ready` |
| Downloaded normal episodes | 175 |
| Downloaded buggy episodes | 175 |
| Limit per group | 35 |
| Frame stride | 4 |
| Max steps per episode | 384 |
| Train max episodes | 36 |
| Train-normal split episodes | 111 |
| Validation-normal split episodes | 31 |
| Validation-buggy split episodes | 38 |
| Test-normal split episodes | 33 |
| Test-buggy split episodes | 36 |
| Locked test materialized | `false` |

Categories represented: `Blinking`, `Frozen Animation`, `Shooting Error`,
`Stuck in Place`, and `Velocity Bug`.

## Follow-Up Validator Receipt

Source file:

`C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_validator_receipt.json`

Receipt values:

| Field | Value |
|---|---:|
| Status | `followup_validated` |
| Protocol | `tempglitch_followup_pair_disjoint_nonlocked` |
| Calibration episodes | 2 |
| Evaluation episodes | 67 |
| Positive evaluation episodes | 38 |
| Negative evaluation episodes | 29 |
| Window count | 15,290 |
| Comparison rows | 60 |
| Baselines | `feature_distance`, `frame_diff` |
| LeWM seeds | 42, 43, 44 |
| Validation buggy used for fit/select | `false` |
| Locked test materialized | `false` |
| Locked test scored | `false` |

Cross-role overlap is zero for `source_episode_id`, `pair_id`, and `source`.

Receipt hashes:

| Artifact | SHA256 |
|---|---|
| Manifest | `1f438bdc907f61acc59796bfa5b4fccaca2e614cfad19e6263f6013edbc9e4be` |
| Comparison | `030546425030d95b3d798283c6d4ea01e92d10012e30c75228e63ed3255d2b16` |
| Metrics | `36ff9ee84cc1bfd313c33d29f7a5e70b6480ec83e7073d01cbea0152f049aa9e` |
| Provenance | `1e4c330588193c8324140d3f848ec113ae19fc5bf9c57c3b4f0525b152482fa9` |
| Command | `c8720cfc9e76bb98ce9ec35b133440f434d70686952a98f54e8a81cfba0668c2` |

Calibration episode IDs:

- `Godot_Blinking_Normal_115`
- `Godot_Frozen_Animation_Platformer_Normal_123`

## Best Recorded Rows

Source file:

`C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_comparison.csv`

Best AUROC LeWM row:

| Field | Value |
|---|---:|
| Seed | 43 |
| Window scorer | `lewm_l2_max` |
| Episode aggregation | `mean` |
| AUROC | 0.700544 |
| AUPRC | 0.796566 |
| F1 | 0.701299 |
| Precision | 0.692308 |
| Recall | 0.710526 |
| Balanced accuracy | 0.648367 |
| FPR@95TPR | 1.000000 |
| TP / FP / FN / TN | 27 / 12 / 11 / 17 |
| AUROC 95% bootstrap CI | [0.570509, 0.816507] |
| F1 95% bootstrap CI | [0.579624, 0.805195] |

Best baseline AUROC row:

| Field | Value |
|---|---:|
| Method | `frame_diff` |
| Episode aggregation | `mean` |
| AUROC | 0.630672 |
| AUPRC | 0.733788 |
| F1 | 0.571429 |
| Precision | 0.720000 |
| Recall | 0.473684 |
| Balanced accuracy | 0.616152 |
| FPR@95TPR | 0.931034 |

Observed deltas for the best LeWM AUROC row versus the best baseline AUROC row:

| Metric | Delta |
|---|---:|
| AUROC | +0.069873 |
| AUPRC | +0.062778 |
| F1 | +0.129870 |
| Balanced accuracy | +0.032214 |

No `significance` output was present in the downloaded K-A folder at intake time.

## Safe Paper Use

Safe wording:

`The expanded TempGlitch K-A follow-up increases the non-locked pair-disjoint evaluation support
to 67 episodes (38 buggy-positive, 29 normal-negative). On this support, the best recorded LeWM
row reaches AUROC 0.7005 and AUPRC 0.7966, above the best recorded simple baseline AUROC 0.6307,
but intervals remain wide and no significance artifact is available.`

Forbidden wording:

- Do not call this a locked-test result.
- Do not call it broad TempGlitch superiority.
- Do not call it state of the art.
- Do not claim statistical significance.
- Do not claim temporal localization, cross-game generalization, SIGReg benefit, or
  action-conditioning benefit from this artifact.

## Interpretation

This artifact is scientifically useful because it removes the earlier small-support objection for
TempGlitch follow-up reporting: the evaluation now covers 67 episodes instead of the earlier
34-episode follow-up support. It is not the best headline metric, because K-B / R5-XGame remains
the strongest validated binary result at AUROC 0.909722 on its frozen non-locked split. K-A
expanded should therefore be used as a robustness/support-expansion result that strengthens the
method-paper narrative without overstating the metric.
