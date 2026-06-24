# NEXT_ACTION.md

Last updated: 2026-06-24T17:20:00+00:00
Commit: `731fef69f76d6025fe7e14a2d9498c49746b8a62`

## Current Priority
Stop at roadmap V4 after local P3 preparation. The GlitchBench subset package, protocol audit,
freeze, validator, and K2 runbook now exist locally, and controlled SIGReg/action ablation tooling
is scaffolded locally without any K3 evidence claim. The next external action is the user-operated
Kaggle K2 run.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (User-Operated Kaggle K2)
1. Upload `lewm-k2-glitchbench-inputs.zip` as a Kaggle Dataset named
   `lewm-k2-glitchbench-inputs`.
2. Attach the required LeWM seed artifact dataset for K2 if LeWM scoring is desired in the same
   run.
3. Run `scripts/run_kaggle_glitchbench_benchmark.py` on Kaggle using the documented K2 command.
4. Download the working directory and validate the resulting benchmark artifact locally before any
   GlitchBench metric claim is registered.

## Success Criteria
- The packaged K2 input bundle remains validator-backed with false locked-test flags.
- The K2 run produces method outputs for the exact frozen image-level GlitchBench subset support.
- Any downloaded K2 artifact validates locally before the claim registry expands.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After This Task
P3 GlitchBench benchmark (Kaggle K2), P4 controlled SIGReg/action ablation artifact run
(Kaggle K3), P5 temporal localization or explicit future-work scoping, P6 demo, P7 full paper
rewrite.
Codex continues local support work autonomously and stops only at Kaggle gates K2-K4.

## Current Known Blocker
K2 is now blocked only on the user-operated Kaggle launch plus any required LeWM seed-artifact
attachment. GlitchBench remains image-level and synthetic-normal, so even after K2 it cannot
support temporal-localization claims. Locked test remains closed.
