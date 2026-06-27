# Paper Draft

The paper draft is now a full method-paper rewrite built from validated P2--P6 evidence: the main
pair-disjoint non-locked TempGlitch follow-up, exact-support learned baselines, the bounded K2
GlitchBench slice, the K3 mechanistic ablation, qualitative surprise timelines, and the separate
R5-XGame secondary family. It still does not claim broad superiority, state of the art,
locked-test results, WOB binary-benchmark results, cross-game generalization, SIGReg benefit,
action-conditioning benefit, real-time operation, or temporal localization.

## Submission Readiness Status

| Surface | Status | Notes |
| --- | --- | --- |
| Full method-paper rewrite | complete locally | Abstract through conclusion, discussion, reproducibility, tables, appendices, and submission docs are synchronized to the current validated evidence. |
| Springer format | structurally complete | `main.tex` uses `llncs`; official Springer files are still required. |
| Bibliography | expanded; final review required | Entries have checked metadata and stable URLs/DOIs where available. |
| Results | validator-backed and split-bounded | TempGlitch, K1, K2, K3, qualitative timelines, and R5-XGame are all mapped to explicit claim limits. |
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
3. Upload the current `paper/sections/`, `paper/appendices/`, `paper/tables/`, and
   `paper/references.bib` contents.
4. Upload publication-ready figure assets only if they are exported separately from validated
   outputs; helper planning files under `paper/figures/` stay local.
5. Keep the anonymous-submission metadata in place for review builds; replace it only for a later
   camera-ready package.

Generated LaTeX build files are gitignored. Every empirical edit must remain synchronized with the
claim registry, source matrix, reviewer audit, submission gate docs, and report 106 paragraph
audit.
