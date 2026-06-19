# 77 — Ambitious Plan A Execution Plan (TempGlitch core + WOB expansion + R6 + FISAT paper)

Status: active execution plan
Date: 2026-06-19
Decision owner: human (project lead)

## 1. Decision

The human has explicitly chosen the **Ambitious controlled-expansion plan ("Plan A")**:

> TempGlitch core + World of Bugs (WOB) expansion + R6 ablations + final FISAT paper.

This is **not** a "paper-only" plan. Experiments are not to be skipped, and the project must not
jump directly to R8 paper finalization. The roadmap stages are executed in order; the project is
not to be re-split into micro-phases unless a hard blocker appears.

This document is the controlling execution narrative for that decision. It is consistent with
`docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md` and the claim discipline in
`docs/research/16_claim_registry.md`.

## 2. Verified current state (confirmed from repo, 2026-06-19)

| Stage | Status | Evidence |
|---|---|---|
| R0 protocol freeze | complete | Roadmap v3, frozen protocols |
| R1 / R2 schedule freeze | complete | 500-update profile (C-060); main schedule frozen |
| R3 TempGlitch seed42 | complete (artifact) | C-061 (first attempt failed on P100), recovered artifact root |
| R4 TempGlitch seeds43/44 | complete | C-062: local SHA256-verified, per-seed validators pass |
| R5 TempGlitch identical-episode eval | complete (non-locked) | C-064, C-065; `outputs/r5_tempglitch_identical_episode/` frozen |
| WOB-P0 Kaggle-native audit | PASSED | C-070; bundle SHA256 `e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9` |
| WOB-P1 seed42 training | VALIDATED (artifact only) | C-071; bundle SHA256 `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03` |
| WOB-P1 seed43 training | VALIDATED (artifact only) | C-074; bundle SHA256 `df027039b13e987a64d65b7668bec9e2cb998ba54cefc2cedf061acf2e5a6e88` |
| WOB-P1 seed44 training | VALIDATED (artifact only) | C-075; bundle SHA256 `c5b3178cdb75a0c1f9bcca78eba8beaaf21ffa703917a3f42c476563849fd041` |
| WOB evaluation (R5-WOB) | NOT STARTED | `WOB_EVALUATION_STATUS=NOT_STARTED` |
| R5-XGAME cross-game comparison | NOT STARTED | depends on R5-WOB |
| R6 ablations + failure analysis | NOT STARTED | — |
| R7 validation decision / locked go-no-go | NOT STARTED | depends on R5-WOB + R6 |
| R8 FISAT paper | scaffold only, claims gated | `paper/` LNICST scaffold; bounded R5 results only |
| Locked test | CLOSED / not materialized / not scored | all leakage flags false across artifacts |

Local `WOB-P0` remains `BLOCKED_MISSING_INPUTS` (incomplete attached root); the Kaggle-native
`WOB-P0` bundle is the verified WOB entry checkpoint.

## 3. What "next" actually is

The next *practical experimental stage* is to **complete the WOB expansion**, not to finalize the
paper. The seed42 non-locked WOB evaluation-readiness gate is now frozen locally, and all three
planned WOB-P1 training artifacts are now verified. The next empirical step is the frozen
non-locked `R5-WOB` evaluation path, which remains closed until a separate explicit human command
authorizes evaluation.

R6 ablations remain **mandatory**. They run after WOB R5/XGAME, or in parallel where they are
CPU-only (e.g. aggregation ablations reusing existing R5 raw scores). Paper drafting may proceed
in parallel at all times, but **every paper claim stays gated to completed evidence** and must be
registered in the claim registry before use.

## 4. Execution order (A–I)

Stages are executed in order; do not burn stages.

- **A. Repo state audit and plan lock.** This document + `NEXT_ACTION.md` update. (in progress)
- **B. WOB expansion opening / evaluation-readiness freeze.** Freeze seed42 non-locked WOB
  evaluation manifest, reporting paths, and claim boundary; validate locally. (this batch)
- **C. R3-WOB seeds 43/44 real-action training.** Completed as training-artifact validation only;
  seed43/seed44 are now SHA256-verified and validator-passed. Precondition satisfied.
- **D. R5-WOB non-locked identical-episode evaluation.** Same frozen manifest for all methods;
  LeWM seeds 42/43/44 + `frame_diff` + train-normal-fitted `feature_distance`.
- **E. R5-XGAME TempGlitch vs WOB comparison.** Controlled cross-dataset table; no universal
  generalization claim; preserve the WOB action-synchronization caveat.
- **F. R6 ablations + failure analysis.** Aggregation, surprise-distance, training-budget, SIGReg,
  and WOB action-conditioning ablations; per-category failure analysis.
- **G. R7 validation decision.** Single frozen configuration, selection rule, aggregation,
  threshold rule, and claim boundary; locked-test go/no-go recommendation only.
- **H. R8 FISAT paper completion.** Sections, tables, figures, appendices, artifact index, all
  claim-gated.
- **I. Optional demo/live package.** Only after R6/R7 evidence stabilizes; illustrative only.

## 5. Hard constraints (unchanged, restated)

- Do not touch, materialize, or score the locked test.
- Do not claim WOB performance before WOB evaluation artifacts exist.
- Do not claim cross-game generalization before R5-XGAME exists.
- Do not claim action-conditioning benefit before the WOB real-action vs zero-action ablation
  exists.
- Do not claim SIGReg benefit before the R6 SIGReg ablation exists.
- No fabricated metrics, citations, figures, or tables.
- Every new paper claim is registered in `docs/research/16_claim_registry.md` before use.
- Never commit raw datasets, credentials, `.tar`, `.tar.gz`, `.zip`, `.pt`, `.pth`, `.ckpt`,
  `.lance`, raw outputs, or large artifacts.

## 6. Current batch (Phase A + B)

Phase A+B are preserved on branch `wob-expansion-readiness-gate` at commit `3271734`. Phase C prep
added the generalized seed validator, robust seed43/44 Kaggle runners, tests, and claim registry
entry C-073. Seed43 and seed44 have now produced locally SHA256-verified, validator-passed
training artifacts recorded as C-074 and C-075. The next empirical gate is `R5-WOB`, which
remains separately closed until explicitly authorized.
