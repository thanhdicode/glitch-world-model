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
| Paper package work may proceed for methods, protocol, limitations, reviewer FAQ, and figure/table templates. | allowed now | roadmap + readiness docs | "bounded local paper package" | "final benchmark paper is complete" |
| The pair-disjoint TempGlitch follow-up is validator-backed on the same 12 normal-negative / 22 buggy-positive evaluation support for every row. | allowed now | `docs/research/101_tempglitch_followup_results.md`, `docs/research/16_claim_registry.md` | "frozen pair-disjoint non-locked split" | "official held-out benchmark" |
| Within that exact TempGlitch split, seed44 `lewm_l2_max` with mean episode aggregation records stronger observed same-support separation than the simple baselines. | allowed with all qualifiers | same as above | "within the frozen non-locked TempGlitch follow-up split" | "LeWM beats baselines generally" |
| The TempGlitch AUROC intervals are wide and overlap, while the best LeWM FPR@95TPR is `0.7500`. | required limitation | same as above | report beside headline metrics | omit uncertainty or operating-point weakness |
| The K1 learned-baseline bundle validates locally and keeps locked-test flags false. | allowed now | `docs/research/117_kaggle_k1_learned_baselines_runbook.md`, `docs/research/16_claim_registry.md` | "validated learned-baseline intake" | "new benchmark evidence without qualifiers" |
| Within that same frozen support, `cnn_lstm` with max episode aggregation is the strongest learned baseline at AUROC `0.613636`, below the best LeWM row and numerically equal to the best `feature_distance` AUROC row. | allowed with all qualifiers | `docs/research/118_k1_learned_baseline_results.md`, `docs/research/16_claim_registry.md` | "bounded comparison on the current frozen support" | "learned baselines beat LeWM" |
| The strongest learned-baseline AUROC delta versus the best LeWM row crosses zero, so use "stronger observed separation" rather than "significant superiority." | required limitation | same as above | "stronger observed separation on this split" | "statistically significant superiority" |
| The downloaded K2 scientific bundle validates locally with SHA256-matched tarball intake, false locked-test flags, and the exact frozen `12`-train / `24`-validation image-level synthetic-normal split. | allowed now | `docs/research/120_kaggle_k2_glitchbench_runbook.md`, `docs/research/122_k2_glitchbench_results.md`, `docs/research/16_claim_registry.md` | "validated bounded K2 intake" | "official benchmark completion without limitations" |
| Within the validated K2 split, `feature_distance` and all three learned baselines reach AUROC/AUPRC `1.0` while the best recorded LeWM rows reach AUROC `0.5`, so K2 is a bounded negative comparison surface for LeWM on this exact slice. | allowed with all qualifiers | `docs/research/122_k2_glitchbench_results.md`, `docs/research/16_claim_registry.md` | "on this exact frozen image-level synthetic-normal split" | "learned baselines beat LeWM generally" |
| The normalized `lewm-k2-lewm-seed-artifacts` package and repaired K2 runner enabled the validated scientific run, but those readiness artifacts are not themselves scientific claims. | allowed now | `docs/research/120_kaggle_k2_glitchbench_runbook.md`, `docs/research/16_claim_registry.md` | "validated runner/input path" | "tooling alone proves performance" |
| GlitchBench in this repo is image-level, uses synthetic normal clips, and does not support temporal-localization claims. | required limitation | `docs/research/119_glitchbench_protocol_audit.md`, `docs/research/121_glitchbench_claim_boundary.md`, `docs/research/16_claim_registry.md` | "image-level bounded benchmark" | "temporal localization" |
| `--baseline-only` is an engineering smoke test and cannot support LeWM-vs-baseline claims. | required limitation | `docs/research/120_kaggle_k2_glitchbench_runbook.md`, `docs/research/121_glitchbench_claim_boundary.md`, `docs/research/16_claim_registry.md` | "engineering smoke test only" | "baseline-only benchmark evidence" |
| The K2 AUROC `1.0` non-LeWM rows still share thresholded F1 `0.6667` and balanced accuracy `0.5` under the train-normal `p95` rule, so ranking quality and threshold calibration must be described separately. | required limitation | `docs/research/122_k2_glitchbench_results.md`, `docs/research/16_claim_registry.md` | "perfect ranking on this split, not perfect calibration" | "perfect classification" |
| Controlled SIGReg and action-conditioning local ablation tooling exists, but K3 evidence is still pending. | allowed now as tooling only | `docs/research/16_claim_registry.md`, `scripts/run_r6_sigreg_ablation.py`, `scripts/validate_r6_ablations.py` | "tooling/readiness" | "SIGReg helps", "action conditioning helps" |
| Every empirical paragraph in the bounded submission package is mapped to registered claims and evidence sources. | required manuscript control | `docs/research/106_first_bounded_paper_claim_audit.md` | "bounded evidence-backed package" | "new evidence created by manuscript prose" |

## Still Blocked For Submission Finalization

- Definitive or official-benchmark main result
- Superiority language
- Direct cross-source metric comparison
- Phase D empirical conclusions
- Any broad `R5-XGame` or WOB generalization statement
- Any claim derived from `--baseline-only`
- Any SIGReg or action-conditioning effect statement before K3 validates
- Any locked-test result statement
- Official-kit compile, page-fit review, and build-warning audit
- Final anonymization and similarity-screen confirmation

## Evidence Rule

A sentence is paper-safe only if it is supported by the claim registry and consistent with the
current roadmap/current-state docs. The TempGlitch follow-up enables a bounded main table and
`R5-XGame` enables a bounded secondary table. Neither result justifies broad superiority,
cross-game generalization, temporal localization, SOTA, SIGReg benefit, or locked-test claims.
