# NEXT_ACTION.md

Last updated: 2026-06-26T09:46:56+00:00
Commit: `cff8e5875ddcced84c45e4b626d5cac1050f5a75`

## Current Priority
Advance to roadmap V4 Phase P6. Phase P5 is closed on the documented future-work path because the
current validated artifacts do not expose true temporal span labels. Authority roadmap:
`docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P6, local)
1. Build the reproducible demo lane on top of the existing bounded non-locked evidence.
2. Keep all claims synchronized with `docs/research/16_claim_registry.md`.
3. Preserve the P5 boundary: qualitative timelines are allowed, temporal-localization metrics are
   not.
4. Keep Kaggle K4 optional and unused unless a later task truly needs fresh full window rescoring.

## Success Criteria
- Demo outputs are reproducible from already validated non-locked artifacts.
- The claim registry, paper text, and context cache remain consistent with the bounded evidence.
- No temporal-localization metric, onset/offset claim, or locked-test action is introduced.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After P6
P7 full paper rewrite, then any later bounded submission packaging decisions.

## Current Known Blocker
No local blocker remains for P5. The current limitation is scientific rather than operational:
temporal-localization claims remain unavailable until a validated artifact supplies real span
annotations. Locked test remains closed.
