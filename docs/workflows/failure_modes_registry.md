# Failure Modes Registry

Every new failure requires one appended row and one regression test. This table only grows.

| date | bucket | symptom_signature | root_cause | fix_commit_sha | guard_test |
|---|---|---|---|---|---|
| 2026-06-13 | packaging_idempotency | `FileExistsError: ... already exists` | Kaggle materialization reused an existing destination | `b67bfd3` | `test_generated_kernel_bootstraps_from_kaggle_like_cwd` |
| 2026-06-13 | environment_decode | `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f` | Windows subprocess pipe used the default cp1252 decoder | `02e65a6` | `test_default_executor_replaces_non_utf8_subprocess_output` |
| 2026-06-13 | dataloader_spawn | `attempt ... before the current process has finished its bootstrapping phase` | Rendered kernel called training at top level with DataLoader workers | `3ef825a` | `test_generated_kernel_is_immutable_and_fail_closed` |
| 2026-06-13 | artifact_contract | `Missing LeWM GPU profile artifacts: validator_report.json` | Kaggle reused a stale `/tmp/glitch-world-model` source tree, so the remote run emitted the previous artifact contract | `ff372c9` | `test_generated_kernel_is_immutable_and_fail_closed`, `test_successful_kernel_with_invalid_artifacts_is_recorded_as_failed` |
| 2026-06-17 | gpu_compute_capability | `P100 sm_60 / no kernel image / unsupported PyTorch CUDA arch` | Kaggle assigned GPU below sm_70 for PyTorch cu128 runtime | `TBD` | `test_compute_capability_failure_requires_stop_and_fix` |
| 2026-06-22 | lancedb_api_mismatch | `AttributeError: 'LanceDBConnection' object has no attribute 'list_tables'` | `run_kaggle_r5_wob_staged.sh` and `requirements/kaggle_runtime.txt` pinned `lancedb==0.25.3` and `pylance==0.39.0`, below the `stable-worldmodel==0.1.1` metadata floor (`lancedb>=0.30.0`, `pylance>=4.0.0`), so `LanceWriter.__enter__` called a newer LanceDB API against older wheels | `TBD` | `test_lancedb_pin_meets_stable_worldmodel_floor`, `test_pylance_pin_meets_stable_worldmodel_floor`, `test_lancedb_and_pylance_match_optional_runtime_file` |

Only `cuda_oom` may advance the approved batch-size ladder. Transient Kaggle infrastructure
failures receive bounded retry. Every other bucket requires stop-and-fix.
