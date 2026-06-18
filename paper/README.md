# Paper Scaffold

The paper scaffold is deliberately cautious and currently centers the verified non-locked
TempGlitch validation-only evidence plus reproducibility appendices. It does not claim broad
superiority, state of the art, locked-test results, WOB training/evaluation results, SIGReg
benefit, real-time operation, or temporal localization.

## Submission Readiness Status

| Surface | Status | Notes |
| --- | --- | --- |
| Scaffold | complete | Section, appendix, table, and control-document structure exists. |
| Springer format | structurally complete | `main.tex` uses `llncs`; official Springer files are still required. |
| Bibliography | expanded; final review required | Entries have checked metadata and stable URLs/DOIs where available. |
| Results | bounded only | Current table is limited to the non-locked TempGlitch validation-only R5 family. |
| Locked test | closed | Not materialized and not scored. |
| WOB-P1 seed42 | pending | Separate empirical gate; not a paper result yet. |
| PDF compile | blocked locally | Local TeX tools/official class are not available in the repo environment. |
| Page count | pending | Requires Overleaf or official Springer Author Kit compile. |
| Similarity screening | pending | Must run before submission. |

## Springer/LNICST note

`paper/main.tex` now targets the official Springer `llncs` class and `splncs04` bibliography
style. The repository does not vendor `llncs.cls` or other unofficial templates. To compile in
Overleaf or a local LaTeX install, provide the official Springer conference template files.

Recommended Overleaf setup:

1. Start from the official Springer `llncs` template.
2. Replace the template `main.tex` with [paper/main.tex](<C:/Users/ADMIN/Desktop/glitch-world-model/paper/main.tex>).
3. Upload the `paper/sections/`, `paper/appendices/`, `paper/tables/`, `paper/figures/`, and
   `paper/references.bib` contents.
4. Keep author/institute metadata as placeholders until the submission package is finalized.

Generated LaTeX build files are gitignored. Update the claim map and source matrix before editing
bounded results prose.
