# WOB Controlled Expansion Plan

Date: 2026-06-18

Status: WOB-P1 seed42 training artifact verified; local `WOB-P0` is blocked on missing local tar
inputs, the Kaggle-native `WOB-P0` pass is verified, and WOB evaluation remains unopened

## 1. Current Evidence Baseline

- R4 rerun seed43/44 training artifacts are artifact-backed after local SHA256 verification and
  per-seed validator passes.
- R5 TempGlitch completed as a provenance-bound, non-locked identical-episode evaluation family on
  the research MVP source.
- Within that frozen R5 TempGlitch family, LeWM seed44 produced the highest observed AUROC and
  AUPRC rows relative to the required `frame_diff` and train-normal-fitted `feature_distance`
  baselines, while F1/calibration remained mixed because `frame_diff` had the strongest observed
  F1 row.
- Locked test remains closed, unmaterialized, and unscored.
- WOB-P1 seed42 training has produced a SHA256-verified, validator-passed artifact under the
  train-normal / validation-normal protocol.
- WOB evaluation has not started.
- `WOB-P0` has now completed as a local dataset/materialization audit and metadata-only manifest
  preview freeze.
- Local `WOB-P0` remains `BLOCKED_MISSING_INPUTS` because the local attached WOB root satisfies
  only 10 of the 120 non-locked rows expected by the frozen split metadata.
- Official Kaggle listing checks confirm that all 120 non-locked rows exist in the authoritative
  Kaggle datasets.
- The verified Kaggle-native `WOB-P0` evidence bundle hash is
  `e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9`.
- The Kaggle-native `WOB-P0` bundle reports `READY_FOR_WOB_P1`, 120 selected rows, 120 resolved
  rows, 0 missing rows, 59 locked rows skipped, `locked_test_materialized=false`,
  `locked_test_scored=false`, `performance_metrics_present=false`, and
  `semantic_action_synchronization_verified=false`.
- The verified WOB-P1 seed42 artifact hash is
  `54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03`.
- The intended next milestone is a non-locked WOB evaluation-readiness gate for seed42, not a
  63.462 GiB local full download and not seed43/44 training.

## 2. Why WOB Comes Next

- WOB is the controlled real-action branch that best matches the original action-conditioned LeWM
  motivation.
- It provides action-bearing episodes that can test whether the TempGlitch zero-action findings
  transfer to a constrained action-conditioned setting.
- It creates a route to evaluate real-action versus zero-action handling without opening locked
  test.
- It must remain a predeclared expansion rather than a post-hoc rescue path for any weak or mixed
  TempGlitch result.

## 3. WOB Dataset/Protocol Audit

Verified from the current repository:

- Public Kaggle sources:
  - `benedictwilkinsai/world-of-bugs-normal`
  - `benedictwilkinsai/world-of-bugs-test`
- License: ODC Attribution License (ODC-By).
- Main normal inventory: 60 episodes; the duplicate `NORMAL-TRAIN-SMALL` subset is excluded.
- Bug inventory: 119 episodes across 10 bug categories.
- Frozen split recorded in the repository: 48 normal train, 12 normal validation, 60 bug
  validation, and 59 locked-test metadata episodes.
- The tar audit reads numeric fields with `allow_pickle=False`.
- Inspected timesteps contain `state`, `action`, `reward`, and `done`.
- State shape is float32 CHW RGB `(3,84,84)`.
- The converter maps the four discrete navigation actions to one-hot `(T,4)` vectors.
- Upstream loader proof already exists for reduced real WOB conversion and loading.

Known caveats:

- The current evidence supports structural action compatibility, not a replay-based
  synchronization proof for every action sequence.
- The locked split remains metadata-only and must stay closed during planning and any future
  non-locked execution.
- Full-scale train/validation materialization remains a separate execution concern.

## 4. Scope Decision for First WOB Phase

Recommended first-pass scope: staged pilot -> full family.

Justification:

- It preserves the TempGlitch evidence chain while limiting risk from WOB action-synchronization
  uncertainty and runtime unknowns.
- It allows one seed to verify data materialization, real-action training integrity, artifact
  contracts, and reporting compatibility before spending three-seed budget.
- It keeps the expansion claim-safe: first prove the WOB path is operational, then decide whether
  to expand to the full family.

This means the first WOB execution sequence should start with a seed42-only controlled pass and
open seed43/44 only after the first seed passes its validator and the reporting path remains
aligned.

## 5. Proposed WOB Phase Breakdown

- `WOB-P0`: Kaggle-native full non-locked dataset/materialization audit plus manifest freeze.
- `WOB-P1`: seed42 real-action normal-only run. Status: training artifact verified, evaluation
  unopened.
- `WOB-P2`: seed43/44 only if seed42 evaluation-readiness review passes and budget remains
  acceptable.
- `WOB-P3`: WOB identical-episode evaluation under a frozen manifest and matched reporting path.
- `WOB-P4`: TempGlitch versus WOB cross-dataset comparison under matched claim boundaries.
- `WOB-P5`: zero-action versus real-action/action-conditioning ablation only if earlier evidence
  justifies it.
- `WOB-P6`: paper integration or a fallback future-work framing, depending on evidence quality.

## 6. WOB Execution Inputs Required

- WOB train-normal source inventory.
- WOB validation-normal source inventory.
- WOB validation-buggy source inventory.
- WOB action streams in the existing tar format.
- Frozen WOB split/protocol metadata.
- Converter/materializer path:
  - `scripts/freeze_wob_protocol.py`
  - `scripts/build_wob_lewm_lance.py`
  - `src/glitch_detection/wob_protocol.py`
  - `src/glitch_detection/lewm_data.py`
- LeWM runtime compatible with real-action training.
- GPU runtime target approved for the chosen seed schedule.
- Planned ignored output roots for artifacts, scores, and metrics.
- Existing validators plus any documented implementation gap for missing WOB-specific orchestration.
- Kaggle-native root-preparation path:
  - `scripts/check_wob_kaggle_listing.py`
  - `cloud/wob_kaggle_native/prepare_wob_root.py`
  - `cloud/wob_kaggle_native/preflight.sh`
  - `cloud/wob_kaggle_native/run_wob_p0_audit.sh`

## 7. Compute And Runtime Budget

No WOB-measured runtime is currently recorded in the repository, so this phase does not invent one.

Conservative planning posture:

- Treat WOB evaluation runtime and memory as unknown until a seed42 evaluation-readiness review
  defines the actual envelope.
- Use TempGlitch R4/R5 only as rough planning context, not as a WOB runtime estimate.
- Do not launch seed43/44 before seed42 evaluation readiness is reviewed.
- Require an explicit compute decision before launching any further WOB training or evaluation.

## 8. Claim Boundaries

Safe after WOB-P1 seed42 training artifact verification:

- WOB is planned as a controlled expansion after the completed TempGlitch R5 checkpoint.
- The repository already has frozen WOB protocol evidence and reduced loader compatibility.
- WOB-P1 seed42 produced a SHA256-verified, validator-passed training artifact under the recorded
  train-normal / validation-normal protocol.
- Validation-buggy rows remained excluded from fit/selection.
- WOB evaluation remains unopened.
- Local `WOB-P0` is complete but blocked on missing non-locked source tar inputs.
- Kaggle-native `WOB-P0` passed and the seed42 `WOB-P1` training artifact is verified; WOB
  evaluation remains unopened until a separate explicit human command.

Unsafe before WOB evaluation:

- Any WOB detection-performance or evaluation result claim.
- Any cross-game generalization claim.
- Any action-conditioning benefit claim.
- Any superiority or state-of-the-art claim.
- Any locked-test claim.

## 9. Go/No-Go Criteria for WOB Execution

All of the following must be true before any WOB evaluation or additional WOB training:

- Post-R5 docs and context are aligned.
- The WOB manifest and reporting sequence are frozen.
- No unresolved leakage or protocol-integrity issue remains.
- The WOB locked split remains closed.
- Compute budget and runtime target are explicitly approved.
- Required scripts are identified, or any implementation gap is documented and accepted.
- A separate explicit human command authorizes WOB evaluation or additional WOB training.

## 10. Next Phase Prompt Stub

Next prompt theme:

`WOB-P1 seed42 non-locked evaluation-readiness gate`

The next execution-oriented phase should freeze the seed42 non-locked WOB evaluation manifest and
reporting path, confirm that validation-buggy rows are used only for evaluation, and stop before
running evaluation unless explicitly authorized to continue.

Update after execution of that prompt:

- `WOB-P0` completed locally in [71_wob_p0_dataset_materialization_audit.md](71_wob_p0_dataset_materialization_audit.md).
- The current local blocker is missing non-locked WOB tar inputs under the attached root.
- The Kaggle-native `WOB-P0` pass is verified from the downloaded evidence bundle with hash
  `e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9`.
- The seed42 WOB-P1 training artifact is verified in
  [72_wob_p1_seed42_training_result.md](72_wob_p1_seed42_training_result.md).
- The next gate is evaluation readiness only; seed43/44, WOB evaluation, and locked test remain
  closed until separately authorized.
