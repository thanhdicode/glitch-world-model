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
2. Audit the current abstract against the final claim map; do not broaden it beyond validated evidence.
3. Finish the literature review from verified primary sources.
4. Keep every manuscript result bounded to validated artifacts; until V4 phases land, reports 101
   and 96 remain the main quantitative evidence and their support/CI limitations must stay visible.
5. Run similarity screening and document the result.
6. Check figures, tables, captions, and accessibility/alt-text requirements.

## Roadmap V4 Paper Upgrade

1. Execute Roadmap V4 Phase P1 locally before reopening any compute gate.
2. Treat learned baselines, GlitchBench, and ablations as V4 phases with their own validated outputs.
3. Use the official Springer kit during the later P7 submission-packaging pass.
4. Keep locked test closed unless a separate frozen validation decision and direct user command exist.
