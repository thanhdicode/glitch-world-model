# Gate 5 Current State

Status date: 2026-06-11

Gate 5 remains `partial`. The validation-only TempGlitch package exists in ignored storage, its
private dataset is ready on Kaggle, and the remote Lance file names and sizes match the approved
local package. No downloaded Kaggle CUDA train/resume artifact set exists.

## Package And Approval Audit

- Dataset inventory SHA-256:
  `897f4a8f310aa9891db5c45cc5bc78285c7cb965a469e46d78346d28c1877f51`
- Kernel approval fingerprint:
  `8c918c264e3a840e47ab11b540de38c2ce0520ca0688bb280637fff49d68d0a4`
- Dataset status: ready; eight Lance files matched by relative name and byte size.
- Dataset approval: consumed by the completed upload.
- First kernel approval: consumed by the HTTP 409 push attempt.
- Second kernel approval: consumed at `2026-06-11T03:48:07.773881+00:00`; Kaggle accepted
  `huynhdieuthanh/lewm-gate5-cuda-smoke-v2` version 1, then the run failed before training.
- Third kernel approval: consumed at `2026-06-11T05:01:48.445275+00:00`; Kaggle accepted
  `huynhdieuthanh/lewm-gate5-cuda-smoke-v3` version 1, then the run failed before training.
- Fourth kernel approval: consumed at `2026-06-11T05:34:30.433734+00:00`; Kaggle accepted
  `huynhdieuthanh/lewm-gate5-cuda-smoke-v4` version 1, then the run failed before epoch 1.
- Confirmed 409 preflight cause: the consumed package used the same Kaggle slug for dataset and
  kernel, `huynhdieuthanh/lewm-tempglitch-gate5-smoke`.
- Corrected v2 ignored package prepared after the 409 incident:
  `outputs/gate5/packages/tempglitch_kernel_v2`.
- Corrected v2 kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v2`.
- Corrected v2 kernel fingerprint:
  `4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`.
- Corrected v2 approval request root:
  `outputs/gate5/approvals/tempglitch_kernel_v2`.
- v2 failure cause: generated script looked for `/kaggle/src/lewm-runtime.txt`, but Kaggle ran
  the code as `/kaggle/src/script.py` without the packaged auxiliary file beside it.
- New v3 ignored package prepared after the v2 runtime failure:
  `outputs/gate5/packages/tempglitch_kernel_v3`.
- New v3 kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v3`.
- New v3 kernel fingerprint:
  `47107246ea537fce9c435717301b12c0408f296b34567602f6408b77a5d856c9`.
- New v3 approval request root:
  `outputs/gate5/approvals/tempglitch_kernel_v3`.
- v3 failure cause: full `stable-worldmodel[env,train]` dependency installation pulled
  `box2d-py`, which failed to build on Kaggle Python 3.12 before training started.
- New v4 ignored package prepared after the v3 dependency failure:
  `outputs/gate5/packages/tempglitch_kernel_v4`.
- New v4 kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v4`.
- New v4 kernel fingerprint:
  `e3a3ad6bcfd73c99ee295003041db7651e375a1d970b11bd3665a7393c87382a`.
- New v4 approval request root:
  `outputs/gate5/approvals/tempglitch_kernel_v4`.
- v4 failure cause: `LanceDataset` attempted to create writable connection state under the
  read-only `/kaggle/input/lewm-tempglitch-gate5-smoke` mount.
- v5 source fix: copy train and validation Lance directories to `/tmp/lewm_input` and pass those
  writable paths to both `train_lewm` calls.
- v5 source root: restored from the existing ignored package parent
  `outputs/gate5/packages/tempglitch/dataset`.
- v5 kernel fingerprint:
  `b98afd071bdf7ccc2bd1e4734689fdf09f67d0d44d4651369c3e1b112baaab79`.
- v5 approval: consumed at `2026-06-11T06:27:45.100446+00:00`; exactly one push was accepted.
- v5 failure cause: Kaggle did not expose either named Lance directory under the fixed
  `/kaggle/input/lewm-tempglitch-gate5-smoke` path.
- v6 offline fix: discover each named Lance directory recursively under `/kaggle/input` before
  copying it to `/tmp/lewm_input`.
- v6 request fingerprint:
  `358e2d77c60c3986be2e84f3c6044200ebfcc2a5fe8f68b0800273fc8c7b6910`; approval is missing.
- Locked test: not packaged, materialized, or scored.

## 409 Diagnosis Matrix

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| Kernel slug already exists or was reserved | UNKNOWN | No read-only local artifact proves a pre-existing Kaggle kernel; the failed slug was not visible in the account list after the 409. |
| Kernel slug equals dataset slug | CONFIRMED | Consumed `kernel-metadata.json` and `dataset-metadata.json` both used `huynhdieuthanh/lewm-tempglitch-gate5-smoke`. |
| Placeholder owner such as `private/...` | RULED_OUT | Consumed package used owner `huynhdieuthanh`, not a placeholder owner. |
| Bad `id` in kernel metadata | CONFIRMED | The kernel `id` was validly formatted but conflicted with the dataset slug; the new guard requires a distinct kernel slug. |
| Bad or stale dataset source slug | RULED_OUT | Kernel `dataset_sources` matched the ready dataset slug. |
| Duplicate title/slug behavior in Kaggle CLI | LIKELY | Kernel title `lewm-tempglitch-gate5-smoke` slugified to the same slug as the dataset and kernel `id`. |
| Package fingerprint approved before metadata fix | CONFIRMED | Old approval fingerprint `8c918...d0a4` covered the pre-fix package and is consumed. |
| Unresolved Kaggle-side stale state | POSSIBLE | The local metadata conflict is sufficient, but Kaggle-side reservation cannot be fully ruled out without another live action, which is forbidden here. |

## V2 Runtime Failure Matrix

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| Dataset not ready | RULED_OUT | `datasets status huynhdieuthanh/lewm-tempglitch-gate5-smoke` returned `ready` immediately before push. |
| Approval missing or mismatched | RULED_OUT | Preflight returned `approval_status: valid` for fingerprint `4d1108...e3f8` before consumption. |
| Duplicate submission retry | RULED_OUT | Exactly one v2 `kernels push` was executed after consuming the fresh approval. |
| Missing packaged runtime file at Kaggle script path | CONFIRMED | Error log reports missing `/kaggle/src/lewm-runtime.txt` before any training artifact was written. |
| CUDA/training/resume failure | NOT ESTABLISHED | The script failed before importing Torch or calling `train_lewm`. |

## V3 Runtime Failure Matrix

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| Dataset not ready | RULED_OUT | `datasets status huynhdieuthanh/lewm-tempglitch-gate5-smoke` returned `ready` immediately before the v3 push. |
| Approval missing or mismatched | RULED_OUT | Preflight returned `approval_status: valid` for fingerprint `47107246...56c9` before consumption. |
| Duplicate submission retry | RULED_OUT | Exactly one v3 `kernels push` was executed after consuming the fresh approval. |
| Missing packaged runtime file at Kaggle script path | RULED_OUT | v3 progressed to dependency installation from the cloned repository. |
| Full LeWM environment dependency build failure | CONFIRMED | The v3 error log reports `box2d-py` failed to build during `stable-worldmodel[env,train]` installation. |
| CUDA/training/resume failure | NOT ESTABLISHED | The script failed before importing Torch or calling `train_lewm`. |

## Artifact Contract Audit

| Expected artifact | Produced by | Currently available from Kaggle run? | Blocker | Fix needed |
| --- | --- | --- | --- | --- |
| `run_config.json` | generated validation kernel | no | v3 failed before writing outputs | approve v4 fingerprint and run once |
| `environment.json` | generated validation kernel | no | v3 failed before writing outputs | same |
| `dataset_metadata.json` | generated validation kernel after training | no | no completed Kaggle training | same |
| `training_metadata.json` | `train_lewm` | no | no completed Kaggle training | same |
| `loss_history.json` | `train_lewm` | no | no completed Kaggle training | same |
| `collapse_diagnostics.json` | `train_lewm` | no | no completed Kaggle training | same |
| `checkpoint.sha256` | `train_lewm` | no | no completed Kaggle training | same |
| `protocol_audit.json` | generated validation kernel | no | v3 failed before writing outputs | same |
| `resume_metadata.json` | generated validation kernel after resume | no | no completed Kaggle resume | same |

Local CPU smoke directories contain training outputs, but they are not Kaggle CUDA evidence and
do not satisfy this table.

## Validator Readiness

The strict validator now checks:

- complete artifact presence;
- CUDA availability and training device;
- resumed epoch advancement;
- matching config, dataset, and checkpoint hashes;
- finite non-empty loss history;
- finite collapse diagnostics;
- false locked-test flags in both protocol and training metadata.

The focused generator tests pass locally. V5 produced only an error log, and strict validation
failed because all nine required artifacts were missing. The offline v6 package is ready but
unapproved; this engineering evidence does not upgrade Gate 5.
