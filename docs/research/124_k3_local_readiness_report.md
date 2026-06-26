# 124 - K3 Local Readiness Report

Date: 2026-06-25
Status: local K3 inputs prepared; dry-run passed; ready for user-operated Kaggle K3

## Authority Confirmation

- Current roadmap authority: [MASTER_ROADMAP_LeWM_Glitch_v4.md](../roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md)
- K1 / Phase P2: complete and artifact-backed
- K2 / Phase P3: complete and artifact-backed
- K3 / Phase P4: local package-ready, scientific artifact pending user-operated Kaggle
- Locked test: closed

The current context cache places the repo after validated K2 intake and at the K3 user-operated
Kaggle gate. No validated K3 scientific artifact exists yet.

## Selected K3 Support Source

The current K3 lane is not TempGlitch follow-up and not K2 GlitchBench.

K3 is tied to the current dry-run plan in:

- `outputs/r6_sigreg_ablation_plan/r6_ablation_plan.json`

That plan points to:

- `outputs/r5_xgame/_r5_xgame_train_normal.lance`
- `outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance`

This makes `R5-XGame train_normal + calibration/eval_normal Lance` the operative K3 input source
of truth for the current repo state.

## Current Input Status

Local K3 preparation now has a deterministic entry point:

- `scripts/prepare_k3_ablation_inputs.py`

Latest local result:

- status: `prepared`
- prepared manifest: `outputs/k3_ablation_inputs/k3_input_manifest.json`
- prepared report: `outputs/k3_ablation_inputs/K3_INPUTS_REPORT.md`

The prepared K3 input paths are:

- `outputs/r5_xgame/_r5_xgame_train_normal.lance`
- `outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance`
- auxiliary provenance path:
  `outputs/r5_xgame/_r5_xgame_eval_buggy.lance`

Dataset hashes:

- train: `34ef70fd3e7cb288646b8e5e1fb4f8ae60e9308cddcd2401c8d77c717c076efc`
- validation: `ecb4c9ef1349b8e1896b783a7ae7b3f6761b2d445370ff814e2cfc179ebbfa19`
- auxiliary buggy eval:
  `496a81078b3aba2e7ed9253805dc7ab759ef363e431d1dfbe0502402f9c539bb`

## Source Import

The successful local source was:

- `C:\Users\ADMIN\Downloads\results\r5_xgame`

This source contains materialized non-locked R5-XGame Lance artifacts plus:

- `stage_preflight.json`
- `stage_materialize.json`
- `r5_xgame_leakage_audit.json`

Those provenance records report 36 train-normal, 12 calibration-normal, 12 normal-negative, and
60 buggy-positive rows, with `locked_test_materialized=false`, `locked_test_scored=false`, and
`validation_buggy_used_for_fit_select=false`.

## Dry-Run Status

The local K3 dry-run passed:

- output root: `outputs/r6_sigreg_ablation_dryrun`
- status: `dry_run_ready`
- variants: `12`
- controlled pairs: `12`
- seeds: `[42, 43, 44]`
- locked test materialized: `false`
- locked test scored: `false`

## TempGlitch Support Mismatch Note

The repo still contains a separate TempGlitch documentation mismatch that is relevant for paper
maintenance but is not the K3 source-of-truth lane:

- current `src/glitch_detection/tempglitch_followup.py` and
  `scripts/validate_tempglitch_followup.py` expect the newer `4 calibration / 10 normal-negative /
  22 buggy-positive` support
- some docs/context/paper surfaces still mention the older `2 / 12 / 22` support

This mismatch does not change the K3 lane decision above. K3 remains bound to the current
R5-XGame input plan.

## Readiness Verdict

Local K3 prep is now input-complete and package-ready:

- package surface: prepared
- intake surface: prepared
- prepared input manifest: prepared
- dry-run matrix: passed
- user-operated Kaggle handoff: ready

## Allowed Claims Now

- The repo provides a deterministic local K3 preparation path.
- The current K3 lane is tied to the frozen R5-XGame train/validation-normal inputs.
- The local K3 dry-run constructs the intended 12-variant controlled matrix.
- No validated K3 scientific artifact exists yet.
- Locked test remains closed.

## Forbidden Claims Now

- Any SIGReg benefit claim
- Any action-conditioning benefit claim
- Any K3 performance claim
- Any locked-test statement
- Any temporal-localization, SOTA, broad superiority, or cross-game generalization claim
