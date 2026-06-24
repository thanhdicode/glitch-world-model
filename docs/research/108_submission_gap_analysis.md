# 108 - Submission Gap Analysis

Date: 2026-06-24
Status: local bounded package audit

## Build And Template Audit

Local tool check:

| Tool or file | Status |
| --- | --- |
| `latexmk` | missing |
| `pdflatex` | missing |
| `bibtex` | missing |
| `biber` | missing |
| `llncs.cls` | missing from repo |
| `splncs04.bst` | missing from repo |

Current `paper/main.tex` expects:

- `\documentclass[runningheads]{llncs}`
- `\bibliographystyle{splncs04}`

Result: a truthful local PDF build is not possible in the current workspace.

## What Is Complete Locally

- Full bounded paper draft with main text, tables, appendices, discussion, reproducibility, and
  limitations.
- Paragraph-level claim audit and paper claim map.
- Anonymous-submission-ready paper metadata.
- Reviewer-risk package and submission-readiness checklist.
- Figure plan with placement and evidence sources.
- Kaggle gate decision recorded as Path A.
- Repository validation and artifact-hygiene workflow support.

## What Still Blocks Submission Finalization

| Gap | Class | Why blocked | Next step |
| --- | --- | --- | --- |
| Official Springer compile | 3 | Missing `llncs.cls` and `splncs04.bst` | obtain official Springer Author Kit |
| Local TeX build | 3 | Missing `pdflatex`, `bibtex`, `biber`, `latexmk` | install or use Overleaf with official kit |
| Page count | 3 | depends on truthful compile | record after first official-kit PDF |
| Overfull boxes and warning audit | 3 | depends on truthful compile | inspect first official-kit build log |
| Final bibliography polish | 2 | source list exists but final venue pass remains | review after compile |
| Final anonymization check | 2 | anonymous-submission metadata is in place, but the surrounding checklist is still manual | run submission pass and PDF metadata check after first official-kit build |
| Similarity screening log | 2 | not yet recorded | run before upload |

## What Does Not Currently Block A Bounded Paper

- A new Kaggle run.
- Retraining.
- A new dataset download.
- Locked-test access.
- New figures derived from untracked or freshly generated evidence.

## Path Decision

Path A is justified:

`No Kaggle needed yet; finalize bounded submission locally after official-kit compile/anonymization/similarity checks.`

The paper already has an honest bounded contribution surface. The remaining blockers are chiefly
formatting, build, and submission-package tasks, not evidence-rescue tasks.
