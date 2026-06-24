# Paper Draft

The paper draft is deliberately cautious and centers the verified pair-disjoint non-locked
TempGlitch follow-up, with R5-XGame as a separate bounded secondary result and reproducibility
appendices. It does not claim broad superiority, state of the art, locked-test results, WOB
training/evaluation results, SIGReg benefit, real-time operation, or temporal localization.

## Submission Readiness Status

| Surface | Status | Notes |
| --- | --- | --- |
| First bounded draft | complete | Abstract through conclusion, discussion, reproducibility, tables, appendices, reviewer audit, and submission gate docs are populated. |
| Springer format | structurally complete | `main.tex` uses `llncs`; official Springer files are still required. |
| Bibliography | expanded; final review required | Entries have checked metadata and stable URLs/DOIs where available. |
| Results | bounded, validator-backed | Main TempGlitch follow-up and secondary R5-XGame tables are populated with explicit support/claim limits. |
| Anonymized source | ready for review build | `main.tex` now uses anonymous-submission metadata; camera-ready metadata still needs a later pass. |
| Locked test | closed | Not materialized and not scored. |
| R5-WOB | positive-probe only | Not a binary-benchmark result. |
| PDF compile | blocked locally | `pdflatex`, `bibtex`, `biber`, `latexmk`, `llncs.cls`, and `splncs04.bst` are unavailable locally. |
| Page count | pending | Requires an official Springer Author Kit compile after the missing tools/files are provided. |
| Similarity screening | pending | Must run before submission. |

## Springer/LNICST note

`paper/main.tex` now targets the official Springer `llncs` class and `splncs04` bibliography
style. The repository does not vendor `llncs.cls` or `splncs04.bst`. To compile in Overleaf or a
local LaTeX install, provide the official Springer conference template files.

Recommended Overleaf setup:

1. Start from the official Springer `llncs` template.
2. Replace the template `main.tex` with [paper/main.tex](<C:/Users/ADMIN/Desktop/glitch-world-model/paper/main.tex>).
3. Upload the `paper/sections/`, `paper/appendices/`, `paper/tables/`, `paper/figures/`, and
   `paper/references.bib` contents.
4. Keep the anonymous-submission metadata in place for review builds; replace it only for a later
   camera-ready package.

Generated LaTeX build files are gitignored. Every empirical edit must remain synchronized with the
claim registry, source matrix, reviewer audit, submission gate docs, and report 106 paragraph
audit.
