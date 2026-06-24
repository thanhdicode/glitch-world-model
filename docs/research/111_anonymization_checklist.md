# 111 - Anonymization Checklist

Date: 2026-06-24
Status: local review-package anonymization audit

## Current Paper-Source Status

| Surface | Status | Notes |
| --- | --- | --- |
| `paper/main.tex` author metadata | ready for anonymized submission | uses `Anonymous Submission` |
| `paper/main.tex` institute metadata | ready for anonymized submission | uses `Institution withheld for double-blind review` |
| acknowledgements section | absent | no acknowledgement text to strip |
| author emails in paper source | absent | none found in `paper/` LaTeX source |
| repository URLs in paper source | absent | none found in the manuscript text |
| self-citation wording | currently safe | no "our prior work" or identity-revealing wording found in the paper text |
| PDF metadata | pending | requires first real official-kit build |

## Internal Files That Must Not Be Uploaded

These files are useful locally but are not part of the anonymized paper submission package:

- `paper/README.md`
- `paper/TODO.md`
- `paper/figures/PLAN.md`
- all `docs/research/*.md` support files
- any file containing local absolute paths such as `C:/Users/ADMIN/...`

## Path And Identity Exposure Audit

Findings:

- the manuscript source itself does not contain local machine paths;
- internal helper docs do contain absolute local paths and repo-management notes;
- those helper files must remain outside the submission upload.

## Manual Checks Still Required

- confirm the final PDF metadata does not embed author or workstation identity;
- confirm the Springer/Overleaf project title and settings are anonymized;
- confirm no generated figure asset or caption introduces identity-revealing file names;
- confirm any camera-ready metadata replacement happens only after the anonymized submission phase.

## Submission Rule

Use the anonymous-ready `paper/main.tex` metadata for the review package. Do not swap in real
author, affiliation, or email metadata during the bounded submission finalization pass.
