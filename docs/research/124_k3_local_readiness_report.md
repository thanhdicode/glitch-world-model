# 124 - K3 Local Readiness Report

Date: 2026-06-25
Status: local K3 preparation blocked by missing R5-XGame raw inputs

## Authority Confirmation

- Current roadmap authority: [MASTER_ROADMAP_LeWM_Glitch_v4.md](../roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md)
- K1 / Phase P2: complete and artifact-backed
- K2 / Phase P3: complete and artifact-backed
- K3 / Phase P4: pending
- Locked test: closed

The current context cache correctly places the repo after validated K2 intake and before user-run
K3. No validated K3 artifact exists yet.

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

- status: `missing_required_inputs`
- prepared manifest: `outputs/k3_ablation_inputs/k3_input_manifest.json`
- prepared report: `outputs/k3_ablation_inputs/K3_INPUTS_REPORT.md`

The expected K3 input paths remain:

- `outputs/r5_xgame/_r5_xgame_train_normal.lance`
- `outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance`
- auxiliary provenance path:
  `outputs/r5_xgame/_r5_xgame_eval_buggy.lance`

Those Lance directories are not currently materialized in this workspace.

## Exact Blocker

The repository does not currently contain the raw/source WOB archives needed to materialize the
frozen R5-XGame lane locally.

The preparation script checked these candidate roots:

- repo root
- `data/`
- `artifacts/`
- `C:\Users\ADMIN\Downloads`

Results:

- repo-local and ignored-local roots do not contain the required `NORMAL-TRAIN/.../*.tar` and
  `TEST/.../*.tar` coverage
- `Downloads` is additionally unsafe as a generic root because it contains old `R5-WOB`
  artifact-style directories, which the R5-XGame runner correctly rejects

The exact per-role missing-file contract is written into:

- `outputs/k3_ablation_inputs/k3_input_manifest.json`

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

Local K3 prep is now deterministic but not yet input-complete:

- package surface: partially prepared
- intake surface: prepared
- exact missing artifact contract: prepared
- user-only Kaggle handoff: not yet possible until the required R5-XGame raw archives are placed
  under a clean root and `scripts/prepare_k3_ablation_inputs.py` is rerun

## Allowed Claims Now

- The repo provides a deterministic local K3 preparation path.
- The current K3 lane is tied to the frozen R5-XGame train/validation-normal inputs.
- No validated K3 scientific artifact exists yet.
- Locked test remains closed.

## Forbidden Claims Now

- Any SIGReg benefit claim
- Any action-conditioning benefit claim
- Any K3 performance claim
- Any locked-test statement
- Any temporal-localization, SOTA, broad superiority, or cross-game generalization claim
