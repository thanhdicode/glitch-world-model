# FISAT Submission Package Plan

Date: 2026-06-18

Status: planning

## Objective

Prepare a clean Springer/LNICST submission package without expanding unsupported claims.

## Package Components

1. `paper/main.tex` plus all included section, appendix, and table files.
2. Official Springer `llncs` template files supplied outside the repository.
3. `paper/references.bib` after verified bibliography expansion.
4. A frozen claim map and source matrix.
5. Validation outputs from the repository command suite.
6. Overleaf compile log and page-count notes.
7. Similarity-screening record.

## Pre-Submission Review

1. Confirm all manuscript claims remain inside `docs/research/70_paper_claim_map.md`.
2. Confirm all section sources remain inside `docs/research/71_paper_source_matrix.md`.
3. Confirm the bounded results table still refers only to the non-locked TempGlitch
   validation-only identical-episode family.
4. Confirm the paper still excludes locked-test and WOB evaluation claims.

## Deferred Until Later

- Final abstract
- Extended literature review
- Any figure set beyond later approved, source-backed additions
- Any wording that implies SOTA, broad superiority, or generalization beyond the bounded family

## Current Status

- Scaffold: complete.
- Springer format: structurally complete, pending official Author Kit compile.
- Bibliography: expanded with checked metadata; final venue-style review still required.
- Results: bounded to the non-locked TempGlitch validation-only R5 family.
- Locked test: closed.
- WOB-P1 seed42: pending separate empirical gate.
- PDF compile: blocked locally by LaTeX/template availability.
- Page count: pending Overleaf compile.
- Similarity screening: pending.
