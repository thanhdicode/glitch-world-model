# NEXT_ACTION.md

Last updated: 2026-07-01T14:32:51+00:00
Commit: `b1cb9c0d30fbb509cbd028cb9e4a36546198c8ff`

## Current Priority
Continue the evidence-safe paper revision and K-C intake-preparation lane after integrating the
locally intake-reviewed K-A expanded TempGlitch output into the manuscript as auxiliary evidence.
Use `CODEX_MASTER_PROMPT_LeWM_v6.md` as the paper-pass prompt.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Paper Revision V6)
1. Apply only evidence-safe edits to `paper/main.tex` and `paper/sections/`.
2. Use K-B / R5-XGame numbers only within the frozen non-locked 12-negative / 60-positive split.
3. Use K-A expanded only as bounded auxiliary support-expansion evidence, not as headline
   superiority or statistical-significance evidence.
4. Keep K-C WOB binary pending until its downloaded tarball and SHA sidecar pass local intake.
5. Compile/check LaTeX when the local or external toolchain is available, then proceed to the
   official Springer/Overleaf LLNCS build handoff.

## Success Criteria
- The claim registry, paper text, and context cache remain consistent with the validated evidence.
- Paper-facing numbers match `docs/research/16_claim_registry.md` and
  `docs/research/128_kb_r5_xgame_final_intake_2026_06_29.md`.
- Any K-A expanded wording matches `docs/research/129_ka_tempglitch_expanded_intake_2026_06_30.md`.
- No temporal-localization metric, onset/offset claim, or locked-test action is introduced.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After This Gate
Paper revision v6, official build review, venue checklist completion, user-operated submission,
then any later camera-ready or reviewer-response work.

## Current Known Blocker
K-A expanded TempGlitch is now locally intake-reviewed, but it has moderate AUROC, wide intervals,
high FPR@95TPR, and no significance artifact, so it should remain auxiliary. K-C WOB binary has
launch scaffolding but no validated Kaggle binary output yet. The official Springer
class/toolchain is still external, so the first real LLNCS PDF build, page-fit review, and PDF
metadata validation must happen in Overleaf or an equivalent author-kit setup.
