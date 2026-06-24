# Paper TODO

Date: 2026-06-24

## Before Overleaf Compile

1. Start from the official Springer `llncs` Author Kit or Overleaf template.
2. Upload `paper/main.tex`, `paper/references.bib`, `paper/sections/`, `paper/appendices/`,
   `paper/tables/`, and any approved figure assets.
3. Confirm `llncs.cls` and `splncs04.bst` come from the official Springer template.
4. Compile with BibTeX and record unresolved references, overfull boxes, page count, and warnings.

## Before FISAT Initial Submission

1. Replace placeholder author and institute metadata.
2. Audit the bounded abstract against page fit and the final claim map; do not broaden it.
3. Finish the literature review from verified primary sources.
4. Keep the results section bounded to reports 101 and 96 and retain their support/CI limitations.
5. Run similarity screening and document the result.
6. Check figures, tables, captions, and accessibility/alt-text requirements.

## Post-Draft Decision

1. Run the paper draft audit with the official kit when available.
2. Decide whether to stop at a bounded submission or request a new compute phase for stronger
   learned baselines/ablations.
3. Do not launch Kaggle, retrain, rescore new datasets, or access locked test from the paper track.
