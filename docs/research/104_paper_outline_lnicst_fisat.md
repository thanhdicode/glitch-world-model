# 104 - LNICST/FISAT Bounded Paper Outline

Date: 2026-06-24
Status: first bounded draft implemented; final submission prose remains provisional

## Proposed Title

**Leakage-Aware Evaluation of Latent Surprise for Gameplay Glitch Detection**

## Abstract Implementation

1. Problem: gameplay glitches are temporal and costly to review.
2. Gap: latent predictive surprise is plausible but weakly evidenced under leakage-aware game-video protocols.
3. Method: normal-only LeWM training, frozen episode aggregation, normal-calibrated thresholds, and pair/source-disjoint evaluation.
4. Results: validated TempGlitch follow-up and bounded R5-XGame observations with support and uncertainty.
5. Boundary: non-locked validation study; no SOTA, localization, broad generalization, or SIGReg claim.

The first bounded abstract is implemented. Do not broaden it during page-fit editing.

## Introduction

- Operational cost of visual gameplay QA.
- Why predictive latent surprise is worth testing.
- Leakage and paired-video structure as central evaluation threats.
- Contributions: protocol, reproducible evidence pipeline, bounded empirical observations, and transparent failure/claim analysis.

## Related Work Buckets

- JEPA and latent predictive world models.
- Video anomaly and out-of-distribution detection.
- Automated game testing and gameplay bug detection.
- Glitch datasets and temporal-label limitations.
- Leakage-aware evaluation and uncertainty reporting.

## Method

- LeWM encoder/predictor and latent-surprise scores.
- Explicit TempGlitch zero-action adaptation.
- Normal-only fitting and validation-only configuration handling.
- Window scoring and episode aggregation.
- Normal-P95 threshold policy.
- Simple baselines: frame difference and feature distance.

## Experiment Protocol

- Dataset lineage and licenses.
- Train/calibration/evaluation roles before windowing.
- Pair/source/episode leakage controls.
- TempGlitch support: 2 calibration normals; 12/22 binary evaluation.
- R5-XGame support: 12 calibration normals; 12/60 binary evaluation.
- Pair/group bootstrap confidence intervals.
- Locked test closed.

## Results Placement

- Main Table 1: TempGlitch pair-disjoint follow-up.
- Secondary Table 2: bounded R5-XGame comparison.
- Table 3: limitation/claim boundary.
- Table 4: failure modes and reviewer risks.
- Figure 1: pipeline and split diagram.
- Figure 2: score distributions or ROC/PR curves from existing validated episode scores, if generated without metric changes.
- Figure 3: provenance/evidence graph, optional.

## Limitations

- Small negative and calibration support.
- Non-locked public validation evidence.
- Binary labels, no temporal spans.
- High operating-point false-positive rate.
- Seed sensitivity and domain/action mismatch.
- Missing strong learned baseline and controlled ablations.

## Reproducibility

- Commands, git SHA, environment, hashes, and validator receipts.
- Artifact-retention policy: outputs outside Git, hashes and summaries tracked.
- Public interfaces and default lightweight CI.
- Exact claim registry and forbidden-claim appendix.

## Conclusion Boundary

The conclusion may state that the study establishes a reproducible leakage-aware evaluation and
finds bounded evidence that latent surprise can separate classes on two frozen non-locked splits.
It must not state general detection success, benchmark leadership, temporal localization,
cross-game generalization, SIGReg benefit, or locked-test performance.

The cautious first-draft conclusion is implemented. Treat it as provisional until official-kit
compile, page fit, and final claim audit.

## Required Figures And Tables

- Table 1: TempGlitch headline comparison with CIs.
- Table 2: R5-XGame bounded comparison with CIs.
- Table 3: limitations/claim matrix.
- Table 4: reviewer-risk/failure-mode matrix.
- Figure 1: leakage-aware protocol flow.
- Figure 2: existing-score distribution or ROC/PR visualization.
- Reproducibility appendix: artifact hashes and commands.

## Draft Files

- Core narrative: `paper/sections/01_introduction.tex` through
  `paper/sections/10_conclusion.tex`.
- Added discussion and reproducibility: `08a_discussion.tex`,
  `08b_reproducibility.tex`.
- Tables 1--4: TempGlitch, R5-XGame, claim boundary, reviewer risk.
- Figure plan: `paper/figures/PLAN.md`; no visual data invented.
- Paragraph audit: `docs/research/106_first_bounded_paper_claim_audit.md`.
