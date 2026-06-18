# Overleaf Springer Checklist

Date: 2026-06-18

Status: active packaging checklist

## Template Control

- Use the official Springer `llncs` conference template.
- `paper/main.tex` uses `\documentclass[runningheads]{llncs}`.
- `paper/main.tex` uses `\bibliographystyle{splncs04}`.
- Do not download or vendor unofficial `llncs` copies into the repository.
- `paper/llncs.cls` is intentionally absent.
- Ensure `llncs.cls` and `splncs04.bst` come from the official Springer Author Kit or Overleaf
  template.
- FISAT 2026 public submission guidance says regular papers must comply with Springer format and
  be 12--20 pages excluding appendices, references, and acknowledgements. Recheck the official
  Author Kit before final export because venue pages can change. Source checked:
  <https://daihoc.fpt.edu.vn/hcm/hoi-nghi-fisat/>.

## Local Compile Status

- Local compile is not yet validated.
- PATH tools checked: `latexmk`, `pdflatex`, `xelatex`, and `lualatex` are unavailable.
- The LaTeX plugin provides bundled Tectonic 0.16.9. The plugin compile runner skipped Tectonic
  because `paper/main.tex` uses bibliography tooling and then skipped TeX Live because no TeX Live
  or MacTeX installation was detected.
- The LaTeX plugin doctor command timed out in this environment and the repository intentionally
  does not include `llncs.cls`.
- Current blocker classification: compile is blocked by local LaTeX/template availability, not by
  a known source-level error found during static scaffold review.

## Overleaf Upload Checklist

- Upload `paper/main.tex`.
- Upload `paper/references.bib`.
- Upload `paper/sections/`.
- Upload `paper/appendices/`.
- Upload `paper/tables/`.
- Upload approved `paper/figures/` assets only after figure review.
- Use the official Springer `llncs.cls`.
- Use the official Springer `splncs04.bst` or the bibliography style shipped with the Author Kit.
- Compile with BibTeX.
- Check unresolved references and citations.
- Check page count against the 12--20 regular-paper range.
- Check figures, tables, captions, and alt-text/accessibility requirements.

## Camera-Ready Package Checklist

- Final PDF.
- LaTeX source archive.
- Final figure assets.
- Final table sources.
- Final bibliography.
- Required author, affiliation, ORCID, and proceedings metadata.
- Copyright/rights forms if requested by the venue.
- No private artifacts, raw data, checkpoints, Lance datasets, credentials, `.env`, `kaggle.json`,
  or artifact bundles.

## Safety Checks

- No WOB training/evaluation results are described as paper results.
- No locked-test claim appears in text, tables, captions, or appendix notes.
- No SOTA, broad superiority, SIGReg, real-time, or temporal-localization claim is introduced.
- Placeholder abstract remains provisional until the final claim audit.
- Placeholder author and institute metadata are replaced only when the submission package is ready.

## Manual Review Before Export

- Re-read `docs/research/70_paper_claim_map.md`.
- Re-read `docs/research/71_paper_source_matrix.md`.
- Confirm the bounded results table caption still says `Non-locked TempGlitch validation-only identical-episode family.`
- Record the exact Overleaf compile log and page count in the submission package notes.
