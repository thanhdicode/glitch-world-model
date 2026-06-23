# 101 - TempGlitch Pair-Disjoint Follow-up Results

Date: 2026-06-24
Status: validated bounded non-locked evidence

## Executive Verdict

The artifact-only TempGlitch follow-up is complete and validator-backed. Within the frozen
pair-disjoint non-locked split, the best recorded LeWM row has stronger observed same-support
separation than the recorded simple baselines. This is a narrow split-qualified observation, not
a broad superiority result: evaluation support is small, uncertainty is wide, the best LeWM
FPR@95TPR is high, and the binary episode labels do not support temporal localization.

## Command Used

```powershell
C:\Python314\python.exe scripts/run_tempglitch_followup_pair_disjoint.py --r5-output-dir outputs/r5_tempglitch_identical_episode --train-lance outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance --validation-normal-lance outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance --validation-buggy-lance outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance --output-dir outputs/tempglitch_followup_pair_disjoint
```

This command recomputed episode-level summaries and statistics from existing validated artifacts.
It did not train, rescore windows, launch Kaggle, download data, or access locked test.

## Input Artifacts

- Validated `R5` family: `outputs/r5_tempglitch_identical_episode/`
- Frozen R5 manifest SHA256:
  `93327b661bd419944b57fb33112ec79264cb8a7b27708252c8507f3d3410f620`
- Train-normal Lance: `outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance`
- Validation-normal Lance: `outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance`
- Validation-buggy Lance: `outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance`
- Best-row seed44 raw scores SHA256:
  `6dc1f0646380f279125c018b630c7abc3a162ab55a2f062564410919b2061019`
- Baseline raw scores SHA256:
  `cf6fb7f2caaac7b9c91cf9d1956fbddb09eed64333335700d088c9a35538b66d`

## Output Artifacts

The complete local bundle is under `outputs/tempglitch_followup_pair_disjoint/`. Repository policy
keeps `outputs/` uncommitted, so the evidence is preserved below by exact paths, hashes, support,
and metric summaries.

## Calibration Split

The threshold for every row is the 95th percentile of exactly two calibration-normal episode
scores:

- `Godot_Blinking_Normal_106`
- `Godot_Frozen_Animation_Platformer_Normal_107`

The two episodes are frozen before evaluation and are excluded from evaluation support.

## Evaluation Support

| Role | Episodes |
| --- | ---: |
| Calibration normal | 2 |
| Evaluation normal-negative | 12 |
| Evaluation buggy-positive | 22 |
| Evaluation total | 34 |
| Manifest windows | 30,549 |

All 60 comparison rows use this same support tuple.

## Leakage Checks

| Cross-role key | Overlap |
| --- | ---: |
| `source_episode_id` | 0 |
| `pair_id` | 0 |
| `source` | 0 |

`validation_buggy_used_for_fit_select=false`, `locked_test_materialized=false`, and
`locked_test_scored=false` are validator-enforced.

## Same-Support Comparison

| Family | Configuration | AUROC | AUPRC | F1 | Precision | Recall | Balanced accuracy | FPR@95TPR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LeWM | seed44, `lewm_l2_max`, episode `mean` | 0.7159 | 0.8026 | 0.7143 | 0.7500 | 0.6818 | 0.6326 | 0.7500 |
| Baseline | `feature_distance`, episode `top2_mean` | 0.6136 | 0.7310 | 0.1600 | 0.6667 | 0.0909 | 0.5038 | 0.8333 |

## Best LeWM Row

The highest recorded LeWM AUROC is seed `44`, scorer `lewm_l2_max`, episode aggregation `mean`.
Its threshold is `1.11839184011`; its confusion counts are TP `15`, FP `5`, FN `7`, TN `7`.

## Best Baseline Row

The highest recorded baseline AUROC is `feature_distance` with `top2_mean` episode aggregation.
Its threshold is `0.413786972315`; its confusion counts are TP `2`, FP `1`, FN `20`, TN `11`.

## Confidence Intervals

Pair-grouped bootstrap intervals use 1,000 valid replicates.

| Row | AUROC 95% CI | F1 95% CI |
| --- | --- | --- |
| Best LeWM | [0.5349, 0.8770] | [0.5854, 0.8293] |
| Best baseline | [0.4636, 0.7545] | [0.0000, 0.3575] |

The AUROC intervals overlap. The estimates therefore do not establish general method
superiority.

## Limitations

- The split is non-locked and validation-only.
- Evaluation contains only 12 normal-negative and 22 buggy-positive episodes.
- Threshold calibration uses only two normal episodes.
- The best LeWM FPR@95TPR is `0.7500`.
- Bootstrap intervals are wide and the best-row AUROC intervals overlap.
- TempGlitch supplies binary video labels rather than verified temporal spans.
- This follow-up does not test SIGReg benefit, action-conditioning benefit, cross-game
  generalization, or state of the art.

## Claim Boundary

Allowed interpretation: the best recorded LeWM configuration shows stronger observed separation
than the recorded simple baselines on the exact frozen pair-disjoint, non-locked, same-support
TempGlitch follow-up split.

No inference may be made about broad LeWM performance, benchmark leadership, temporal
localization, SIGReg benefit, cross-game generalization, or locked-test performance.

## Exact Paper-Safe Wording

> Within the frozen non-locked TempGlitch follow-up split, the best LeWM configuration shows
> stronger same-support separation than the recorded simple baselines; however, the evaluation
> support is small, confidence intervals are wide and overlapping for AUROC, and FPR@95TPR
> remains high.

## Exact Paper-Forbidden Wording

- "LeWM beats baselines."
- "LeWM detects gameplay glitches generally."
- "LeWM is state of the art."
- "The model generalizes across games."
- "SIGReg improves glitch detection."
- "The method localizes glitches temporally."
- "Locked-test performance is known."

## Artifact Hashes

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `followup_manifest.csv` | 7,897,250 | `f9e38950dc0c9f156d58a7d228ff0172ec65c86c4063ab4f918006bffc9f1d25` |
| `followup_manifest.sha256` | 66 | `8cfa321a738daf2a4643c0a323ca708c1f60582d112c979123c7ac5cb7aefa4a` |
| `followup_episode_scores.csv` | 415,551 | `7e1a6f3390c933fdd8cfd70adc579e0b464049e3aab92d28e56f97f8ea09103e` |
| `followup_comparison.csv` | 32,009 | `81dcfe164d19906f1cb82e7e4108c848778a5f50fdb65303448ad7896b15cdae` |
| `followup_metrics.json` | 92,553 | `51ad3b860c0b8354adec74376dc9e9fcc87d172aed399a73c0a284d0bd8b8831` |
| `followup_provenance.json` | 4,476 | `14701a28ab92f2c3244df2f6a2d8cb7d5eac2f35cf38e446cc668be3a0ff5852` |
| `FOLLOWUP_REPORT.md` | 1,426 | `4ef51fc4bfc06695f65cb665014b89e8a38ae8422b67d2ed98ef95fcb7295820` |
| `followup_command.txt` | 469 | `66810951d952d381af6196a4648793b62237cb495d2e53c54c8c3ab49c1c7271` |
| `followup_validator_receipt.json` | 1,712 | `706d93c781e85ec03a013a1eb84aa5311a0f080d5ce1e05bb091fd3d72e14ae1` |

Validator status: `followup_validated`. Source metrics status: `followup_complete`.
