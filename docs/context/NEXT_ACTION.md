# NEXT_ACTION.md

Last updated: 2026-06-24T12:05:00+00:00
Commit: `d475724e49acbd024daed3f2b4dfe9c1ba071c33`

## Current Priority
Stop at roadmap V4 after K1 intake. The K1 learned-baseline Kaggle run has been downloaded,
validated locally, and compared against the existing TempGlitch follow-up evidence. The next local
action is P3 preparation for the GlitchBench benchmark while keeping locked test closed.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P3 local preparation, before Kaggle K2)
1. Freeze the exact public-benchmark protocol, split policy, and claim boundary for GlitchBench.
2. Prepare the local packaging/validator path for K2 so the Kaggle handoff uses the same
   train-normal, validation-only, locked-test-closed discipline as earlier gates.
3. Register the benchmark-facing paper/table slots and keep all K1 learned-baseline claims bounded
   to the validated TempGlitch follow-up support.
4. Stop before any Kaggle K2 launch until the local package, validator, and claim wording are
   ready.

## Success Criteria
- K1 learned-baseline intake remains validator-backed with false locked-test flags.
- The strongest learned baseline stays documented as bounded evidence on the exact TempGlitch
  follow-up support only.
- The GlitchBench local package/validator path is ready for a user-operated Kaggle K2 run.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After This Task
P3 GlitchBench benchmark (Kaggle K2), P4 SIGReg/action ablation (Kaggle K3), P5 temporal
localization (Kaggle K4 optional), P6 demo, P7 full paper rewrite.
Codex does every local task autonomously and stops only at Kaggle gates K2-K4.

## Current Known Blocker
The next roadmap step requires local P3 packaging and validator preparation for a user-operated
Kaggle K2 benchmark run. Official Springer kit / TeX toolchain work still belongs later at P7.
Locked test remains closed.
