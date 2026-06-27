# 110 - Reference And Bibliography Audit

Date: 2026-06-27
Status: local paper-source bibliography audit after P7 rewrite

## Active Bibliography File

The paper source uses:

- `paper/references.bib`

The paper does not use `docs/research/references.bib` for submission builds. That research copy
remains internal support material only.

## Citation-Key Audit

Audit method:

- scanned all `paper/**/*.tex` files for `\cite{...}` keys;
- compared the cited keys against entry keys in `paper/references.bib`.

Results after the P7 rewrite:

- cited keys: `dreamerv3`, `glitchbench`, `guo2017calibration`, `hendrycks2017baseline`,
  `ijepa`, `kapoor2023leakage`, `kaufman2011leakage`, `lewm`, `park2020mnad`,
  `pineau2021reproducibility`, `planet`, `politowski2022automatedtesting`,
  `sultani2018ucfcrime`, `tempglitch`, `vjepa`, `worldmodels`
- missing cite keys: none
- unused `.bib` entries: none

## Placeholder Audit

No obviously placeholder bibliography entries were found in `paper/references.bib`:

- every entry has a concrete title;
- every entry has author metadata;
- every entry has a year;
- every cited entry has at least one retrieval surface such as DOI or URL.

## Remaining Bibliography Risks

- The current workspace cannot run an official BibTeX-based paper build, so this audit does not
  replace a real compile-time warning check.
- The P7 rewrite keeps the bibliography key set unchanged, but citation and bibliography warnings
  still need to be recorded from the first official LLNCS compile.
- Several entries are arXiv preprints, which is acceptable for local drafting but should still be
  rechecked against final venue preferences during the official-kit compile pass.
- Final bibliography style compliance still depends on `splncs04.bst` during an actual build.

## Submission Guidance

- Upload `paper/references.bib` with the paper source package.
- Exclude `docs/research/references.bib` from the submission upload.
- After the first official-kit build, record undefined citations, style warnings, and any venue-
  specific bibliography adjustments in the build log.
