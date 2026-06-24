# 107 - Submission Readiness Checklist

Date: 2026-06-24
Status: bounded local package checklist

## Classification Key

1. Ready now
2. Needs local editing only
3. Needs official template/toolchain
4. Needs Kaggle/new compute
5. Should not be attempted for this paper

## Checklist

| Surface | Classification | Current status | Evidence or note |
| --- | --- | --- | --- |
| Section completeness | 1 | Complete from abstract through conclusion, plus discussion, reproducibility, and appendices | `paper/main.tex`, `paper/sections/`, `paper/appendices/` |
| Main TempGlitch table | 1 | Complete and validator-backed | report 101, `paper/tables/r5_bounded_results.tex` |
| Secondary R5-XGame table | 1 | Complete and bounded | report 96, `paper/tables/r5_xgame_results.tex` |
| Limitations and claim-boundary tables | 1 | Complete | `paper/tables/limitations_claim_boundary.tex`, `paper/tables/reviewer_risk.tex` |
| Reviewer-response package | 1 | Complete | `docs/research/107_paper_draft_reviewer_audit.md` |
| Submission-gap package | 1 | Complete | this checklist, `docs/research/108_submission_gap_analysis.md`, `docs/research/109_kaggle_decision_gate.md` |
| Claim registry alignment | 1 | Current bounded claims are registered and mapped | `docs/research/16_claim_registry.md`, `docs/research/70_paper_claim_map.md`, report 106 |
| Reproducibility/provenance section | 1 | Complete | `paper/sections/08b_reproducibility.tex`, appendix B |
| Figure planning | 1 | Complete as a plan only, with no invented data | `paper/figures/PLAN.md` |
| References metadata | 2 | Bibliography exists, but final citation-by-citation review remains | `paper/references.bib` |
| Anonymity package | 2 | Anonymous-submission metadata is now in `paper/main.tex`, but a final anonymization checklist must still be run | `paper/main.tex`, `docs/research/111_anonymization_checklist.md` |
| Similarity screening record | 2 | Not yet documented | must be recorded before submission |
| Final wording polish | 2 | Bounded wording is in place, but venue-level prose compression may still be needed after compile | paper sections and report 106 |
| Official Springer class files | 3 | Missing locally | `llncs.cls`, `splncs04.bst` absent from repo |
| Local build tools | 3 | Missing locally | `pdflatex`, `bibtex`, `biber`, `latexmk` not installed |
| PDF compile | 3 | Blocked by missing class/tools | no truthful local build possible |
| Page-fit review | 3 | Blocked until official-kit compile exists | page count unknown |
| Warning audit | 3 | Blocked until official-kit compile exists | overfull boxes and missing-reference warnings unknown |
| Strong learned baseline on exact TempGlitch support | 4 | Not available | optional strengthening only |
| New LeWM seeds beyond recorded artifacts | 4 | Not run | optional strengthening only |
| Controlled SIGReg/action ablations | 4 | Not run | optional strengthening only |
| Locked-test result | 5 | Closed by policy | out of scope without separate direct user command |
| Cross-game generalization claim | 5 | Unsupported by current evidence | should not be attempted for this paper |
| Temporal localization claim | 5 | Unsupported by current labels | should not be attempted for this paper |
| WOB binary-benchmark claim | 5 | Unsupported by `R5-WOB` | should not be attempted for this paper |

## Final Blocker List

- Official Springer class files are missing locally.
- Local TeX executables are missing locally.
- Page count, overfull boxes, and citation/build warnings cannot be checked until the official kit
  is available.
- Similarity screening and final anonymization still need a submission-stage pass.
