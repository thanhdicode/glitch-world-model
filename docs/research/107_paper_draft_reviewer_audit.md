# 107 - Paper Draft Reviewer Audit

Date: 2026-06-24
Decision context: bounded local paper package, Path A

## Executive Summary

The current draft can support a cautious bounded empirical paper. The dominant reviewer risks are
support size, calibration fragility, wide uncertainty, and the absence of stronger exact-support
learned baselines or controlled ablations. Those are real weaknesses, but they do not invalidate
the paper if the framing stays narrow and evidence-qualified.

## Reviewer Concern Matrix

| # | Reviewer question | Current evidence answer | Remaining weakness | Kaggle needed | Safe wording for paper | Wording to avoid |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Why are there only 12 TempGlitch normal-negative evaluation episodes? | The frozen pair-disjoint follow-up uses the currently validated non-locked support and reports counts beside the metrics. | False-positive estimates remain fragile. | Not yet | "on the frozen 12-negative / 22-positive split" | "on a comprehensive TempGlitch benchmark" |
| 2 | Why is the TempGlitch threshold calibrated on only two normal episodes? | The two calibration episodes are named explicitly and excluded from evaluation. | Threshold stability is weak. | No | "threshold calibration uses two normal episodes" | "the threshold is well calibrated" |
| 3 | Does the AUROC gap prove LeWM is better than the baselines? | No. The AUROC intervals overlap, and the draft states only stronger observed same-support separation within the frozen split. | Reviewer skepticism is justified. | No | "stronger observed same-support separation" | "LeWM beats baselines" |
| 4 | Why is FPR@95TPR still so high? | The main TempGlitch row records FPR@95TPR = 0.7500 and the draft states it directly. | Operating-point utility remains weak. | No | "FPR@95TPR remains high" | "high-recall operation is practical" |
| 5 | Are two bounded result families enough to support a paper? | They are enough for a bounded empirical study focused on protocol and evidence containment. | They are not enough for a broad benchmark or SOTA paper. | No | "bounded leakage-aware empirical evaluation" | "definitive benchmark study" |
| 6 | Why are the baselines so simple? | The paper includes `frame_diff` and train-normal-fitted `feature_distance` because they are validator-backed on exact support. | No exact-support learned video baseline is present. | Later, optional | "named simple baselines" | "comprehensive baseline suite" |
| 7 | Why is there no learned video baseline? | No learned video baseline is available on the exact follow-up support. The paper treats that as a limitation, not a hidden omission. | Stronger reviewers may expect one. | Optional future phase | "no learned baseline on exact support" | "LeWM outperforms prior learned methods" |
| 8 | Why is there no SIGReg ablation? | The repository has no controlled SIGReg on/off evidence for this paper lane. | Mechanistic conclusions are blocked. | Optional future phase | "no controlled SIGReg evidence" | "SIGReg improves detection" |
| 9 | Why is there no action-conditioning evidence? | TempGlitch uses explicit zero-action input, while R5-XGame uses its own validated real-action path; they are not used to infer action benefit. | The paper cannot discuss action-conditioning advantage. | Optional future phase | "the two action modes are not directly comparable" | "actions help" |
| 10 | Can the paper claim temporal localization? | No. TempGlitch labels are binary video-level labels, not verified temporal spans. | Window scores may tempt over-interpretation. | Not with current labels | "binary episode discrimination only" | "the model localizes glitches" |
| 11 | Why is locked test absent? | Locked test remains intentionally closed under repo policy because the evidence is still validation-only and bounded. | Final-benchmark credibility is limited. | No | "locked test remains unmaterialized and unscored" | "hidden test performance" |
| 12 | Does R5-XGame prove cross-game generalization? | No. It is a separate frozen non-locked split with different distribution, class balance, action mode, and training lineage. | Readers may still mentally compare the numbers. | No | "separate bounded evidence family" | "generalizes across games" |
| 13 | Why is R5-XGame positive-heavy? | The current held-out binary set is 12 normal-negative and 60 buggy-positive episodes, and that imbalance is named in the draft. | Precision and false-positive interpretation remain less stable than a more balanced split. | No | "positive-heavy split" | "balanced benchmark" |
| 14 | Why include R5-WOB at all if it is not a binary benchmark? | It demonstrates pipeline execution and positive-class signal presence under a normal-calibrated threshold. | It cannot support AUROC/FPR binary claims. | No | "positive-probe only" | "WOB benchmark result" |
| 15 | Are the claims reproducible? | Yes at the bounded level: validators, hashes, commands, and claim-registry mappings are all tracked. | Official-kit PDF build is still blocked locally. | No | "validator-backed, provenance-bound evidence" | "fully submission-complete artifact stack" |
| 16 | Why should reviewers care if the evidence is so narrow? | The value is in the leakage-aware protocol, exact-support comparison, and honest negative-boundary reporting for gameplay anomaly research. | Some venues may still prefer broader empirical scale. | No | "bounded empirical study" | "production-ready QA solution" |
| 17 | Could the result be driven by split-specific quirks? | Yes, that risk exists, and the draft keeps the conclusion split-bounded and uncertainty-qualified. | External validity remains open. | Later, optional | "within this frozen split" | "robust across gameplay settings" |
| 18 | Why are the best rows chosen by recorded AUROC? | The paper reports descriptive best-row comparisons from a frozen recorded bundle and does not retrain or refit thresholds on evaluation. | Best-row reporting can still look optimistic. | No | "best recorded row within the frozen bundle" | "optimal model selected for deployment" |
| 19 | Does the paper overstate the contribution as a method paper? | No. The framing is an evaluation paper around latent-surprise signals and leakage-aware protocol controls. | Title and abstract still need final page-fit review under the official kit. | No | "evaluation of latent surprise" | "new state-of-the-art method" |
| 20 | Why not postpone the paper until stronger compute is available? | Because the current package already supports a truthful bounded paper and the missing compute would strengthen, not rescue, the core claim surface. | Reviewer appetite for broader baselines is still a risk. | Not yet | "current evidence supports a bounded study" | "the evidence is already exhaustive" |

## Bottom-Line Reviewer Position

The paper is defensible if it is sold as a bounded leakage-aware evaluation with explicit limits.
The current weaknesses argue for restraint in framing, not for inflating the result or quietly
turning the paper into a different kind of claim.
