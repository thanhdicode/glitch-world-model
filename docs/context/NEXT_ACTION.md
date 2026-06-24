# NEXT_ACTION.md

Last updated: 2026-06-24T06:40:56+00:00
Commit: `816fd867bda0f7e82f8fbbc5604794cbbb35236d`

## Current Priority
Perform official-kit compile/anonymization/similarity pass, then finalize bounded submission
package.

## Next Gate
1. Compile with the official Springer kit when available and record page fit, missing references,
   and warnings.
2. Complete anonymization, similarity screening, bibliography review, and PDF metadata review.
3. Replace figure plans only with provenance-recorded approved figures.
4. Keep any stronger baseline or ablation compute as a separate user-approved decision.

## Success Criteria
- Official-kit build status and page fit are known.
- The bounded paper package remains mapped to registered verified claims.
- The local submission package is ready except for external-template or external-tool blockers.
- Locked test remains closed and the repository verification suite stays green.

## Current Known Blocker
The local TeX toolchain and official Springer files are unavailable: `pdflatex`, `bibtex`,
`biber`, `latexmk`, `llncs.cls`, and `splncs04.bst` are all missing. Typeset build and page-fit
review therefore require the official kit. Locked test remains closed.
