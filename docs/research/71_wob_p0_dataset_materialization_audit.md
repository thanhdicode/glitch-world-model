# WOB-P0 Dataset / Materialization Audit

Date: 2026-06-18

Status: `LOCAL_BLOCKED_BUT_KAGGLE_PASSED`

## 1. Executive Status

`WOB-P0` now has two distinct states that must not be conflated. Local `WOB-P0` remains blocked
on incomplete raw tar coverage, while the Kaggle-native `WOB-P0` path has passed with a verified
downloaded evidence bundle. World of Bugs training and evaluation remain unopened.

Current status split:

- `LOCAL_WOB_P0_STATUS = BLOCKED_MISSING_INPUTS`
- `WOB_P0_KAGGLE_STATUS = PASSED`
- `WOB_STATUS = READY_FOR_WOB_P1`
- `WOB_P1_TRAINING_STATUS = NOT_STARTED`

The full local 63.462 GiB non-locked acquisition path is not the intended training workflow.
Official Kaggle datasets should be mounted directly inside a Kaggle notebook, filtered by the
repository split metadata, and audited there before any training decision is made.

Verified Kaggle-native `WOB-P0` bundle facts:

- evidence tarball SHA256:
  `e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9`
- final audit status: `READY_FOR_WOB_P1`
- mounted dataset roots:
  - `/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-normal`
  - `/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-test`
- split CSV:
  `/kaggle/working/glitch-world-model/configs/wob_protocol/split.csv`
- phase: `p0_full_nonlocked`
- `selected_rows = 120`
- `resolved_rows = 120`
- `missing_rows = 0`
- `locked_rows_skipped = 59`
- `locked_test_materialized = false`
- `locked_test_scored = false`
- `performance_metrics_present = false`
- `action_metadata_present = true`
- `semantic_action_synchronization_verified = false`
- WOB root manifest SHA256:
  `cc6031f304cb6c39d49567ba25a750e1f7d7e07738b471237db4f4ac8b46ea73`
- audit manifest preview SHA256:
  `cefe9f32014bde5aa767d81019479d2f17fbe5fd1dfd388982e8812d4f434d22`
- GPU preflight:
  - `Tesla T4`
  - `sm_75`
  - `future_training_gpu_ok = true`

First live Kaggle execution notes:

- The official datasets mounted successfully under nested Kaggle paths such as
  `/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-normal` and
  `/kaggle/input/datasets/benedictwilkinsai/world-of-bugs-test`.
- The first live Kaggle-native attempt exposed runner bugs rather than a data-availability
  problem:
  - shallow path detection assumptions;
  - `find | head` under `set -o pipefail` causing exit code `141`;
  - exporting `LEWM_REPO_ROOT` after calling `setup_runtime.sh`;
  - assuming ignored `outputs/gate3/world_of_bugs/split.csv` exists in a fresh clone.
- The repository now includes a one-section Kaggle entrypoint that fixes those wrapper issues and
  uses tracked protocol metadata under `configs/wob_protocol/`.

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

Human action required before `WOB-P1` execution:

1. Keep local WOB replay blocked unless full raw coverage is explicitly needed for another reason.
2. Keep locked-test rows closed and excluded via `split.csv`.
3. Authorize only the seed42 `WOB-P1` real-action train-normal run; do not open seed43/44 or WOB
   evaluation yet.

## 6. Claim Boundaries

Safe:

- `WOB-P0 audit completed.`
- `WOB remains unopened for training/evaluation.`
- `A metadata-only non-locked manifest preview was frozen from existing split metadata.`
- `Current local WOB inputs are incomplete for a full local WOB replay.`
- `The official Kaggle dataset listings contain all non-locked rows needed for a Kaggle-native WOB-P0 audit.`
- `The verified Kaggle-native WOB-P0 bundle resolved all 120 non-locked rows while keeping locked test closed.`
- `Kaggle-native WOB-P0 tooling passed, but WOB training/evaluation remain unopened.`

Unsafe:

- Any WOB performance claim.
- Any cross-game generalization claim.
- Any action-conditioning benefit claim.
- Any superiority or state-of-the-art claim.
- Any locked-test result claim.

## 7. Recommended Next Phase

Current recommendation: prepare `WOB-P1` seed42 safely, but do not run WOB evaluation yet.

Next prerequisite task:

- prepare the seed42 one-section Kaggle runner using the verified `WOB-P0` bundle.

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
