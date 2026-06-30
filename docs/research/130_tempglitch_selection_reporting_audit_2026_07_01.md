# 130 - TempGlitch Selection Reporting Audit 2026-07-01

## Status

No-GPU audit complete. The current TempGlitch evidence already contains the relevant max-style
LeWM window scorers, so the immediate fix is reporting hardening rather than rescoring or
retraining.

## Key Finding

`lewm_l2_max` is a window scorer. It is distinct from episode-level `max` aggregation. In the
validated TempGlitch artifacts inspected for this audit, the best AUROC rows use `lewm_l2_max`
with episode aggregation `mean`.

## Inspected Artifacts

| Artifact family | Comparison artifact | Safety metadata | Best AUROC row |
| --- | --- | --- | --- |
| R5 identical episode | `outputs/r5_tempglitch_identical_episode/r5_comparison.csv` | `outputs/r5_tempglitch_identical_episode/r5_metrics.json` | seed44 `lewm_l2_max`, episode `mean`, AUROC `0.69696969697`, AUPRC `0.796124555802`, F1 `0.723404255319`, 12 normal-negative / 22 buggy-positive evaluation episodes |
| Pair-disjoint follow-up | `outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv` | `outputs/tempglitch_followup_pair_disjoint/followup_metrics.json` | seed44 `lewm_l2_max`, episode `mean`, AUROC `0.715909090909`, AUPRC `0.802619294928`, F1 `0.714285714286`, 12 normal-negative / 22 buggy-positive evaluation episodes |
| K-A expanded follow-up | `C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_comparison.csv` | `C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_metrics.json` | seed43 `lewm_l2_max`, episode `mean`, AUROC `0.70054446461`, AUPRC `0.796565575405`, F1 `0.701298701299`, 29 normal-negative / 38 buggy-positive evaluation episodes |

## Generated Inspection Summaries

The reporting helper was run in Markdown mode and wrote inspection-only summaries under
`.test-tmp/tempglitch_selection_audit/`:

- `.test-tmp/tempglitch_selection_audit/r5_selection.md`
- `.test-tmp/tempglitch_selection_audit/followup_selection.md`
- `.test-tmp/tempglitch_selection_audit/ka_expanded_selection.md`

These helper outputs are intentionally uncommitted scratch artifacts.

## Paper And Claim Registry Audit

- Claim C-065 already records the R5 identical-episode best AUROC row as seed44 `lewm_l2_max`
  with mean episode aggregation.
- Claim C-091 already records the pair-disjoint TempGlitch best row as seed44 `lewm_l2_max`
  with mean episode aggregation.
- Claim C-118 already records the K-A expanded best row as seed43 `lewm_l2_max` with mean
  episode aggregation.
- Paper-facing text and tables already describe the pair-disjoint best LeWM row as
  `lewm_l2_max` plus episode `mean`; no paper or claim-registry synchronization edit was needed.
- Paper-facing text should continue to describe these as bounded, non-locked, validation-only
  observations with wide uncertainty and no broad superiority claim.

## Safety Boundary

- No GPU training was run.
- No window rescoring was run.
- No Kaggle action was taken.
- No locked-test materialization or scoring occurred.
- No output bundle, checkpoint, Lance dataset, raw data, cache, or credential was committed.

## Next Decision

Do not spend GPU on history-size or encoder changes until the K-C WOB binary intake status and
paper narrative gap are known. If a GPU lane opens later, combine history-size and encoder choices
into one controlled experiment family.
