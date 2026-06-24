# Paper Claim Map

Date: 2026-06-24
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
| `R5-XGame` intake is now reproducible across LF/CRLF checkouts because the frozen manifest is validated by normalized CSV content, while legacy tarball/hash fields in older `stage_package.json` files remain non-authoritative. | allowed now | `docs/research/94_r5_xgame_intake_reconciliation.md`, `docs/research/16_claim_registry.md` | "cross-platform intake reconciliation" | "the old package receipt itself proves the repaired tarball SHA" |
| Within the frozen non-locked `R5-XGame` split, the best recorded LeWM row is above the best recorded baseline rows, but the comparison remains bounded to this split and should not be rewritten into broad superiority language. | allowed now | `docs/research/96_r6_xgame_bounded_comparison.md`, `docs/research/16_claim_registry.md` | "within the frozen split" | "LeWM beats baselines generally" |
| The repository provides a frozen four-role `R5-XGame` split, staged runner, Kaggle launcher, and local validator. | allowed now | `docs/research/16_claim_registry.md`, `docs/research/r5_xgame_runbook.md` | "execution-ready tooling" | "completed metric evidence without limitations" |
| Locked-test materialization and scoring remain false. | allowed now; required flag | `docs/research/16_claim_registry.md` | exact flag wording | any locked-test result |
| Paper package work may proceed for methods, protocol, limitations, reviewer FAQ, and figure/table templates. | allowed now | roadmap + readiness docs | "prep-only paper lane" | "final paper results complete" |
| The pair-disjoint TempGlitch follow-up is validator-backed on the same 12 normal-negative / 22 buggy-positive evaluation support for every row. | allowed now | `docs/research/101_tempglitch_followup_results.md`, `docs/research/16_claim_registry.md` | "frozen pair-disjoint non-locked split" | "official held-out benchmark" |
| Within that exact TempGlitch split, seed44 `lewm_l2_max` with mean episode aggregation records stronger observed same-support separation than the simple baselines. | allowed with all qualifiers | same as above | "within the frozen non-locked TempGlitch follow-up split" | "LeWM beats baselines generally" |
| The TempGlitch AUROC intervals are wide and overlap, while the best LeWM FPR@95TPR is `0.7500`. | required limitation | same as above | report beside headline metrics | omit uncertainty or operating-point weakness |
| Every empirical paragraph in the first bounded draft is mapped to registered claims and evidence sources. | required manuscript control | `docs/research/106_first_bounded_paper_claim_audit.md` | “bounded evidence-backed draft” | “new evidence created by manuscript prose” |

## Still Blocked After Follow-up Validation

- Definitive or official-benchmark main result
- Final abstract
- Final conclusion
- Superiority language
- Direct cross-source metric comparison
- Phase D empirical conclusions
- Any broad `R5-XGame` or WOB generalization statement
- Any locked-test result statement

## Evidence Rule

A sentence is paper-safe only if it is supported by the claim registry and consistent with the
current roadmap/current-state docs. The TempGlitch follow-up now enables a bounded main table and
`R5-XGame` enables a bounded secondary table. Neither result justifies broad superiority,
cross-game generalization, temporal localization, SOTA, SIGReg benefit, or locked-test claims.
