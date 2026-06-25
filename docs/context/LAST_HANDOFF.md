# LAST_HANDOFF.md

Last completed task: K2 GlitchBench runner repair for read-only package validation and real LeWM
scoring
Commit: latest branch commit for this task (see `git log -1`)
Date: 2026-06-25T00:00:00Z

## What Changed

- Patched `scripts/run_kaggle_glitchbench_benchmark.py` so learned-baseline config constructors no
  longer receive `device=...`; device is still passed to `train_model(...)` and
  `score_records_with_checkpoint(...)`.
- Added regression tests covering the learned-baseline constructor path and a full-K2 setup path
  that reaches learned-baseline setup without the Kaggle `TypeError`.
- Added `cloud/k2_glitchbench/run_kaggle_k2_full.sh`, which installs the isolated LeWM runtime,
  verifies imports, and only then runs the scientific full K2 benchmark command.
- Extended staged-install completeness tests so K2 now fails CI if `hydra-core`,
  `stable-pretraining`, `stable-worldmodel`, `lancedb`, or the fast-fail import verification step
  are dropped from the K2 launcher.
- Patched `scripts/validate_glitchbench_bundle.py` so protocol-materialization temp files are now
  written outside `package_root`, making direct `/kaggle/input` validation read-only safe.
- Added a regression test that proves validation leaves the mounted package untouched and writes the
  temporary protocol CSV externally.
- Upgraded `scripts/run_kaggle_glitchbench_benchmark.py` from a baseline-only partial runner into a
  complete K2 runner with:
  - explicit `--baseline-only` engineering mode
  - fail-closed scientific full-run behavior when LeWM artifacts are absent
  - seed42/43/44 LeWM artifact-root validation
  - real LeWM scoring on the exact K2 validation manifest
  - `mean` and `max` aggregation support
  - train-normal `p95` thresholding
  - per-seed/per-aggregation score CSVs plus metadata
- Added `scripts/build_k2_lewm_seed_artifact_dataset.py` and built a normalized Kaggle-ready
  artifact zip for the current local seed42/43/44 roots.
- Updated the K2 runbook, GlitchBench claim boundary, claim registry, paper claim map, pending
  paper table, and context cache to reflect the repaired K2 path and the non-scientific status of
  `--baseline-only`.

## Checks Passed

- focused runner/validator/builder tests
- direct local K2 package dry-run after the repair
- local build of the normalized LeWM seed-artifact dataset
- full repository verification suite still pending until this task's final code/docs diff is
  checked at completion

## Safety Status

- GlitchBench remains image-level and synthetic-normal.
- K2 still supports no temporal-localization or cross-game generalization claim.
- `--baseline-only` is now explicitly documented as an engineering smoke test only.
- No GlitchBench metric claim was added because no downloaded K2 artifact has validated yet.
- No SIGReg or action-conditioning effect claim was added.
- No locked-test access, materialization, or scoring occurred in this task.

## Gate Status After Task

- P3 local K2 repair is complete.
- The next external action is a Kaggle rerun of the direct `/kaggle/input` dry-run, followed by the
  scientific full K2 launch with the LeWM artifact dataset attached.
- P4 local ablation tooling remains available, but K3 should stay closed until K2 intake completes.
- Gate 10 remains closed.

## Open Blockers

- The repaired K2 runner still requires a user-operated Kaggle rerun and local post-run intake.
- K3 still requires K2 intake completion plus a separate user-operated Kaggle launch.
- GlitchBench cannot support temporal-localization claims on the current public path.

## Next Recommended Task

- Rerun the scientific K2 Kaggle job on the pinned commit that includes the learned-baseline
  constructor fix and the new runtime-install launcher, then validate the downloaded artifact
  locally before any K2 metric enters the claim registry.

## Files Likely Relevant Next

- `scripts/validate_glitchbench_bundle.py`
- `scripts/run_kaggle_glitchbench_benchmark.py`
- `scripts/build_k2_lewm_seed_artifact_dataset.py`
- `docs/research/120_kaggle_k2_glitchbench_runbook.md`
- `docs/research/121_glitchbench_claim_boundary.md`
