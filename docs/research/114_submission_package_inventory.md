# 114 - Submission Package Inventory

Date: 2026-06-24
Status: local submission-package inventory

## Include In Submission Source Package

Core source:

- `paper/main.tex`
- `paper/references.bib`
- `paper/sections/*.tex`
- `paper/appendices/*.tex`

Referenced table files:

- `paper/tables/artifact_hashes.tex`
- `paper/tables/claim_map.tex`
- `paper/tables/dataset_inventory.tex`
- `paper/tables/limitations_claim_boundary.tex`
- `paper/tables/literature_matrix.tex`
- `paper/tables/r5_bounded_results.tex`
- `paper/tables/r5_xgame_results.tex`
- `paper/tables/r6_ablation_results.tex`
- `paper/tables/reviewer_risk.tex`

## Exclude From Submission Source Package

Internal helper files:

- `paper/README.md`
- `paper/TODO.md`
- `paper/figures/PLAN.md`
- `paper/figures/README.md`
- all `docs/context/*.md`
- all `docs/research/*.md`

Internal-only or currently excluded table files:

- `paper/tables/r5_wob_results.tex`
- `paper/tables/phase6d_results.tex`
- `paper/tables/phase6e_validation_metrics.tex`
- `paper/tables/README.md`

Repository-only controls:

- `scripts/`
- `tests/`
- `configs/`
- `outputs/`
- `data/`
- `external/`

## Evidence And Claim Documents To Keep Internal

These support the paper but are not part of the source upload:

- `docs/research/16_claim_registry.md`
- `docs/research/70_paper_claim_map.md`
- `docs/research/101_tempglitch_followup_results.md`
- `docs/research/106_first_bounded_paper_claim_audit.md`
- `docs/research/107_paper_draft_reviewer_audit.md`
- `docs/research/107_submission_readiness_checklist.md`
- `docs/research/108_submission_gap_analysis.md`
- `docs/research/109_kaggle_decision_gate.md`
- `docs/research/110_reference_and_bibliography_audit.md`
- `docs/research/111_anonymization_checklist.md`
- `docs/research/112_similarity_screening_plan.md`
- `docs/research/113_official_build_blocker_and_overleaf_plan.md`
- `docs/research/114_submission_package_inventory.md`

## Submission Rule

The upload set should contain only the anonymized LLNCS paper source required to compile the
current manuscript. Governance docs, claim-control docs, evidence memos, outputs, checkpoints,
and helper notes remain internal.
