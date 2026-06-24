# 112 - Similarity Screening Plan

Date: 2026-06-24
Status: planning only; no external checker has been run

## Current Status

No similarity checker has been run from this workspace. Similarity screening therefore remains a
required external/manual submission step, not a completed status.

## What Must Be Screened

- the final paper PDF produced from the official Springer/LLNCS build;
- the abstract and conclusion after any last page-fit edits;
- figure captions and appendix wording if they are edited after the main screening pass.

## Self-Overlap Risks To Review

Potential overlap sources inside this repository:

- `docs/research/101_tempglitch_followup_results.md`
- `docs/research/106_first_bounded_paper_claim_audit.md`
- `docs/research/107_paper_draft_reviewer_audit.md`
- `docs/research/108_submission_gap_analysis.md`
- `PLAYBOOK.md`
- `paper/README.md`
- `paper/TODO.md`

These docs are valid drafting support, but prose copied too literally from them into the final PDF
should be manually reviewed for repetitive phrasing.

## AI-Generated Prose Review Checklist

- verify that every empirical sentence still maps to registered claims;
- remove repeated stock phrasing if it appears across adjacent sections;
- confirm paraphrases remain faithful to the evidence and not broader than the source report;
- confirm literature summaries are not over-close to quoted source language;
- confirm transition sentences do not add unverified conclusions.

## Quote And Citation Handling

- avoid long direct quotations unless absolutely necessary;
- prefer paraphrase plus citation for related-work material;
- keep metric sentences tied to repository evidence, not to prose from support memos;
- recheck all bibliography entries after the first official-kit build for citation-style warnings.

## Paraphrase Quality Checklist

- sentence remains factually identical to the source claim;
- wording is narrower, not broader, than the evidence;
- repeated phrases such as "stronger observed same-support separation" are used only where needed;
- no sentence implies SOTA, broad superiority, generalization, localization, or deployment.

## Final Manual Step

Run an external similarity checker on the first official-kit PDF, record the result, and then do a
human read-through of any highlighted overlaps before upload.
