# Paper Revision V6 Design

Date: 2026-06-29

## Goal

Revise the LeWM-Glitch manuscript into a submission-ready EAI FISAT 2026 paper that is strong enough for a Q3-style venue and approaches Q2 expectations in rigor, while preserving the repository's evidence-safe claim boundaries.

The revision must improve scientific framing, result interpretation, LaTeX readiness, and submission hygiene without adding unsupported claims. K-A expanded TempGlitch remains pending until a downloaded Kaggle output bundle passes local validation.

## Inputs

- User-provided planning documents:
  - `C:\Users\ADMIN\Downloads\CODEX_MASTER_PROMPT_LeWM_v6.md`
  - `C:\Users\ADMIN\Downloads\SENIOR_SPEC_LeWM_Glitch_v6.md`
  - `C:\Users\ADMIN\Downloads\<Vietnamese Topic-A assessment while K-A runs>.md`
- Current repo state:
  - Branch: `main`
  - Current checked commit at design time: `c638076`
  - Paper root: `paper/`
  - Claim registry: `docs/research/16_claim_registry.md`
  - K-B final intake: `docs/research/128_kb_r5_xgame_final_intake_2026_06_29.md`
- Relevant skills:
  - `superpowers:brainstorming`
  - `superpowers:writing-plans`
  - `academic-paper`
  - `academic-pipeline`
  - LaTeX plugin: `latex-doctor`, `latex-compile`, `texlive-runtime-installer`

## Current Evidence Boundary

Allowed paper-facing evidence:

- TempGlitch follow-up: frozen pair-disjoint non-locked support with 2 calibration-normal, 12 normal-negative, and 22 buggy-positive episodes. Best LeWM row: AUROC `0.7159`, AUPRC `0.8026`; best learned/simple baseline AUROC `0.6136`; no significant superiority claim.
- R5-XGame / K-B: final-intake-validated non-locked support with 12 normal-negative and 60 buggy-positive episodes. Best LeWM row: AUROC `0.909722`, AUPRC `0.981384`; best baseline AUROC `0.768056`; confidence intervals overlap per final intake, so no significance or broad superiority claim.
- K2 GlitchBench: bounded image-level honest negative; LeWM reaches AUROC `0.5`, while several non-LeWM baselines reach AUROC `1.0` on the exact bounded split.
- K3 ablation: bounded negative mechanistic readout; no SIGReg or action-conditioning benefit.
- Qualitative timelines: allowed only as diagnostic visualizations with `temporal_metrics_claimed=false`; no temporal localization metric.

Forbidden paper-facing claims:

- State-of-the-art, broad superiority, deployment readiness, real-time capability.
- Locked-test results or held-out test-set performance.
- Cross-game generalization from TempGlitch plus R5-XGame.
- Temporal localization, onset/offset/duration, temporal IoU, temporal AP.
- SIGReg benefit or action-conditioning benefit.
- K-A expanded metrics before local validation of the downloaded output bundle.

## Design Approach

Use a paper-first, evidence-safe aggressive revision. The paper should be assertive about what is validated, but conservative about what is not. The strongest narrative is:

1. Gameplay glitches are temporal violations of learned normal dynamics.
2. JEPA-style latent prediction error is a natural label-free surprise signal for that setting.
3. R5-XGame provides the strongest bounded positive result and should be a co-primary headline.
4. TempGlitch remains the core temporal public benchmark result, with K-A pending as a support-tightening upgrade.
5. K2 and K3 are not embarrassing failures; they are honest negative findings that sharpen the method scope.
6. Qualitative E(t) timelines are valuable for interpretability, but must stay explicitly non-localization.

## Revision Workstreams

### Workstream 1: Claim-Safety And Result Text

Fix claim-risk text before stylistic polishing.

- Remove or resolve the K-A and K-B pending markers from paper-facing TeX.
- Replace unsupported significance wording with bounded wording.
- Correct the R5-XGame CI sentence: final intake says the best LeWM and best baseline confidence intervals overlap, so the paper must not say they do not overlap.
- Keep TempGlitch and R5-XGame as separate frozen result families rather than a cross-game generalization story.
- Audit every `.tex` file under `paper/`, not just files included by `main.tex`, because accidental Overleaf uploads may include stale internal tables.

### Workstream 2: Structure, Length, And LLNCS Readiness

Make the manuscript fit an LNCS/FISAT submission shape.

- Keep `\documentclass[runningheads]{llncs}`.
- Add `\usepackage{microtype}` if compatible with the toolchain.
- Keep abstract at or below 250 words; current count is 240 at design time.
- If compiled page count exceeds the target, remove internal reviewer-facing scaffolding first:
  - Appendix E forbidden claims.
  - Claim map table.
  - Reviewer-risk table.
  - Raw artifact hash table if needed.
- Treat official Overleaf/Springer author-kit build as the final page-count authority if local LaTeX differs.

### Workstream 3: Narrative Upgrade

Improve the paper's research contribution without changing evidence.

- Rewrite the Introduction around the core causal intuition: game glitches are violations of learned latent dynamics.
- Explain why JEPA is more appropriate than pixel reconstruction for temporal dynamics, while avoiding a causal proof claim.
- Reframe GlitchBench K2 as an honest negative image-level mismatch result rather than a generic method failure.
- Reframe K3 as a bounded negative mechanistic readout, not as broad evidence against SIGReg or actions.
- Add a Discussion subsection explaining why the positive TempGlitch/R5-XGame results and negative K2 result jointly support a temporal-scope interpretation.

### Workstream 4: Related Work And Citation Integrity

Use primary sources only for external comparisons.

- Add or verify concurrent-work coverage for RESP and T-SAR-JEPA if their arXiv records are accessible and match the cited claims.
- Verify TempGlitch VLM claims from the primary TempGlitch source before adding any exact GPT-4V or Gemini numbers.
- If exact VLM AUROC values cannot be verified, write only that TempGlitch reports near-chance VLM behavior and cite the paper.
- Ensure every in-text citation has a matching `.bib` entry and every `.bib` entry used in the paper has a real source.

### Workstream 5: Figures And Visual Evidence

Turn the qualitative timeline lane into a reviewer-friendly figure.

- Reuse `scripts/generate_qualitative_surprise_timelines.py` as the first option.
- If the current script only emits diagnostic PNGs, extend or wrap it in the implementation phase to produce a single-column publication figure in PDF and PNG.
- Figure caption must state: qualitative only, no temporal localization metric, no ground-truth spans.
- Include exactly one representative timeline figure unless page budget allows more.

### Workstream 6: LaTeX, Integrity, And Submission Hygiene

Use the LaTeX plugin and academic-pipeline integrity expectations.

- Run LaTeX doctor to determine whether local compilation is possible.
- Compile locally via the LaTeX plugin if a usable runtime exists.
- If local compile is unavailable or incomplete, prepare the paper for Overleaf and record that official LLNCS build remains external.
- Run anonymization grep for institution, team, GitHub, and acknowledgments.
- Run claim and forbidden-word grep.
- Run citation and pending-marker audit.
- Keep raw outputs, datasets, checkpoints, Lance directories, and credentials out of Git.

## Acceptance Criteria

The revision is complete only when all applicable checks pass:

- `paper/main.tex` compiles locally or has a documented external-LLNCS build handoff.
- Abstract is no more than 250 words.
- No paper-facing K-A, K-B, or unsupported pending markers remain.
- No unverified VLM AUROC values appear.
- No text claims non-overlapping CI for R5-XGame unless supported by updated validated evidence.
- No locked-test, cross-game-generalization, SOTA, real-time, deployment, SIGReg-benefit, action-benefit, or temporal-localization claim appears.
- Any timeline figure is explicitly qualitative-only.
- K-A expanded results are absent unless a downloaded K-A bundle validates locally.
- References resolve and all new citations are from primary sources.
- Anonymization grep finds no institution/team/GitHub identity leaks.
- Repository verification commands pass before commit, or skipped checks are documented.

## Non-Goals

- Do not run locked test.
- Do not introduce K-C/WOB binary or synthetic GlitchBench claims in this revision unless those experiments are separately run and validated.
- Do not rewrite the full experimental pipeline.
- Do not fabricate or infer VLM numbers.
- Do not include raw artifact hashes if page budget is tight.

## Proposed Implementation Plan Shape

After user approval of this design spec, write a task-by-task implementation plan using `superpowers:writing-plans`. The plan should decompose the work into small commits:

1. Claim-safety text fixes.
2. Introduction and discussion narrative rewrite.
3. Related-work and citation update with verified sources only.
4. Results-table caption and VLM-comparison update.
5. Timeline figure integration.
6. Appendix/page-count reduction.
7. LaTeX/anonymization/integrity validation.
8. Context cache and final repository verification.

## Self-Review

- Placeholder scan: no placeholder tokens or unspecified implementation requirements remain in this design.
- Consistency check: the evidence boundary matches the current claim registry and K-B final intake state.
- Scope check: this is a paper revision and validation design, not an experiment launch plan.
- Ambiguity check: K-A is explicitly gated on local validation before any paper use.
