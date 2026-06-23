# 102 - Paper Results Table Plan

Date: 2026-06-24
Status: bounded paper-package plan

## Main Table 1 - TempGlitch Pair-Disjoint Follow-up

Use the same-support rows from report 101. Show the best LeWM AUROC row and best baseline AUROC
row with AUROC, AUPRC, F1, precision, recall, balanced accuracy, FPR@95TPR, and pair-bootstrap
AUROC/F1 intervals. The caption must say `frozen`, `non-locked`, `pair-disjoint`, `12 normal-negative`,
and `22 buggy-positive`.

Paper-ready metrics: all displayed metrics and intervals because they are validator-backed and
support-matched. The table must retain the small-support and overlapping-AUROC-CI note.

## Secondary Table 2 - Bounded R5-XGame Comparison

Use report 96 only. Show the best recorded LeWM row, `feature_distance`, and `frame_diff` on the
frozen 12-normal-negative / 60-buggy-positive split. Keep the `R5-XGame` table visually separate
from TempGlitch: the datasets, calibration support, action modes, class balance, and model training
lineage differ, so their absolute metrics cannot be used as a direct cross-game comparison.

Paper-ready metrics: the exact best-row metrics and intervals already recorded in report 96.
Exploratory metrics: family means and the aggregation/scorer summaries in report 97.

## Table 3 - Limitations And Claim Boundary

| Evidence surface | What it supports | What it does not support |
| --- | --- | --- |
| TempGlitch follow-up | bounded same-support separation on one frozen pair-disjoint split | broad superiority, localization, SOTA |
| R5-XGame | bounded ranking on one positive-heavy non-locked split | cross-game generalization, action benefit |
| R5-WOB | pipeline execution and positive-probe signal | binary discrimination |
| Locked test | no result; gate closed | any locked-test metric or claim |

## Table 4 - Failure Modes And Reviewer Risks

| Risk | Evidence symptom | Required paper treatment |
| --- | --- | --- |
| Small negative support | TempGlitch 12 negatives; XGame 12 negatives | show counts and wide CIs |
| Calibration fragility | TempGlitch uses 2 normal calibration episodes | name threshold source and support |
| High operating-point FPR | best TempGlitch FPR@95TPR = 0.7500 | report, do not hide behind AUROC |
| Seed sensitivity | XGame seed44 exceeds seeds42/43 | show as limitation, not stable effect |
| Label granularity | binary video/episode labels | forbid temporal-localization wording |
| Domain/protocol mismatch | zero-action TempGlitch versus real-action WOB | prohibit direct causal/action claims |
| Public non-locked reuse | both main families are validation evidence | avoid final-benchmark language |

## Comparison Rules

Directly comparable:

- rows within one validated bundle when manifest, support, labels, threshold policy, and protocol
  match;
- the two TempGlitch follow-up headline rows;
- the three R5-XGame rows in report 96.

Not directly comparable:

- TempGlitch follow-up metrics versus R5-XGame metrics;
- R5-WOB positive-probe outputs versus any binary metric family;
- old Phase 6D exposed/sequential-subset results versus the current pair-disjoint follow-up;
- window-level pilot metrics versus episode-level follow-up metrics.

## Blocked Claims And Results

Blocked until new compute or Kaggle: stronger learned baselines, new LeWM seeds, SIGReg on/off,
action-conditioning, full VideoGlitchBench, new WOB/XGame scoring, and GPU inference throughput.
Blocked regardless of compute until its separate release gate: locked-test results.
