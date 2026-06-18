# WOB-P0 Dataset / Materialization Audit

Date: 2026-06-18

Status: `BLOCKED_MISSING_INPUTS`

## 1. Executive Status

`WOB-P0` completed as a local dataset/materialization audit plus metadata-only manifest-preview
freeze. World of Bugs training and evaluation remain unopened. The current repository contains the
frozen WOB protocol, the reduced Lance conversion proof, and a dedicated `WOB-P0` audit runner,
but the local attached WOB root does not contain the full non-locked tar tree required for a full
local replay.

Current status split:

- `LOCAL_WOB_P0_STATUS = BLOCKED_MISSING_INPUTS`
- `KAGGLE_NATIVE_STATUS = READY_FOR_KAGGLE_WOB_P0`
- `WOB_P1_TRAINING_STATUS = NOT_STARTED`

The full local 63.462 GiB non-locked acquisition path is not the intended training workflow.
Official Kaggle datasets should be mounted directly inside a Kaggle notebook, filtered by the
repository split metadata, and audited there before any training decision is made.

## 2. Evidence Sources Inspected

- `docs/research/40_gate3_gate4_real_dataset_protocol.md`
- `docs/research/65_lewm_research_mvp_source_audit.md`
- `docs/research/68_r5_tempglitch_and_wob_expansion_plan.md`
- `docs/research/69_r5_tempglitch_identical_episode_results.md`
- `docs/research/70_wob_controlled_expansion_plan.md`
- `outputs/gate3/world_of_bugs/inventory.csv`
- `outputs/gate3/world_of_bugs/protocol_audit.json`
- `outputs/gate3/world_of_bugs/split.csv`
- `outputs/gate3/world_of_bugs/split.audit.json`
- `outputs/gate4/wob_train.lance`
- `outputs/gate4/wob_validation.lance`
- `scripts/freeze_wob_protocol.py`
- `scripts/build_wob_lewm_lance.py`
- `scripts/run_wob_p0_materialization_audit.py`
- `scripts/check_wob_kaggle_listing.py`
- `cloud/wob_kaggle_native/prepare_wob_root.py`
- `src/glitch_detection/wob_protocol.py`
- `src/glitch_detection/lewm_data.py`
- `src/glitch_detection/wob_p0_audit.py`
- `tests/test_wob_protocol.py`
- `tests/test_wob_p0_audit.py`

## 3. WOB Protocol Facts

| Item | Finding | Evidence |
|---|---|---|
| Public inputs | Kaggle sources are `benedictwilkinsai/world-of-bugs-normal` and `benedictwilkinsai/world-of-bugs-test`. | `docs/research/40_gate3_gate4_real_dataset_protocol.md`, `scripts/freeze_wob_protocol.py` |
| License | ODC Attribution License (ODC-By). | `docs/research/40_gate3_gate4_real_dataset_protocol.md`, `scripts/freeze_wob_protocol.py` |
| Inventory counts | 60 main normal episodes and 119 bug episodes across 10 categories. | `outputs/gate3/world_of_bugs/protocol_audit.json`, `docs/research/40_gate3_gate4_real_dataset_protocol.md` |
| Split names | Repository split labels are `train`, `validation`, and `test`; their semantic roles are train-normal, validation-normal plus validation-buggy, and locked-test. | `outputs/gate3/world_of_bugs/split.csv`, `outputs/gate3/world_of_bugs/split.audit.json` |
| Frozen split counts | 48 normal train, 12 normal validation, 60 bug validation, 59 locked-test metadata rows. | `outputs/gate3/world_of_bugs/split.audit.json`, `docs/research/40_gate3_gate4_real_dataset_protocol.md` |
| Action representation | Tar steps contain scalar discrete `action` alongside `state`, `reward`, and `done`; the converter maps actions to one-hot `(T,4)` tensors. | `outputs/gate3/world_of_bugs/protocol_audit.json`, `src/glitch_detection/lewm_data.py`, `tests/test_wob_protocol.py` |
| Action caveat | Structural action compatibility is verified, but replay/action synchronization is not proven beyond the recorded caveat `semantic_action_synchronization_verified=false`. | `outputs/gate3/world_of_bugs/protocol_audit.json`, `docs/research/40_gate3_gate4_real_dataset_protocol.md` |
| Locked split | Locked test exists only as metadata and remains unmaterialized and unscored. | `outputs/gate3/world_of_bugs/split.audit.json`, `docs/research/40_gate3_gate4_real_dataset_protocol.md` |

## 4. Materialization Status

- Existing converter/materializer scripts are present:
  - `scripts/freeze_wob_protocol.py`
  - `scripts/build_wob_lewm_lance.py`
  - `src/glitch_detection/wob_protocol.py`
  - `src/glitch_detection/lewm_data.py`
- Existing local Lance outputs are present under `outputs/gate4/`:
  - `wob_train.lance`
  - `wob_train_5.lance`
  - `wob_validation.lance`
  - `wob_validation_5.lance`
- Dedicated audit tooling was added and executed:
  - `scripts/run_wob_p0_materialization_audit.py`
  - `src/glitch_detection/wob_p0_audit.py`
- Audit run:
  - command: `python scripts/run_wob_p0_materialization_audit.py --wob-root outputs/wob_schema_audit/attached --output-dir outputs/wob_p0_materialization_audit --dry-run --allow-materialization-check --no-locked --write-manifest-preview`
  - status: `BLOCKED_MISSING_INPUTS`
  - non-locked rows expected from frozen metadata: `120`
  - non-locked tar rows found under the provided local root: `10`
  - non-locked tar rows missing under the provided local root: `110`
- Kaggle-native listing check:
  - command: `python scripts/check_wob_kaggle_listing.py --output-dir outputs/wob_kaggle_listing`
  - result: all `120` non-locked rows are present in the official Kaggle listings
  - total listed non-locked bytes: `68,141,332,480` (`63.462 GiB`)
  - local full download of those rows was intentionally stopped and cleaned because direct Kaggle mounting is the intended workflow
- Manifest preview/freeze:
  - metadata-only preview written to `outputs/wob_p0_materialization_audit/wob_manifest_preview.csv`
  - SHA256: `fffbd08be4c5ade02487784b762805ecbfb1d89f962988986ee075854807e54f`
  - companion files:
    - `outputs/wob_p0_materialization_audit/wob_manifest_preview.sha256`
    - `outputs/wob_p0_materialization_audit/wob_manifest_metadata.json`
    - `outputs/wob_p0_materialization_audit/wob_p0_audit.json`
    - `outputs/wob_p0_materialization_audit/wob_p0_audit.md`

## 5. Missing Inputs / Implementation Gaps

Missing local inputs are the blocker for local replay, not for Kaggle-native preparation.

- The frozen split expects the non-locked WOB tar tree to resolve directly from `split.csv`
  sources such as:
  - `NORMAL-TRAIN/ep-0000/ep-0000.tar`
  - `TEST/<category>/ep-XXXX/ep-XXXX.tar` for validation-buggy rows
- The provided local root `outputs/wob_schema_audit/attached/` contains only 10 matching
  non-locked tar files, leaving 110 non-locked rows unresolved.
- Example missing paths recorded by the audit:
  - `C:\Users\ADMIN\Desktop\glitch-world-model\outputs\wob_schema_audit\attached\NORMAL-TRAIN\ep-0002\ep-0002.tar`
  - `C:\Users\ADMIN\Desktop\glitch-world-model\outputs\wob_schema_audit\attached\TEST\BlackScreen\ep-0001\ep-0001.tar`
  - `C:\Users\ADMIN\Desktop\glitch-world-model\outputs\wob_schema_audit\attached\TEST\CameraClipping\ep-0000\ep-0000.tar`

Human action required before `WOB-P1`:

1. Run the Kaggle-native `WOB-P0` audit with the official mounted Kaggle datasets.
2. Keep locked-test rows closed and excluded via `split.csv`.
3. Review the Kaggle-native `WOB-P0` report before authorizing any `WOB-P1` training.

## 6. Claim Boundaries

Safe:

- `WOB-P0 audit completed.`
- `WOB remains unopened for training/evaluation.`
- `A metadata-only non-locked manifest preview was frozen from existing split metadata.`
- `Current local WOB inputs are incomplete for a full local WOB replay.`
- `The official Kaggle dataset listings contain all non-locked rows needed for a Kaggle-native WOB-P0 audit.`
- `Kaggle-native WOB-P0 tooling is prepared, but training/evaluation remain unopened.`

Unsafe:

- Any WOB performance claim.
- Any cross-game generalization claim.
- Any action-conditioning benefit claim.
- Any superiority or state-of-the-art claim.
- Any locked-test result claim.

## 7. Recommended Next Phase

Current recommendation: do not open `WOB-P1` yet.

Next prerequisite task:

- run the Kaggle-native `WOB-P0` audit in a Kaggle notebook with the official datasets attached.

Only after that passes should the next execution phase become:

- `WOB-P1` seed42 real-action train-normal run.

## 8. Kaggle / Cloud Guidance For The Next Execution Phase

This guidance is for `WOB-P1` only after the Kaggle-native `WOB-P0` pass succeeds and a human
explicitly authorizes training.

- Kaggle is acceptable only if the runtime provides a T4-or-newer GPU with CUDA `sm_70+` and at
  least 14 GB VRAM.
- Do not use P100; preflight must fail on `sm_60`.
- Start with seed42 only.
- Train-normal only.
- Keep locked test closed.
- Run a dry-run/preflight first before any live training submission.
- Required inputs should include the mounted official Kaggle inputs, frozen split metadata, the
  Kaggle-native root-preparation/audit scripts, and the chosen LeWM runtime/config package.
- Do not upload a local 63 GiB WOB tar tree back to Kaggle.
