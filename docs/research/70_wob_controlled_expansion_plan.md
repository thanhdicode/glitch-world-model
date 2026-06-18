# WOB Controlled Expansion Plan

Date: 2026-06-18

Status: planning-only; local `WOB-P0` is blocked on missing local tar inputs, while the
Kaggle-native `WOB-P0` preparation path is now in place

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
- World of Bugs training/evaluation have not started.
- `WOB-P0` has now completed as a local dataset/materialization audit and metadata-only manifest
  preview freeze.
- Local `WOB-P0` remains `BLOCKED_MISSING_INPUTS` because the local attached WOB root satisfies
  only 10 of the 120 non-locked rows expected by the frozen split metadata.
- Official Kaggle listing checks confirm that all 120 non-locked rows exist in the authoritative
  Kaggle datasets.
- The intended next milestone is a Kaggle-native `WOB-P0` audit using mounted Kaggle inputs, not a
  63.462 GiB local full download.

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
- `WOB-P1`: seed42 real-action normal-only run.
- `WOB-P2`: seed43/44 only if seed42 validator passes and budget remains acceptable.
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

- Treat WOB runtime and memory as unknown until Kaggle-native `WOB-P0` and the first controlled
  seed pass define the actual envelope.
- Use TempGlitch R4/R5 only as rough planning context, not as a WOB runtime estimate.
- Approve the staged seed42-first plan before any three-seed WOB family is considered.
- Require an explicit compute decision before launching `WOB-P1`.

## 8. Claim Boundaries

Safe before WOB execution:

- WOB is planned as a controlled expansion after the completed TempGlitch R5 checkpoint.
- The repository already has frozen WOB protocol evidence and reduced loader compatibility.
- WOB remains unopened for training/evaluation.
- Local `WOB-P0` is complete but blocked on missing non-locked source tar inputs.
- Kaggle-native `WOB-P0` preparation is complete and should be executed before any `WOB-P1`
  training request.

Unsafe before WOB execution:

- Any WOB result claim.
- Any cross-game generalization claim.
- Any action-conditioning benefit claim.
- Any superiority or state-of-the-art claim.
- Any locked-test claim.

## 9. Go/No-Go Criteria for WOB Execution

All of the following must be true before any WOB training or evaluation:

- Post-R5 docs and context are aligned.
- The WOB manifest and reporting sequence are frozen.
- No unresolved leakage or protocol-integrity issue remains.
- The WOB locked split remains closed.
- Compute budget and runtime target are explicitly approved.
- Required scripts are identified, or any implementation gap is documented and accepted.
- A separate explicit human command authorizes WOB execution.

## 10. Next Phase Prompt Stub

Next prompt theme:

`WOB-P0 Kaggle-native dataset/materialization audit + manifest freeze`

The next execution-oriented phase should audit the frozen WOB inputs, confirm the materialization
path, freeze the first non-locked WOB manifest, and stop before training unless explicitly
authorized to continue.

Update after execution of that prompt:

- `WOB-P0` completed locally in [71_wob_p0_dataset_materialization_audit.md](71_wob_p0_dataset_materialization_audit.md).
- The current local blocker is missing non-locked WOB tar inputs under the attached root.
- The prepared next step is a Kaggle-native `WOB-P0` pass using mounted official Kaggle datasets
  and the `cloud/wob_kaggle_native/` package.
- The one-section notebook entrypoint is
  `cloud/wob_kaggle_native/run_kaggle_wob_p0_all.sh`.
- `WOB-P1` should not start until that Kaggle-native audit passes and a human explicitly
  authorizes training.
