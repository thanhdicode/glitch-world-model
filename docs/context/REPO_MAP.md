# REPO_MAP.md

Generated: 2026-06-11T06:32:55+00:00
Commit: `54fa49f37b99dca85fcd9329c8924ede05776c21`
Generator: `scripts/update_context_cache.py`

## Top-Level Map
| Path | Purpose |
|---|---|
| `"docs/` | Tracked repository path. |
| `AGENTS.md/` | Tracked repository path. |
| `CLAUDE.md/` | Tracked repository path. |
| `CONVENTIONS.md/` | Tracked repository path. |
| `Makefile/` | Tracked repository path. |
| `PLAYBOOK.md/` | Tracked repository path. |
| `README.md/` | Tracked repository path. |
| `RULES.md/` | Tracked repository path. |
| `configs/` | Experiment and runtime configuration. |
| `docs/` | Research evidence, workflows, context cache, and roadmap. |
| `dvc.yaml/` | Tracked repository path. |
| `kaggle/` | Validation-only launch packages. |
| `paper/` | Cautious manuscript scaffold and generated tables. |
| `pyproject.toml/` | Tracked repository path. |
| `requirements/` | Optional runtime requirement pins. |
| `scripts/` | Auditable command-line entry points. |
| `src/` | Reusable pipeline and model integration code. |
| `tests/` | Fast default-environment tests. |

## Python Modules
| File | Symbols | Purpose |
|---|---|---|
| `scripts/build_lewm_lance_dataset.py` | _read_split, build_lewm_lance_dataset, build_parser, main | Python module. |
| `scripts/build_lewm_split.py` | _read_rows, _read_exposed, build_parser, main | Python module. |
| `scripts/build_tempglitch_lewm_lance.py` | _rows_by_source, build_parser, main | Python module. |
| `scripts/build_wob_lewm_lance.py` | build_parser, main | Python module. |
| `scripts/check_claim_registry.py` | Claim, parse_claim_registry, validate_claims, build_parser, main | Python module. |
| `scripts/convert_tempglitch_labels.py` | build_parser, main | Python module. |
| `scripts/create_dynamics_test_dataset.py` | draw_scene, main | Python module. |
| `scripts/create_hard_dynamics_dataset.py` | draw_scene, main | Python module. |
| `scripts/create_test_dataset.py` | draw_frame, main | Python module. |
| `scripts/doctor.py` | module_available, check_gitignored, collect_report, print_report, core_requirements_satisfied, main | Python module. |
| `scripts/download_glitchbench_subset.py` | fetch_rows, download_image, save_resized, main | Python module. |
| `scripts/download_tempglitch.py` | build_parser, main | Python module. |
| `scripts/evaluate_tempglitch_locked_test.py` | format_metric, read_video_rows, validate_locked_test_release, write_locked_metrics_markdown, build_parser, main | Python module. |
| `scripts/freeze_tempglitch_protocol.py` | _sha256, _exposed_groups, build_parser, main | Python module. |
| `scripts/freeze_wob_protocol.py` | _kaggle_csv, _sha256, build_parser, main | Python module. |
| `scripts/ingest_phase6e_kaggle_artifacts.py` | _read_json, _validate_required_artifacts, _read_and_validate_scores, _write_report, ingest_phase6e_kaggle_artifacts, build_parser, main | Python module. |
| `scripts/inspect_lewm_dataset.py` | build_parser, main | Python module. |
| `scripts/make_paper_tables.py` | write_tables, main | Python module. |
| `scripts/prepare_lewm_kaggle_package.py` | build_parser, main | Python module. |
| `scripts/prepare_phase6e_kaggle_dataset.py` | _require_file, _estimate_directory, _upload_readme, prepare_phase6e_kaggle_dataset, build_parser, main | Python module. |
| `scripts/request_lewm_kaggle_approvals.py` | build_parser, main | Python module. |
| `scripts/run_dynamics_experiments.py` | main | Python module. |
| `scripts/run_glitchbench_subset_experiments.py` | main | Python module. |
| `scripts/run_hard_dynamics_experiments.py` | main | Python module. |
| `scripts/run_kaggle_lewm.py` | build_parser, main | Python module. |
| `scripts/run_kaggle_video_autoencoder.py` | _require_file, _read_grouped_split, _validate_clip_dirs, _write_json, run_kaggle_video_autoencoder, build_parser, main | Python module. |
| `scripts/run_phase6e_kaggle_automation.py` | build_parser, build_config, main | Python module. |
| `scripts/run_synthetic_demo.py` | write_synthetic_frames, write_synthetic_labels, main | Python module. |
| `scripts/run_tempglitch_repeated_grouped_splits.py` | _require_file, _clear_score_files, _write_split_artifacts, _write_partitions, _format_metric, _write_locked_summary, _metric_summary, _write_repeated_summary, run_repeated_grouped_experiments, build_parser, main | Python module. |
| `scripts/run_tempglitch_smoke_test.py` | build_parser, main | Python module. |
| `scripts/run_tempglitch_split_experiments.py` | write_scores_csv, preprocess_tempglitch_videos, normal_train_records, score_validation_and_test, write_comparison, best_and_worst_categories, positive_clip_counts, clip_counts_by_split, build_parser, main | Python module. |
| `scripts/run_tempglitch_video_level_experiments.py` | require_input_file, find_input_file, category_metrics, build_parser, main | Python module. |
| `scripts/run_worldofbugs_asset_demo.py` | first_existing, write_repeated_frames, write_labels, main | Python module. |
| `scripts/select_tempglitch_protocol_config.py` | load_validation_candidates, build_parser, main | Python module. |
| `scripts/smoke_lewm_checkpoint.py` | build_parser, main | Python module. |
| `scripts/summarize_all_experiments.py` | read_json, fmt, row_for, main | Python module. |
| `scripts/update_context_cache.py` | CacheMetadata, git_sha, metadata, read_optional, has_gate5_conflict_record, build_boot, build_project_state, build_next_action, build_last_handoff_template, build_context_readme, build_context_policy, build_task_router | Python module. |
| `scripts/validate_context_cache.py` | main | Python module. |
| `scripts/validate_lewm_kaggle_artifacts.py` | main | Python module. |
| `scripts/validate_research_release.py` | git_tracked_files, validate_tracked_files, validate_required_paths, validate_playbook_structure, validate_release, working_tree_errors, build_parser, main | Python module. |
| `src/glitch_detection/__init__.py` | - | Glitch detection research pipeline. |
| `src/glitch_detection/analysis.py` | _split_metadata, load_scores_with_labels, prediction_rows, _group_rows, binary_metrics_by_group, top_errors, _percentile, score_distribution_summary, write_json, write_rows_csv, write_markdown_table, _format_markdown_value | Python module. |
| `src/glitch_detection/calibration.py` | calibrate_threshold, evaluate_with_fixed_threshold | Python module. |
| `src/glitch_detection/compare_experiments.py` | read_metrics, build_comparison_rows, _format_value, write_comparison_markdown, parse_metric_args, build_parser, main | Python module. |
| `src/glitch_detection/dataset_protocols.py` | FrozenSplitRecord, _hash_fraction, _group_rows, _stratified_assignments, freeze_tempglitch_split, freeze_wob_split, audit_frozen_split, _raise_on_invalid, _sha256, write_frozen_split | Python module. |
| `src/glitch_detection/dataset_report.py` | read_score_values, build_report, _format_value, write_markdown_report, build_parser, main | Python module. |
| `src/glitch_detection/evaluate.py` | read_scores, binary_metrics, choose_best_f1_threshold, auroc, average_precision, evaluate_scores, build_parser, main | Python module. |
| `src/glitch_detection/experiment_protocol.py` | ProtocolPartitions, ValidationProtocolResult, _git_commit, _config_hash, _write_json, prepare_protocol_partitions, run_validation_protocol, score_test_with_release_gate | Python module. |
| `src/glitch_detection/feature_distance.py` | list_clip_frames, clip_feature, fit_centroid, score_records_with_centroid, score_records, score_manifest, build_parser, main | Python module. |
| `src/glitch_detection/frame_diff.py` | load_grayscale_frame, list_clip_frames, score_clip, score_manifest, build_parser, main | Python module. |
| `src/glitch_detection/kaggle_automation.py` | _utc_now, _write_json_atomic, AutomationState, StateStore, ApprovalStore, FingerprintBuilder, SecurityViolation, SecurityGuard, is_transient_error, _gpu_block_reason, AutomationCommandError, AutomationBlockedError | Python module. |
| `src/glitch_detection/lewm_adapter.py` | LeWMIntegrationError, ActionMode, sha256_file, LeWMCheckpointSpec, LeWMAdapter | Python module. |
| `src/glitch_detection/lewm_data.py` | LeWMDataUnavailableError, LeWMEpisode, _frame_paths, episode_from_clip, episode_from_wob_tar, episode_from_video, write_lance_dataset, inspect_lance_dataset, write_dataset_inspection | Python module. |
| `src/glitch_detection/lewm_kaggle.py` | LeWMKaggleConfig, validate_kaggle_slug, quota_allocation, render_validation_kernel, prepare_lewm_kaggle_package, _read_json, _sha256_json, validate_lewm_kaggle_package, _kernel_fingerprint_payload, _write_request, validate_kernel_push_preflight, request_package_approvals | Python module. |
| `src/glitch_detection/lewm_latent.py` | LeWMUnavailableError, resolve_checkpoint, resolve_config, _require_torch, _list_frames, _load_pixels, score_record, score_manifest, build_parser, main | Python module. |
| `src/glitch_detection/lewm_protocol.py` | LeWMSplitRecord, _hash_fraction, assign_hashed_group_splits, audit_lewm_splits, write_lewm_split | Python module. |
| `src/glitch_detection/lewm_training.py` | LeWMTrainingError, LeWMTrainConfig, _require_runtime, _config_hash, build_model_config, _preprocess_pixels, _sigreg, _dataset, _run_epoch, train_lewm | Python module. |
| `src/glitch_detection/manifest.py` | ClipRecord, LabelInterval, write_manifest, read_manifest, read_labels, clip_has_glitch | Python module. |
| `src/glitch_detection/mini_latent.py` | MiniLatentModel, list_clip_frames, load_frame_vector, load_clip_matrix, fit_pca_encoder, encode_frames, fit_transition, transition_error, fit_model, score_records_with_model, score_records, score_manifest | Python module. |
| `src/glitch_detection/model_selection.py` | select_validation_config, evaluate_locked_test | Python module. |
| `src/glitch_detection/neural_protocol.py` | NeuralPartitions, rebase_clip_records, prepare_neural_partitions | Python module. |
| `src/glitch_detection/pairs.py` | _row_value, infer_tempglitch_pair_id, group_sources_by_pair, pair_leakage_report | Python module. |
| `src/glitch_detection/plot_scores.py` | read_score_series, plot_scores, build_parser, main | Python module. |
| `src/glitch_detection/preprocess.py` | list_frame_files, resize_and_save_frame, preprocess_frames, extract_video_frames, preprocess_input, build_parser, main | Python module. |
| `src/glitch_detection/repeated_eval.py` | FittedScorer, train_normal_records, fit_scorer_for_split, score_fitted_scorer, clip_score_rows, write_clip_scores_csv, split_rows_as_dicts, source_labels_for_split, build_video_rows | Python module. |
| `src/glitch_detection/run_baseline.py` | run_baseline, build_parser, main | Python module. |
| `src/glitch_detection/score_clips.py` | _frame_diff_scorer, available_scorers, run_scorer, build_parser, main | Python module. |
| `src/glitch_detection/splits.py` | SplitRecord, GroupedSplitRecord, _split_counts_for_group, assign_video_splits, assign_grouped_video_splits, validate_no_group_leakage, write_grouped_split_csv, write_split_csv, read_split_csv, read_grouped_split_csv, sources_for_split, split_counts_by_group | Python module. |
| `src/glitch_detection/statistics.py` | _percentile, _metric, bootstrap_metric_ci | Python module. |
| `src/glitch_detection/tempglitch.py` | TempGlitchVideoRef, TempGlitchSample, normalize_tempglitch_label, encode_tempglitch_video_url, parse_tempglitch_video_url, _load_json, fetch_tempglitch_dataset_info, fetch_tempglitch_rows, fetch_all_tempglitch_metadata, tempglitch_category_counts, _relative_video_path, _write_tempglitch_source_readme | Python module. |
| `src/glitch_detection/video_autoencoder.py` | VideoAutoencoderUnavailableError, VideoAutoencoderConfig, require_torch, resolve_checkpoint, list_clip_frames, select_frame_paths, load_clip_array, ClipTensorDataset, build_model, _resolve_device, _set_deterministic_seed, _data_loader | Python module. |
| `src/glitch_detection/video_eval.py` | _percentile, _aggregate, aggregate_scores_by_source, source_labels_from_intervals, _split_metadata, build_video_level_rows, compute_video_level_metrics, calibrate_video_threshold, evaluate_video_with_fixed_threshold, write_video_rows_csv, write_json, write_video_comparison | Python module. |
| `src/glitch_detection/wob_protocol.py` | parse_wob_inventory, inspect_wob_episode_tar | Python module. |

## Scripts
| Script | Purpose | Related gate |
|---|---|---|
| `scripts/build_lewm_lance_dataset.py` | CLI/helper script. | Gate 5 |
| `scripts/build_lewm_split.py` | CLI/helper script. | Gate 5 |
| `scripts/build_tempglitch_lewm_lance.py` | CLI/helper script. | Gate 5 |
| `scripts/build_wob_lewm_lance.py` | CLI/helper script. | Gate 5 |
| `scripts/check_claim_registry.py` | CLI/helper script. | general |
| `scripts/convert_tempglitch_labels.py` | CLI/helper script. | general |
| `scripts/create_dynamics_test_dataset.py` | CLI/helper script. | general |
| `scripts/create_hard_dynamics_dataset.py` | CLI/helper script. | general |
| `scripts/create_test_dataset.py` | CLI/helper script. | general |
| `scripts/doctor.py` | CLI/helper script. | general |
| `scripts/download_glitchbench_subset.py` | CLI/helper script. | general |
| `scripts/download_tempglitch.py` | CLI/helper script. | general |
| `scripts/evaluate_tempglitch_locked_test.py` | CLI/helper script. | general |
| `scripts/freeze_tempglitch_protocol.py` | CLI/helper script. | general |
| `scripts/freeze_wob_protocol.py` | CLI/helper script. | general |
| `scripts/ingest_phase6e_kaggle_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/inspect_lewm_dataset.py` | CLI/helper script. | Gate 5 |
| `scripts/make_paper_tables.py` | CLI/helper script. | general |
| `scripts/prepare_lewm_kaggle_package.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_phase6e_kaggle_dataset.py` | CLI/helper script. | Gate 5 |
| `scripts/request_lewm_kaggle_approvals.py` | CLI/helper script. | Gate 5 |
| `scripts/run_dynamics_experiments.py` | CLI/helper script. | general |
| `scripts/run_glitchbench_subset_experiments.py` | CLI/helper script. | general |
| `scripts/run_hard_dynamics_experiments.py` | CLI/helper script. | general |
| `scripts/run_kaggle_lewm.py` | CLI/helper script. | Gate 5 |
| `scripts/run_kaggle_video_autoencoder.py` | CLI/helper script. | Gate 5 |
| `scripts/run_phase6e_kaggle_automation.py` | CLI/helper script. | Gate 5 |
| `scripts/run_synthetic_demo.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_repeated_grouped_splits.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_smoke_test.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_split_experiments.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_video_level_experiments.py` | CLI/helper script. | general |
| `scripts/run_worldofbugs_asset_demo.py` | CLI/helper script. | general |
| `scripts/select_tempglitch_protocol_config.py` | CLI/helper script. | general |
| `scripts/smoke_lewm_checkpoint.py` | CLI/helper script. | Gate 5 |
| `scripts/summarize_all_experiments.py` | CLI/helper script. | general |
| `scripts/update_context_cache.py` | CLI/helper script. | general |
| `scripts/validate_context_cache.py` | CLI/helper script. | general |
| `scripts/validate_lewm_kaggle_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/validate_research_release.py` | CLI/helper script. | general |

## Tests
| Test | Coverage |
|---|---|
| `tests/conftest.py` | conftest |
| `tests/test_analysis.py` | analysis |
| `tests/test_calibration.py` | calibration |
| `tests/test_compare_experiments.py` | compare_experiments |
| `tests/test_context_cache.py` | context_cache |
| `tests/test_dataset_protocols.py` | dataset_protocols |
| `tests/test_dataset_report.py` | dataset_report |
| `tests/test_doctor.py` | doctor |
| `tests/test_evaluate.py` | evaluate |
| `tests/test_experiment_protocol.py` | experiment_protocol |
| `tests/test_feature_distance.py` | feature_distance |
| `tests/test_frame_diff.py` | frame_diff |
| `tests/test_imports.py` | imports |
| `tests/test_ingest_phase6e_kaggle_artifacts.py` | ingest_phase6e_kaggle_artifacts |
| `tests/test_kaggle_automation_foundation.py` | kaggle_automation_foundation |
| `tests/test_kaggle_automation_orchestrator.py` | kaggle_automation_orchestrator |
| `tests/test_kaggle_automation_validation.py` | kaggle_automation_validation |
| `tests/test_kaggle_video_autoencoder_runner.py` | kaggle_video_autoencoder_runner |
| `tests/test_leakage_aware_scorers.py` | leakage_aware_scorers |
| `tests/test_lewm_adapter.py` | lewm_adapter |
| `tests/test_lewm_data.py` | lewm_data |
| `tests/test_lewm_kaggle.py` | lewm_kaggle |
| `tests/test_lewm_latent.py` | lewm_latent |
| `tests/test_lewm_protocol.py` | lewm_protocol |
| `tests/test_lewm_training.py` | lewm_training |
| `tests/test_locked_test_gate.py` | locked_test_gate |
| `tests/test_manifest.py` | manifest |
| `tests/test_mini_latent.py` | mini_latent |
| `tests/test_model_selection.py` | model_selection |
| `tests/test_neural_protocol.py` | neural_protocol |
| `tests/test_pairs.py` | pairs |
| `tests/test_phase6e_kaggle_automation_cli.py` | phase6e_kaggle_automation_cli |
| `tests/test_phase6e_kaggle_docs.py` | phase6e_kaggle_docs |
| `tests/test_prepare_phase6e_kaggle_dataset.py` | prepare_phase6e_kaggle_dataset |
| `tests/test_preprocess.py` | preprocess |
| `tests/test_protocol_splits.py` | protocol_splits |
| `tests/test_repeated_eval.py` | repeated_eval |
| `tests/test_repeated_grouped_runner.py` | repeated_grouped_runner |
| `tests/test_research_release_tools.py` | research_release_tools |
| `tests/test_run_baseline.py` | run_baseline |
| `tests/test_score_clips.py` | score_clips |
| `tests/test_splits.py` | splits |
| `tests/test_statistics.py` | statistics |
| `tests/test_tempglitch.py` | tempglitch |
| `tests/test_tempglitch_split_runner.py` | tempglitch_split_runner |
| `tests/test_video_autoencoder.py` | video_autoencoder |
| `tests/test_video_eval.py` | video_eval |
| `tests/test_wob_protocol.py` | wob_protocol |

## Docs
| Doc | Purpose |
|---|---|
| `docs/context/BOOT.md` | BOOT |
| `docs/context/CONTEXT_POLICY.md` | CONTEXT POLICY |
| `docs/context/LAST_HANDOFF.md` | LAST HANDOFF |
| `docs/context/NEXT_ACTION.md` | NEXT ACTION |
| `docs/context/PROJECT_STATE.md` | PROJECT STATE |
| `docs/context/README.md` | README |
| `docs/context/REPO_MAP.md` | REPO MAP |
| `docs/context/TASK_ROUTER.md` | TASK ROUTER |
| `docs/research/00_research_overview.md` | 00 research overview |
| `docs/research/01_problem_statement.md` | 01 problem statement |
| `docs/research/02_literature_matrix.md` | 02 literature matrix |
| `docs/research/03_github_repo_inventory.md` | 03 github repo inventory |
| `docs/research/04_dataset_benchmark_map.md` | 04 dataset benchmark map |
| `docs/research/05_methodology_v0.md` | 05 methodology v0 |
| `docs/research/06_experiment_plan.md` | 06 experiment plan |
| `docs/research/07_baseline_plan.md` | 07 baseline plan |
| `docs/research/08_reproducibility_checklist.md` | 08 reproducibility checklist |
| `docs/research/09_risks_and_limitations.md` | 09 risks and limitations |
| `docs/research/10_paper_outline.md` | 10 paper outline |
| `docs/research/11_tempglitch_integration_plan.md` | 11 tempglitch integration plan |
| `docs/research/12_experiment_results_log.md` | 12 experiment results log |
| `docs/research/15_reproducibility_checklist.md` | 15 reproducibility checklist |
| `docs/research/16_claim_registry.md` | 16 claim registry |
| `docs/research/17_source_verification_log.md` | 17 source verification log |
| `docs/research/18_full_paper_readiness_gap.md` | 18 full paper readiness gap |
| `docs/research/19_benchmark_access_resolution.md` | 19 benchmark access resolution |
| `docs/research/20_phase2_dataset_pipeline_report.md` | 20 phase2 dataset pipeline report |
| `docs/research/21_phase3_phase4_baseline_results.md` | 21 phase3 phase4 baseline results |
| `docs/research/22_phase3b_scaled_failure_analysis.md` | 22 phase3b scaled failure analysis |
| `docs/research/23_evaluation_protocol.md` | 23 evaluation protocol |
| `docs/research/23_video_level_protocol.md` | 23 video level protocol |
| `docs/research/24_paper_results_decision.md` | 24 paper results decision |
| `docs/research/25_phase6c_protocol_hardening_plan.md` | 25 phase6c protocol hardening plan |
| `docs/research/26_phase6c_protocol_results.md` | 26 phase6c protocol results |
| `docs/research/27_phase6d_repeated_grouped_experiment_protocol.md` | 27 phase6d repeated grouped experiment protocol |
| `docs/research/28_phase6d_repeated_grouped_results.md` | 28 phase6d repeated grouped results |
| `docs/research/29_phase6e_kaggle_video_autoencoder_protocol.md` | 29 phase6e kaggle video autoencoder protocol |
| `docs/research/30_phase6e_kaggle_run_log_template.md` | 30 phase6e kaggle run log template |
| `docs/research/31_phase6e_kaggle_validation_results.md` | 31 phase6e kaggle validation results |
| `docs/research/34_kaggle_training_plan.md` | 34 kaggle training plan |
| `docs/research/36_lewm_integration_audit.md` | 36 lewm integration audit |
| `docs/research/37_lewm_runtime_checkpoint_report.md` | 37 lewm runtime checkpoint report |
| `docs/research/38_lewm_data_format.md` | 38 lewm data format |
| `docs/research/39_lewm_kaggle_training_guide.md` | 39 lewm kaggle training guide |
| `docs/research/40_gate3_gate4_real_dataset_protocol.md` | 40 gate3 gate4 real dataset protocol |
| `docs/research/40_research_tooling_stack.md` | 40 research tooling stack |
| `docs/research/41_dvc_hydra_migration_plan.md` | 41 dvc hydra migration plan |
| `docs/research/41_gate5_current_state.md` | 41 gate5 current state |
| `docs/research/42_experiment_tracking_plan.md` | 42 experiment tracking plan |
| `docs/research/42_gate5_kernel_approval_status.md` | 42 gate5 kernel approval status |
| `docs/research/43_gate5_kaggle_cuda_smoke_results.md` | 43 gate5 kaggle cuda smoke results |
| `docs/research/adr/ADR-001-topic-scope.md` | ADR-001-topic-scope |
| `docs/research/adr/ADR-002-dataset-strategy.md` | ADR-002-dataset-strategy |
| `docs/research/adr/ADR-003-lewm-integration-strategy.md` | ADR-003-lewm-integration-strategy |
| `docs/research/adr/ADR-004-mandatory-lewm-main-method.md` | ADR-004-mandatory-lewm-main-method |
| `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch (1).md` | MASTER ROADMAP LeWM Glitch (1) |
| `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v2.md` | MASTER ROADMAP LeWM Glitch v2 |
| `docs/superpowers/plans/2026-06-06-baseline-glitch-pipeline.md` | 2026-06-06-baseline-glitch-pipeline |
| `docs/superpowers/plans/2026-06-09-phase6d-repeated-grouped-run.md` | 2026-06-09-phase6d-repeated-grouped-run |
| `docs/superpowers/plans/2026-06-09-phase6e-kaggle-automation.md` | 2026-06-09-phase6e-kaggle-automation |
| `docs/superpowers/plans/2026-06-09-phase6e-kaggle-launch-package.md` | 2026-06-09-phase6e-kaggle-launch-package |
| `docs/superpowers/plans/2026-06-09-phase6e-kaggle-video-autoencoder.md` | 2026-06-09-phase6e-kaggle-video-autoencoder |
| `docs/superpowers/plans/2026-06-10-research-grade-lab.md` | 2026-06-10-research-grade-lab |
| `docs/superpowers/specs/2026-06-09-phase6e-kaggle-automation-design.md` | 2026-06-09-phase6e-kaggle-automation-design |
| `docs/superpowers/specs/2026-06-09-phase6e-kaggle-video-autoencoder-design.md` | 2026-06-09-phase6e-kaggle-video-autoencoder-design |
| `docs/workflows/00_environment_audit.md` | 00 environment audit |
| `docs/workflows/01_global_research_tooling_plan.md` | 01 global research tooling plan |
| `docs/workflows/agent_governance_sources.md` | agent governance sources |
| `docs/workflows/agent_task_template.md` | agent task template |
| `docs/workflows/artifact_policy.md` | artifact policy |
| `docs/workflows/codex_task_protocol.md` | codex task protocol |
| `docs/workflows/codex_workflow.md` | codex workflow |
| `docs/workflows/dvc_mlflow_plan.md` | dvc mlflow plan |
| `docs/workflows/experiment_release_gates.md` | experiment release gates |
| `docs/workflows/experiment_tracking.md` | experiment tracking |
| `docs/workflows/kaggle_gpu_protocol.md` | kaggle gpu protocol |
| `docs/workflows/kaggle_live_approval.md` | kaggle live approval |
| `docs/workflows/lewm_integration_protocol.md` | lewm integration protocol |
| `docs/workflows/locked_test_release.md` | locked test release |
| `docs/workflows/new_research_project_bootstrap.md` | new research project bootstrap |
