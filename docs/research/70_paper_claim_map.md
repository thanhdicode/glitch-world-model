# Paper Claim Map

Date: 2026-06-23
Status: active paper-writing control document

## Paper Positioning

Preferred framing:

`a leakage-aware empirical evaluation of latent surprise for gameplay glitch detection`

Forbidden framing:

- state-of-the-art glitch detector
- LeWM fully solves gameplay QA
- cross-game generalized detector
- temporal-localization system

## Allowed Now

| Claim | Status | Evidence | Allowed wording | Forbidden overclaim |
| --- | --- | --- | --- | --- |
| `R5-WOB` is a validated provenance-bound non-locked positive-probe bundle. | allowed now | `docs/research/r5_wob_results_analysis.md`, `docs/research/16_claim_registry.md` | "positive-probe evaluation" | "complete binary benchmark" |
| `R5-WOB` demonstrates pipeline execution and class-conditional signal presence under a normal-calibrated threshold. | allowed now | same as above | "execution and signal presence" | "binary discrimination performance" |
| `R5-XGame` now has a validated live-output and tarball/sidecar intake receipt after a packaging-only repair. | allowed now | `docs/research/93_r5_xgame_validated_bundle_summary.md`, `PACKAGE_FIX_REPORT.md`, `docs/research/16_claim_registry.md` | "validated bundle integrity" | "new run or retraining" |
| `R5-XGame` provides non-locked binary validation evidence that latent surprise scores separate buggy-positive and normal-negative episodes, with the best recorded configuration reaching AUROC approximately `0.91` on the frozen split. | allowed now | `docs/research/93_r5_xgame_validated_bundle_summary.md`, `docs/research/16_claim_registry.md` | "bounded non-locked validation evidence" | "broad generalization, SOTA, or final benchmark" |
| The repository provides a frozen four-role `R5-XGame` split, staged runner, Kaggle launcher, and local validator. | allowed now | `docs/research/16_claim_registry.md`, `docs/research/r5_xgame_runbook.md` | "execution-ready tooling" | "completed metric evidence without limitations" |
| Locked-test materialization and scoring remain false. | allowed now; required flag | `docs/research/16_claim_registry.md` | exact flag wording | any locked-test result |
| Paper package work may proceed for methods, protocol, limitations, reviewer FAQ, and figure/table templates. | allowed now | roadmap + readiness docs | "prep-only paper lane" | "final paper results complete" |

## Still Blocked After Intake Validation

- Main binary results table
- Final abstract
- Final conclusion
- Superiority language
- Cross-source comparison table
- Phase D empirical conclusions
- Any broad `R5-XGame` or WOB generalization statement
- Any locked-test result statement

## Evidence Rule

A sentence is paper-safe only if it is supported by the claim registry and consistent with the
current roadmap/current-state docs. Validated intake enables bounded `R5-XGame` wording, but
remote execution status alone is never sufficient evidence and the validated bundle still does not
justify broad benchmark claims.
