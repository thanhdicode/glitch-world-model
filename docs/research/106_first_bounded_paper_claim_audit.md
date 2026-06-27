# 106 - Full Method-Paper Claim Audit

Date: 2026-06-27
Status: full method-paper claim control after P7 rewrite

## Framing

The manuscript is now framed as:

> a leakage-aware evaluation of a JEPA-style latent-surprise detector for gameplay glitch detection

It is still not framed as a state-of-the-art benchmark paper, universal game-QA solution,
cross-game generalization proof, temporal-localization benchmark, SIGReg-improvement paper, or
locked-test result.

## Paragraph Map

| Manuscript surface | Registered claims | Required qualifiers |
| --- | --- | --- |
| TempGlitch support and leakage paragraph | C-090, C-092 | frozen, pair-disjoint, non-locked, same support |
| TempGlitch best LeWM metrics paragraph | C-091 | seed44/config exactness, 12/22 support, high FPR remains visible |
| Exact-support learned-baseline paragraph | C-095, C-100, C-101, C-102 | strongest learned row is `cnn_lstm` + `max`; paired AUROC delta crosses zero |
| K2 benchmark paragraph | C-096, C-103, C-110, C-111, C-112 | image-level, synthetic-normal, bounded negative comparison, threshold-calibration caveat |
| K3 ablation paragraph | C-097, C-106, C-113, C-114 | validation-normal mechanistic readout only; no detection-performance language |
| Qualitative timeline paragraph | C-098, C-115 | qualitative only, no temporal metric, no span labels |
| R5-XGame paragraph | C-084, C-088 | separate frozen non-locked family, no direct cross-family comparison |
| Cross-family non-comparability paragraph | C-082, C-084, C-088 | separate distribution/protocol/action mode/training lineage |
| R5-WOB boundary paragraph | C-079, C-082 | positive-probe only, zero normal-negative evaluation |

## Abstract And Conclusion Map

- The abstract maps its TempGlitch row to C-090--C-092.
- The abstract's learned-baseline statement maps to C-095/C-100/C-102.
- The abstract's K2 negative comparison maps to C-096/C-110/C-111/C-112.
- The abstract's K3 statement maps to C-097/C-113/C-114.
- The abstract's qualitative-timeline limitation maps to C-098/C-115.
- The conclusion repeats the same evidence boundary and ends with the official-build/submission
  handoff rather than a new compute promise.

## Wording Audit

Required wording retained:

- frozen split;
- non-locked;
- same-support where methods are compared;
- pair-disjoint for the main TempGlitch family;
- bounded or split-bounded interpretation;
- AUROC confidence-interval overlap and/or inconclusive paired comparison where relevant;
- high TempGlitch FPR@95TPR;
- qualitative-only wording for timelines.

Rejected or rewritten:

- "LeWM beats baselines" -> "the best recorded LeWM row shows stronger observed same-support
  separation on the frozen split";
- "learned baselines lose" -> bounded split-specific comparison only;
- "GlitchBench proves LeWM fails" -> bounded negative comparison on the exact K2 slice only;
- "SIGReg hurts performance" -> no measured prediction-loss benefit in the validated K3 artifact;
- "action conditioning helps or hurts" -> no stable directional action delta in K3;
- "temporal localization" -> no true span annotations, qualitative timelines only;
- any locked-test wording -> locked test remains unmaterialized and unscored.

## Artifact And Build Audit

- TempGlitch result source: report 101 and claims C-090--C-092.
- K1 source: report 118 and claims C-095/C-100/C-101/C-102.
- K2 source: report 122 and claims C-096/C-103/C-110/C-111/C-112.
- K3 source: report 126 and claims C-097/C-106/C-113/C-114.
- Timeline boundary source: reports 127/128 and claims C-098/C-115.
- R5-XGame source: reports 96/97 and claims C-084/C-088/C-089.
- R5-WOB boundary: C-079/C-082.
- Local `pdflatex`, `bibtex`, `biber`, and `latexmk` are unavailable, and the repository does not
  vendor `llncs.cls` or `splncs04.bst`. The paper is therefore source-ready and audit-ready, but
  not locally PDF-verified from this workspace.
