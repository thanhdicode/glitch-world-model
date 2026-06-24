# Paper TODO

Date: 2026-06-24

## Before Overleaf Compile

1. Start from the official Springer `llncs` Author Kit or Overleaf template.
2. Upload `paper/main.tex`, `paper/references.bib`, `paper/sections/`, `paper/appendices/`,
   `paper/tables/`, and any approved figure assets.
3. Confirm `llncs.cls` and `splncs04.bst` come from the official Springer template.
4. Compile with `pdflatex` plus `bibtex` or with `latexmk` after those tools are installed.
5. Record unresolved references, overfull boxes, page count, and warnings.

## Before FISAT Initial Submission

1. Keep the anonymous-submission metadata for the review package; prepare camera-ready metadata
   separately.
2. Audit the bounded abstract against page fit and the final claim map; do not broaden it.
3. Finish the literature review from verified primary sources.
4. Keep the results section bounded to reports 101 and 96 and retain their support/CI limitations.
5. Run similarity screening and document the result.
6. Check figures, tables, captions, and accessibility/alt-text requirements.

## Post-Draft Decision

1. Finalize the bounded submission package locally.
2. Use the official Springer kit to complete compile, page-fit, and warning review when available.
3. Keep stronger learned baselines or ablations as a separate future compute decision.
4. Do not launch Kaggle, retrain, rescore new datasets, or access locked test from the paper track.
