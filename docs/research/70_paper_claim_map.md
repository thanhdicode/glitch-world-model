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
| `R5-XGame` is the active mandatory binary-discrimination gate. | allowed now | `docs/research/r5_xgame_plan.md`, `docs/research/phase_b_r5_xgame_execution_report.md` | "active Phase B gate" | "validated result" |
| The repository provides a frozen four-role `R5-XGame` split, staged runner, Kaggle launcher, and local validator. | allowed now | `docs/research/16_claim_registry.md`, `docs/research/r5_xgame_runbook.md` | "execution-ready tooling" | "completed metric evidence" |
| Locked-test materialization and scoring remain false. | allowed now; required flag | `docs/research/16_claim_registry.md` | exact flag wording | any locked-test result |
| Paper package work may proceed for methods, protocol, limitations, reviewer FAQ, and figure/table templates. | allowed now | roadmap + readiness docs | "prep-only paper lane" | "final paper results complete" |

## Blocked Until Phase B Intake Validation

- Main binary results table
- Final abstract
- Final conclusion
- Superiority language
- Cross-source comparison table
- Phase D empirical conclusions
- Any `R5-XGame` metric statement

## Evidence Rule

A sentence is paper-safe only if it is supported by the claim registry and consistent with the
current roadmap/current-state docs. Remote execution status alone is never sufficient evidence.
