# 113 - Official Build Blocker And Overleaf Plan

Date: 2026-06-24
Status: local build blocked; manual/Overleaf plan prepared

## Exact Missing Local Requirements

Tool audit:

- `pdflatex`: missing
- `bibtex`: missing
- `biber`: missing
- `latexmk`: missing

File audit:

- `llncs.cls`: missing from the repository
- `splncs04.bst`: missing from the repository

Additional check:

- no `llncs.cls` or `splncs04.bst` were found in the bundled workspace dependencies path

## Local Build Decision

A truthful local LLNCS build is not possible in the current workspace. Do not claim local PDF
build success, page count, or warning clearance from this machine.

## Overleaf Or Manual Build Plan

1. Start from the official Springer `llncs` author kit or official Overleaf LLNCS template.
2. Confirm the template provides `llncs.cls` and `splncs04.bst`.
3. Upload the paper source package:
   - `paper/main.tex`
   - `paper/references.bib`
   - `paper/sections/*.tex`
   - `paper/appendices/*.tex`
   - referenced table files from `paper/tables/`
4. Do not upload internal helper files such as:
   - `paper/README.md`
   - `paper/TODO.md`
   - `paper/figures/PLAN.md`
   - `docs/research/*.md`
5. Keep the anonymous-submission metadata in `paper/main.tex` for the review build.

## Referenced Table Upload Set

Upload these table files:

- `paper/tables/artifact_hashes.tex`
- `paper/tables/claim_map.tex`
- `paper/tables/dataset_inventory.tex`
- `paper/tables/limitations_claim_boundary.tex`
- `paper/tables/literature_matrix.tex`
- `paper/tables/r5_bounded_results.tex`
- `paper/tables/r5_xgame_results.tex`
- `paper/tables/r6_ablation_results.tex`
- `paper/tables/reviewer_risk.tex`

Do not upload these unless they are intentionally reintroduced:

- `paper/tables/r5_wob_results.tex`
- `paper/tables/phase6d_results.tex`
- `paper/tables/phase6e_validation_metrics.tex`

## What To Record After First Real Build

- PDF output path or Overleaf build identifier
- page count
- undefined citation warnings
- undefined reference warnings
- overfull and underfull box warnings
- bibliography/style warnings
- any PDF metadata issues relevant to anonymization

## Minimal Post-Build Log Template

- build surface:
- date:
- template source:
- page count:
- undefined citations:
- undefined references:
- overfull boxes:
- bibliography warnings:
- anonymization/PDF metadata notes:
