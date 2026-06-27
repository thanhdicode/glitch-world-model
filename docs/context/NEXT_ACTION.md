# NEXT_ACTION.md

Last updated: 2026-06-27T12:31:39+00:00
Commit: `3ce684c8197ef57f4856d663ae14e2f46cb53f47`

## Current Priority
Advance to roadmap V4 Phase P7. The P6 demo lane is now implemented, so the next work is the full
paper rewrite and submission package preparation under the existing bounded claim surface.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P7, local)
1. Regenerate paper tables from the validated P2-P6 artifacts.
2. Rewrite the paper sections so every empirical paragraph stays mapped to
   `docs/research/16_claim_registry.md`.
3. Keep the P5/P6 boundary explicit: qualitative timelines are allowed, temporal-localization
   metrics are not.
4. Preserve the closed locked-test state and keep all output artifacts outside Git.

## Success Criteria
- Demo outputs are reproducible from already validated non-locked artifacts.
- The claim registry, paper text, and context cache remain consistent with the bounded evidence.
- No temporal-localization metric, onset/offset claim, or locked-test action is introduced.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After P7
Bounded submission packaging decisions, venue checklist completion, and user-operated submission.

## Current Known Blocker
No local blocker remains for P6. The current limitation is scientific rather than operational:
temporal-localization claims remain unavailable until a validated artifact supplies real span
annotations, and the paper rewrite must stay inside the current bounded evidence. Locked test
remains closed.
