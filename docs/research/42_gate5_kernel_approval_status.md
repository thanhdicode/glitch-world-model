# Gate 5 Kernel Approval Status

Status date: 2026-06-11

## Status: BLOCKED_ON_V5_DATASET_SOURCE

The one-time kernel approval matched fingerprint
`8c918c264e3a840e47ab11b540de38c2ce0520ca0688bb280637fff49d68d0a4`,
passed the package security scan, and was unconsumed immediately before execution.

It was consumed at `2026-06-11T02:31:30.540310+00:00` for exactly one kernel push. Kaggle
returned HTTP `409 Conflict`. The kernel was not visible in the subsequent account kernel list,
so there is no run to poll or artifact set to download.

The repository approval schema records `fingerprint`, `approved_at`, `one_time_use`, and
`consumed_at`; it does not define a separate approval-phrase field. The artifact was valid under
that current schema before consumption.

No retry is authorized. The next live attempt requires:

1. resolve the Kaggle submission conflict without performing another push;
2. regenerate or revalidate the final package and fingerprint;
3. create a new ignored request record;
4. obtain a fresh explicit approval for that exact fingerprint.

Changing the kernel identity, metadata, script, dependencies, or packaged source invalidates the
old fingerprint.

## Consumed V2 Approval

After the HTTP 409 diagnosis, a corrected validation-only package was prepared locally under
ignored storage:

- Dataset slug: `huynhdieuthanh/lewm-tempglitch-gate5-smoke`
- v2 kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v2`
- Dataset fingerprint: `897f4a8f310aa9891db5c45cc5bc78285c7cb965a469e46d78346d28c1877f51`
- Kernel inventory SHA-256: `8f6474331d4873971d42757ccee96494cd306f455399443b97e860dc40906e4c`
- Kernel metadata SHA-256: `c3749bcf9c41b009f853577eb75fc94338e38312625a1ea372bea66da328abf1`
- Kernel script SHA-256: `0d484a956d29b15c866f60e37efe1c1979b53b1c39bd70762036d4abcea59fca`
- v2 kernel approval fingerprint:
  `4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`

The v2 approval was created, preflight returned `approval_status: valid`, dataset status returned
`ready`, and the approval was consumed at `2026-06-11T03:48:07.773881+00:00`. Exactly one v2
kernel push was submitted. Kaggle accepted kernel version 1, then the run reached
`KernelWorkerStatus.ERROR`.

The error log shows the script failed before training because it tried to install from
`/kaggle/src/lewm-runtime.txt`, which Kaggle did not place beside `/kaggle/src/script.py`.

## Consumed V3 Approval

The generator now makes the validation kernel clone this repository and install from
`requirements/lewm-runtime.txt`. A v3 package/request was prepared:

- Dataset slug: `huynhdieuthanh/lewm-tempglitch-gate5-smoke`
- v3 kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v3`
- Dataset fingerprint: `897f4a8f310aa9891db5c45cc5bc78285c7cb965a469e46d78346d28c1877f51`
- Kernel inventory SHA-256: `5487df7e1f185b10d4a54844af7d7d8bd09428b6823cc4ac080ca56ee5fdb570`
- Kernel metadata SHA-256: `8d105564299a05e4025c9d6836e41e2f382eac0970b442c6130dcc97ae392a35`
- Kernel script SHA-256: `106e3da88790b112e91808ee1dde954b46d566ec18858b0e22d856db38c88a66`
- v3 kernel approval fingerprint:
  `47107246ea537fce9c435717301b12c0408f296b34567602f6408b77a5d856c9`

The v3 approval was created, preflight returned `approval_status: valid`, dataset status returned
`ready`, and the approval was consumed at `2026-06-11T05:01:48.445275+00:00`. Exactly one v3
kernel push was submitted. Kaggle accepted kernel version 1, then the run reached
`KernelWorkerStatus.ERROR`.

The v3 error log shows dependency installation failed before training because full
`stable-worldmodel[env,train]` pulled `box2d-py`, which failed to build on Kaggle Python 3.12.

## New V4 Request

The generator now clones the repository to `/tmp/glitch-world-model`, keeping the clone out of
Kaggle output artifacts, and installs only the minimal LeWM smoke dependencies. A new ignored v4
package/request has been prepared:

- Dataset slug: `huynhdieuthanh/lewm-tempglitch-gate5-smoke`
- v4 kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v4`
- Dataset fingerprint: `897f4a8f310aa9891db5c45cc5bc78285c7cb965a469e46d78346d28c1877f51`
- Kernel inventory SHA-256: `22df50ee756e446ae6ccc37abbfebcc19a3be1b5880b8afc317aeb9452c0d8dd`
- Kernel metadata SHA-256: `96884642a9fa9ca19fd87b7f08b47f9eff8cc6a18000e2c66b153e49f754eb45`
- Kernel script SHA-256: `dee3fbfdf930aef32bb68831133bd7920d99bc71f235cb7cebe9a298bfc02ab6`
- v4 kernel approval fingerprint:
  `e3a3ad6bcfd73c99ee295003041db7651e375a1d970b11bd3665a7393c87382a`

The request records are in ignored storage at `outputs/gate5/approvals/tempglitch_kernel_v4`.
The associated approval was later created and consumed exactly once as recorded below.

## Consumed V4 Approval And V5 Status

The v4 approval for fingerprint
`e3a3ad6bcfd73c99ee295003041db7651e375a1d970b11bd3665a7393c87382a` was consumed at
`2026-06-11T05:34:30.433734+00:00` for exactly one push. Kaggle accepted version 1, then the run
failed before epoch 1 because `LanceDataset` attempted to write under read-only `/kaggle/input`.

The v5 generator now copies the two Lance directories to writable `/tmp/lewm_input` before
training. No v5 package or request has been generated because the required source root
`outputs/gate5/source` is absent. V5 fingerprint and approval status are therefore `PENDING` and
`BLOCKED_ON_DATASET`, respectively. No live push is authorized.
