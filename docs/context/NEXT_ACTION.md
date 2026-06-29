# NEXT_ACTION.md

Last updated: 2026-06-29T03:58:00+00:00
Commit: `0289c5bfcc825502f1ca76564de0f81a3df4b60d`

## Current Priority
Run the evidence-safe paper revision pass from `CODEX_MASTER_PROMPT_LeWM_v6.md` after the
completed local P7 rewrite and final-intake-validated K-B / R5-XGame output.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Paper Revision V6)
1. Apply only evidence-safe edits to `paper/main.tex` and `paper/sections/`.
2. Use K-B / R5-XGame numbers only within the frozen non-locked 12-negative / 60-positive split.
3. Keep K-A expanded results out of the paper until a validated output bundle exists.
4. Compile/check LaTeX when the local or external toolchain is available, then proceed to the
   official Springer/Overleaf LLNCS build handoff.

## Success Criteria
- The claim registry, paper text, and context cache remain consistent with the validated evidence.
- Paper-facing numbers match `docs/research/16_claim_registry.md` and
  `docs/research/128_kb_r5_xgame_final_intake_2026_06_29.md`.
- No temporal-localization metric, onset/offset claim, or locked-test action is introduced.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After This Gate
Paper revision v6, official build review, venue checklist completion, user-operated submission,
then any later camera-ready or reviewer-response work.

## Current Known Blocker
K-A expanded TempGlitch remains pending. Do not include expanded K-A results until its Kaggle
output is downloaded and locally validated. The official Springer class/toolchain is still external,
so the first real LLNCS PDF build, page-fit review, and PDF metadata validation must happen in
Overleaf or an equivalent author-kit setup.
