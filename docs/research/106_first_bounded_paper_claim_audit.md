# 106 - First Bounded Paper Draft Claim Audit

Date: 2026-06-24
Status: bounded paper package claim control

## Framing

The manuscript is framed as:

> a leakage-aware empirical evaluation of latent-surprise signals for gameplay glitch detection

It is not framed as a state-of-the-art method paper, full game-QA solution, temporal-localization
benchmark, cross-game generalization proof, or SIGReg contribution.

## Results Paragraph Map

| Manuscript paragraph | Registered claims | Required qualifiers |
| --- | --- | --- |
| TempGlitch support and leakage paragraph | C-090, C-092 | frozen, pair-disjoint, non-locked, same support |
| TempGlitch best LeWM metrics paragraph | C-091 | seed44/config exactness, 12/22 support, bounded |
| TempGlitch baseline and interpretation paragraph | C-091 | AUROC CI overlap, small support, high FPR, no broad superiority |
| R5-XGame result paragraph | C-084, C-088 | frozen non-locked 12/60 split, overlapping CI |
| Cross-family non-comparability paragraph | C-082, C-084, C-088 | separate distribution/protocol, no generalization |
| Exploratory aggregation/seed paragraph | C-089 | descriptive recorded-row summary, not causal ablation |
| R5-WOB discussion paragraph | C-079, C-082 | positive-probe only, zero normal-negative evaluation |

## Abstract And Conclusion Map

- The abstract's TempGlitch support and metrics map to C-090--C-092.
- Its R5-XGame status statement maps to C-084/C-088.
- Its negative claim boundary maps to C-082 and the notes for C-088/C-091.
- The conclusion repeats the same bounded observations without adding a deployment, localization,
  generalization, SIGReg, or locked-test conclusion, and now points to local submission
  finalization rather than a new compute gate.

## Wording Audit

Required wording retained:

- frozen split;
- non-locked;
- same-support where methods are compared;
- bounded;
- small evaluation/calibration support;
- wide and overlapping AUROC confidence intervals;
- high TempGlitch FPR@95TPR.

Rejected or rewritten:

- "LeWM beats baselines" -> "the best recorded LeWM row shows stronger observed same-support
  separation within the frozen non-locked split";
- "detects glitches generally" -> bounded episode discrimination only;
- "generalizes" -> result families are explicitly separate and not directly comparable;
- "temporal localization" -> binary video labels do not support localization;
- "SIGReg improves performance" -> no controlled SIGReg evidence;
- any locked-test wording -> locked test remains unmaterialized and unscored.

## Artifact And Build Audit

- TempGlitch result source: report 101 and claims C-090--C-092.
- R5-XGame source: reports 96/97 and claims C-084/C-088/C-089.
- R5-WOB boundary: C-079/C-082.
- Output artifacts remain outside Git; exact hashes are in report 101 and the provenance appendix.
- Local `pdflatex`, `bibtex`, `biber`, and `latexmk` are unavailable, and the repository does not
  vendor `llncs.cls` or `splncs04.bst`. Typeset compilation and page-fit review therefore remain
  pending.
