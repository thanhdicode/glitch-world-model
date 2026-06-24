# NEXT_ACTION.md

Last updated: 2026-06-25T00:00:00+00:00
Commit: `ea7c8609e9cead37d90bcd8c97e9d6e72393a173`

## Current Priority
Rerun the repaired Kaggle K2 path, not K3. The repo now has a read-only-safe K2 bundle validator,
a scientific full K2 runner with real LeWM scoring, and a normalized LeWM seed-artifact dataset
builder. A first full K2 Kaggle attempt then failed at learned-baseline setup because
`device=...` was passed into learned-baseline config constructors; that constructor bug is now
patched locally. The next external action is to rerun the full K2 job on the new pinned commit with
the LeWM seed artifact dataset attached.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (User-Operated Kaggle K2)
1. Upload `lewm-k2-glitchbench-inputs.zip` as Kaggle dataset `lewm-k2-glitchbench-inputs`.
2. Upload `lewm-k2-lewm-seed-artifacts.zip` as Kaggle dataset `lewm-k2-lewm-seed-artifacts`.
3. Run the direct `/kaggle/input` dry-run command from
   `docs/research/120_kaggle_k2_glitchbench_runbook.md`.
4. If the dry-run returns `dry_run_ready`, run the scientific full K2 command with
   `--lewm-seed-artifact-root /kaggle/input/lewm-k2-lewm-seed-artifacts` on the latest pinned
   commit for the constructor fix.
5. Download the full `glitchbench_k2` working directory and validate the resulting artifact locally
   before any K2 metric enters the claim registry.

## Success Criteria
- Direct read-only Kaggle input validation passes without writing inside the mounted package root.
- The scientific full K2 run finishes with status `k2_complete_lewm_and_baselines`.
- The output bundle contains per-seed/per-aggregation LeWM score CSVs, metrics, and metadata.
- Any downloaded K2 artifact validates locally before the paper claim surface expands.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After This Task
P3 Kaggle K2 benchmark intake/validation, P4 controlled SIGReg/action ablation artifact run
(Kaggle K3), P5 temporal localization or explicit future-work scoping, P6 demo, P7 full paper
rewrite.

## Current Known Blocker
K2 remains blocked on the user-operated Kaggle rerun and post-run local intake. GlitchBench
remains image-level and synthetic-normal, so even after K2 it cannot support temporal-localization
claims. K3 remains blocked until K2 artifact intake is complete. Locked test remains closed.
