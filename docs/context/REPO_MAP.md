# REPO_MAP.md

Generated: 2026-06-23T16:06:28+00:00
Commit: `6993964547348659cb2f8882f0a84347f765e200`
Generator: `scripts/update_context_cache.py`

## Top-Level Map
| Path | Purpose |
|---|---|
| `"docs/` | Tracked repository path. |
| `AGENTS.md/` | Tracked repository path. |
| `CLAUDE.md/` | Tracked repository path. |
| `CONVENTIONS.md/` | Tracked repository path. |
| `Makefile/` | Tracked repository path. |
| `PACKAGE_FIX_REPORT.md/` | Tracked repository path. |
| `PLAYBOOK.md/` | Tracked repository path. |
| `README.md/` | Tracked repository path. |
| `RULES.md/` | Tracked repository path. |
| `cloud/` | Tracked repository path. |
| `configs/` | Experiment and runtime configuration. |
| `docs/` | Research evidence, workflows, context cache, and roadmap. |
| `dvc.yaml/` | Tracked repository path. |
| `kaggle/` | Validation-only launch packages. |
| `paper/` | Cautious manuscript scaffold and generated tables. |
| `pyproject.toml/` | Tracked repository path. |
| `requirements/` | Optional runtime requirement pins. |
| `scripts/` | Auditable command-line entry points. |
| `slides/` | Tracked repository path. |
| `src/` | Reusable pipeline and model integration code. |
| `tests/` | Fast default-environment tests. |
| `uv.lock/` | Tracked repository path. |

## Python Modules
| File | Symbols | Purpose |
|---|---|---|
| `scripts/assemble_r5_wob_from_stages.py` | build_parser, main | Python module. |
| `scripts/audit_gate6_tempglitch_source.py` | build_parser, main | Python module. |
| `scripts/audit_lewm_research_source.py` | build_parser, main | Python module. |
| `scripts/audit_r5_xgame_split.py` | audit, build_parser, main | Audit an R5-XGame manifest and emit a machine-readable leakage report. |
| `scripts/build_lewm_lance_dataset.py` | _read_split, build_lewm_lance_dataset, build_parser, main | Python module. |
| `scripts/build_lewm_split.py` | _read_rows, _read_exposed, build_parser, main | Python module. |
| `scripts/build_tempglitch_lewm_lance.py` | build_parser, main | Python module. |
| `scripts/build_tempglitch_validation_manifest.py` | evenly_spaced_starts, build_validation_manifest, main | Python module. |
| `scripts/build_wob_lewm_lance.py` | build_parser, main | Python module. |
| `scripts/check_claim_registry.py` | Claim, parse_claim_registry, validate_claims, build_parser, main | Python module. |
| `scripts/check_wob_kaggle_listing.py` | build_parser, load_nonlocked_rows, dataset_slug_for_source, parse_kaggle_files_csv, kaggle_files, human_kaggle_setup_instructions, compute_listing_report, render_markdown, main | Python module. |
| `scripts/convert_tempglitch_labels.py` | build_parser, main | Python module. |
| `scripts/create_dynamics_test_dataset.py` | draw_scene, main | Python module. |
| `scripts/create_hard_dynamics_dataset.py` | draw_scene, main | Python module. |
| `scripts/create_test_dataset.py` | draw_frame, main | Python module. |
| `scripts/diagnose_kaggle_submission.py` | _default_executor, parse_kaggle_username, collect_package_diagnostics, run_redacted_command, _kaggle_executable, build_parser, main | Python module. |
| `scripts/doctor.py` | module_available, check_gitignored, collect_report, print_report, core_requirements_satisfied, main | Python module. |
| `scripts/download_glitchbench_subset.py` | fetch_rows, download_image, save_resized, main | Python module. |
| `scripts/download_tempglitch.py` | build_parser, main | Python module. |
| `scripts/evaluate_tempglitch_locked_test.py` | format_metric, read_video_rows, validate_locked_test_release, write_locked_metrics_markdown, build_parser, main | Python module. |
| `scripts/freeze_r5_xgame_split.py` | build_r5_xgame_rows, write_rows, build_parser, main | Freeze a deterministic, non-locked R5-XGame manifest from the WOB source split. |
| `scripts/freeze_tempglitch_protocol.py` | _sha256, _exposed_groups, build_parser, main | Python module. |
| `scripts/freeze_wob_protocol.py` | _kaggle_csv, _sha256, build_parser, main | Python module. |
| `scripts/ingest_phase6e_kaggle_artifacts.py` | _read_json, _validate_required_artifacts, _read_and_validate_scores, _write_report, ingest_phase6e_kaggle_artifacts, build_parser, main | Python module. |
| `scripts/inspect_lewm_dataset.py` | build_parser, main | Python module. |
| `scripts/make_paper_tables.py` | write_tables, main | Python module. |
| `scripts/plan_frozen_video_representation_baseline.py` | build_parser, main | Python module. |
| `scripts/plot_lewm_surprise_timeline.py` | plot_scores, main | Python module. |
| `scripts/prepare_lewm_gate6_package.py` | build_parser, main | Python module. |
| `scripts/prepare_lewm_gpu_profile_package.py` | _git, main | Python module. |
| `scripts/prepare_lewm_kaggle_package.py` | build_parser, main | Python module. |
| `scripts/prepare_lewm_r3_seed_run.py` | canonical_sha256, git_sha, prepare_seed_run, build_parser, main | Python module. |
| `scripts/prepare_phase6e_kaggle_dataset.py` | _require_file, _estimate_directory, _upload_readme, prepare_phase6e_kaggle_dataset, build_parser, main | Python module. |
| `scripts/prepare_wob_expansion_readiness.py` | _read_split_rows, _sha256_bytes, build_eval_manifest_rows, render_eval_manifest_csv, build_readiness, render_split_source, prepare, build_parser, main | Freeze the seed42 non-locked World of Bugs evaluation-readiness bundle. |
| `scripts/repair_kaggle_kernel_write_path.py` | discover_kaggle_executables, safe_file_status, create_canary_package, build_submission_variants, _run, _diagnostics, _canary_slug, _check_remote, _run_variant, build_parser, main | Python module. |
| `scripts/run_dynamics_experiments.py` | main | Python module. |
| `scripts/run_gate7_lance_scoring.py` | _validate_inputs, build_parser, main | Python module. |
| `scripts/run_gate7_lewm_evaluation.py` | main | Python module. |
| `scripts/run_gate8_baselines_from_lance.py` | baseline_values, fit_feature_centroid, validate_baseline_alignment, _git_sha, _loader, _fit_train_centroid, _batch_strings, _validate_batch_metadata, _score_target, _validate_fingerprints, run_gate8_baselines, build_parser | Python module. |
| `scripts/run_gate9_ablations.py` | validate_gate9_alignment, aggregate_lewm_rows, _evaluate_scorer, evaluate_gate9_rows, run_gate9, build_parser, main | Python module. |
| `scripts/run_glitchbench_subset_experiments.py` | main | Python module. |
| `scripts/run_hard_dynamics_experiments.py` | main | Python module. |
| `scripts/run_kaggle_lewm.py` | _guard_cuda_runtime, build_parser, main | Python module. |
| `scripts/run_kaggle_parity_check.py` | run_utf8_subprocess, kernel_entrypoint_is_guarded, _spawn_probe_source, run_kaggle_parity_check, build_parser, main | Python module. |
| `scripts/run_kaggle_video_autoencoder.py` | _require_file, _read_grouped_split, _validate_clip_dirs, _write_json, run_kaggle_video_autoencoder, build_parser, main | Python module. |
| `scripts/run_lewm_gate6_automation.py` | build_parser, main | Python module. |
| `scripts/run_lewm_gpu_profile_automation.py` | main | Python module. |
| `scripts/run_lewm_scoring.py` | build_parser, _git_commit, main | Python module. |
| `scripts/run_phase6e_kaggle_automation.py` | build_parser, build_config, main | Python module. |
| `scripts/run_r5_tempglitch_identical_episode_evaluation.py` | main | Python module. |
| `scripts/run_r5_wob_identical_episode_evaluation.py` | - | Python module. |
| `scripts/run_r5_wob_stage.py` | - | Python module. |
| `scripts/run_r5_xgame_comparison.py` | _load_metrics, _sha256_file, _validate_wob_output, _extract_best_rows, build_comparison_table, write_comparison_csv, write_provenance, build_parser, main | R5-XGAME: Cross-dataset comparison of TempGlitch R5 and WOB R5 results. |
| `scripts/run_r5_xgame_resume_missing_seed44.py` | _runner, _read_json, _csv_data_row_count, find_partial_output_dir, copy_partial_output_dir, _require_false_flag, validate_partial_output_for_resume, finalize_from_complete_scores, resume_missing_seed44_and_finalize, build_parser, main | Resume/finalize an R5-XGame run from a mounted partial output tree. |
| `scripts/run_r5_xgame_staged.py` | _sha256, _read_manifest, _validate_seed_selection, _role_hash, _validate_counts, _normalize_rows, _resolve_source_path, _coverage, _reject_old_r5_wob_inputs, _stage_marker_path, _file_record, _write_stage_marker | Fail-closed staged entrypoint for the four-role R5-XGame protocol. |
| `scripts/run_r6_tempglitch_ablations.py` | run_aggregation_ablation, run_cpu_ablation, build_parser, main | R6 TempGlitch ablation runner. |
| `scripts/run_r6_wob_ablations.py` | build_parser, main | R6 WOB ablation runner. |
| `scripts/run_synthetic_demo.py` | write_synthetic_frames, write_synthetic_labels, main | Python module. |
| `scripts/run_tempglitch_repeated_grouped_splits.py` | _require_file, _clear_score_files, _write_split_artifacts, _write_partitions, _format_metric, _write_locked_summary, _metric_summary, _write_repeated_summary, run_repeated_grouped_experiments, build_parser, main | Python module. |
| `scripts/run_tempglitch_smoke_test.py` | build_parser, main | Python module. |
| `scripts/run_tempglitch_split_experiments.py` | write_scores_csv, preprocess_tempglitch_videos, normal_train_records, score_validation_and_test, write_comparison, best_and_worst_categories, positive_clip_counts, clip_counts_by_split, build_parser, main | Python module. |
| `scripts/run_tempglitch_video_level_experiments.py` | require_input_file, find_input_file, category_metrics, build_parser, main | Python module. |
| `scripts/run_wob_p0_materialization_audit.py` | main | Python module. |
| `scripts/run_worldofbugs_asset_demo.py` | first_existing, write_repeated_frames, write_labels, main | Python module. |
| `scripts/select_tempglitch_protocol_config.py` | load_validation_candidates, build_parser, main | Python module. |
| `scripts/smoke_lewm_checkpoint.py` | build_parser, main | Python module. |
| `scripts/summarize_all_experiments.py` | read_json, fmt, row_for, main | Python module. |
| `scripts/update_context_cache.py` | CacheMetadata, git_sha, metadata, read_optional, has_gate5_conflict_record, build_boot, build_project_state, build_next_action, build_last_handoff_template, build_context_readme, build_context_policy, build_task_router | Python module. |
| `scripts/validate_cloud_gpu_runtime.py` | _output_root, inspect_runtime, main | Python module. |
| `scripts/validate_context_cache.py` | main | Python module. |
| `scripts/validate_lewm_gate6_artifacts.py` | main | Python module. |
| `scripts/validate_lewm_gpu_profile_artifacts.py` | main | Python module. |
| `scripts/validate_lewm_kaggle_artifacts.py` | main | Python module. |
| `scripts/validate_lewm_r3_seed_artifacts.py` | _read_json, _assert, _finite_numbers, validate_artifacts, main | Python module. |
| `scripts/validate_lewm_research_mvp_config.py` | _require, validate_research_mvp_config, build_parser, main | Python module. |
| `scripts/validate_r5_wob_evaluation.py` | _read_json, _read_csv, _assert, _finite_or_blank, validate_r5_wob, hashlib_sha256, build_parser, main | Python module. |
| `scripts/validate_r5_wob_stage_outputs.py` | build_parser, main | Python module. |
| `scripts/validate_r5_xgame_comparison.py` | validate_r5_xgame, build_parser, main | Validate an R5-XGAME cross-dataset comparison output directory. |
| `scripts/validate_r5_xgame_output_bundle.py` | sha256, _expected_sha256, _verify_sidecar, _safe_extract, _read_csv, _normalized_manifest_payload, normalized_manifest_sha256, _validate_manifest_matches_frozen, _validate_stage_package_marker, _require_metrics, _validate_evaluation_classes, _validate_provenance | Fail-closed validator for a completed R5-XGame output directory or tarball. |
| `scripts/validate_r6_ablations.py` | validate_r6, build_parser, main | Validate R6 ablation outputs. |
| `scripts/validate_research_release.py` | git_tracked_files, validate_tracked_files, validate_required_paths, validate_playbook_structure, validate_release, working_tree_errors, build_parser, main | Python module. |
| `scripts/validate_wob_expansion_readiness.py` | _read_json, _assert, _sha256_bytes, _read_manifest_rows, validate_readiness, build_parser, main | Validate the frozen seed42 non-locked World of Bugs evaluation-readiness bundle. |
| `scripts/validate_wob_seed42_artifacts.py` | main | Python module. |
| `scripts/validate_wob_seed_artifacts.py` | seed_name, validator_status, phase_name, tarball_prefix, required_tarball_files, _read_json, _assert, _assert_false_if_present, _finite_numbers, _sha256_file, _sha256_tar_member, _parse_sha256_sidecar | Python module. |
| `scripts/verify_r5_wob_upload.py` | _sha256_file, _read_expected_hash, _verify_sidecar, _safe_extract, _locate_output_dir, _run_validator, _output_hashes, _metric_inventory, _write_receipt, _verify_extracted, verify, _find_member_text | Verify and ingest an R5-WOB success bundle or inspect a failure bundle. |
| `scripts/verify_wob_p0_kaggle_evidence.py` | sha256_file, parse_sha256_sidecar, _read_text_member, _read_json_member, verify_wob_p0_kaggle_evidence, build_parser, main | Python module. |
| `src/glitch_detection/__init__.py` | - | Glitch detection research pipeline. |
| `src/glitch_detection/analysis.py` | _split_metadata, load_scores_with_labels, prediction_rows, _group_rows, binary_metrics_by_group, top_errors, _percentile, score_distribution_summary, write_json, write_rows_csv, write_markdown_table, _format_markdown_value | Python module. |
| `src/glitch_detection/calibration.py` | calibrate_threshold, evaluate_with_fixed_threshold | Python module. |
| `src/glitch_detection/compare_experiments.py` | read_metrics, build_comparison_rows, _format_value, write_comparison_markdown, parse_metric_args, build_parser, main | Python module. |
| `src/glitch_detection/dataset_protocols.py` | FrozenSplitRecord, _hash_fraction, _group_rows, _stratified_assignments, freeze_tempglitch_split, freeze_wob_split, audit_frozen_split, _raise_on_invalid, _sha256, write_frozen_split | Python module. |
| `src/glitch_detection/dataset_report.py` | read_score_values, build_report, _format_value, write_markdown_report, build_parser, main | Python module. |
| `src/glitch_detection/evaluate.py` | read_scores, binary_metrics, choose_best_f1_threshold, auroc, average_precision, evaluate_scores, build_parser, main | Python module. |
| `src/glitch_detection/experiment_protocol.py` | ProtocolPartitions, ValidationProtocolResult, _git_commit, _config_hash, _write_json, prepare_protocol_partitions, run_validation_protocol, score_test_with_release_gate | Python module. |
| `src/glitch_detection/failure_triage.py` | FailureBucket, classify_failure, allowed_action, is_oom | Python module. |
| `src/glitch_detection/feature_distance.py` | list_clip_frames, clip_feature, fit_centroid, score_records_with_centroid, score_records, score_manifest, build_parser, main | Python module. |
| `src/glitch_detection/frame_diff.py` | load_grayscale_frame, list_clip_frames, score_clip, score_manifest, build_parser, main | Python module. |
| `src/glitch_detection/frozen_video_representation.py` | FrozenVideoRepresentationConfig, dependency_status, plan_frozen_video_representation_baseline | Python module. |
| `src/glitch_detection/gate6_data.py` | read_rows_by_source, sha256_file, select_tempglitch_rows, audit_gate6_source, write_audit | Python module. |
| `src/glitch_detection/kaggle_automation.py` | _utc_now, _write_json_atomic, AutomationState, StateStore, FingerprintBuilder, SecurityViolation, PublicReleaseSpec, KaggleAction, KaggleExecutionPolicy, SecurityGuard, is_transient_error, _gpu_block_reason | Python module. |
| `src/glitch_detection/lewm_adapter.py` | LeWMIntegrationError, ActionMode, sha256_file, LeWMCheckpointSpec, LeWMAdapter | Python module. |
| `src/glitch_detection/lewm_data.py` | LeWMDataUnavailableError, LeWMEpisode, _frame_paths, episode_from_clip, episode_from_wob_tar, episode_from_video, write_lance_dataset, inspect_lance_dataset, write_dataset_inspection | Python module. |
| `src/glitch_detection/lewm_gate6.py` | Gate6KaggleConfig, build_source_archive, render_gate6_kernel, prepare_gate6_kaggle_package, _load_json, _finite_numbers, validate_gate6_kaggle_package, validate_gate6_artifacts | Python module. |
| `src/glitch_detection/lewm_gate6_automation.py` | _write_json, Gate6AutomationConfig, Gate6AutomationHandlers | Python module. |
| `src/glitch_detection/lewm_gpu_profile.py` | _utc_now, _write_json, canonical_sha256, LeWMGPUProfileConfig, build_dataset_manifest, build_profile_fingerprint, run_exact_updates, build_checkpoint_payload, verify_reloaded_checkpoint, environment_snapshot, _contains_forbidden, write_artifact_manifest | Python module. |
| `src/glitch_detection/lewm_gpu_profile_automation.py` | _write_json, enrich_failure, ProfileAutomationConfig, validate_live_launch_contract, ProfileAttemptRunner, run_profile_attempt_ladder | Python module. |
| `src/glitch_detection/lewm_gpu_profile_kaggle.py` | _zip_info, build_permitted_project_snapshot, _bytes_sha256, LeWMGPUProfileKaggleConfig, _git_tracked, _archive_directory, render_profile_kernel, prepare_profile_kaggle_package, validate_profile_kaggle_package | Python module. |
| `src/glitch_detection/lewm_kaggle.py` | LeWMKaggleConfig, validate_kaggle_slug, quota_allocation, supports_cuda_compute_capability, render_validation_kernel, prepare_lewm_kaggle_package, _read_json, _sha256_json, validate_lewm_kaggle_package, _kernel_fingerprint_payload, validate_kernel_push_preflight, build_package_audit | Python module. |
| `src/glitch_detection/lewm_lance_eval.py` | runtime_provenance, select_calibration_episodes, canonical_row_from_sample, canonical_rows_from_samples, validate_manifest_rows, validate_manifest_row, validate_calibration_episode_count, validate_score_alignment, write_csv_rows, read_csv_rows, _lance_dataset, open_metadata_dataset | Python module. |
| `src/glitch_detection/lewm_latent.py` | LeWMUnavailableError, resolve_checkpoint, resolve_config, _require_torch, _list_frames, _load_pixels, score_record, score_manifest, build_parser, main | Python module. |
| `src/glitch_detection/lewm_protocol.py` | LeWMSplitRecord, _hash_fraction, assign_hashed_group_splits, audit_lewm_splits, write_lewm_split | Python module. |
| `src/glitch_detection/lewm_research.py` | LeWMResearchProtocol, _read_csv_by_source, _sha256_file, audit_local_research_source, write_research_audit | Python module. |
| `src/glitch_detection/lewm_surprise.py` | aggregate_scores, score_direction_check, score_record_series, score_record, _resolve_device, score_manifest, registered_score_manifest | Python module. |
| `src/glitch_detection/lewm_training.py` | LeWMTrainingError, LeWMTrainConfig, _require_runtime, _config_hash, build_model_config, _preprocess_pixels, _sigreg, _dataset, _run_epoch, _utc_now, _train_update_step, _train_lewm_by_updates | Python module. |
| `src/glitch_detection/manifest.py` | ClipRecord, LabelInterval, write_manifest, read_manifest, read_labels, clip_has_glitch | Python module. |
| `src/glitch_detection/mini_latent.py` | MiniLatentModel, list_clip_frames, load_frame_vector, load_clip_matrix, fit_pca_encoder, encode_frames, fit_transition, transition_error, fit_model, score_records_with_model, score_records, score_manifest | Python module. |
| `src/glitch_detection/model_selection.py` | select_validation_config, evaluate_locked_test | Python module. |
| `src/glitch_detection/neural_protocol.py` | NeuralPartitions, rebase_clip_records, prepare_neural_partitions | Python module. |
| `src/glitch_detection/pairs.py` | _row_value, infer_tempglitch_pair_id, group_sources_by_pair, pair_leakage_report | Python module. |
| `src/glitch_detection/plot_scores.py` | read_score_series, plot_scores, build_parser, main | Python module. |
| `src/glitch_detection/preprocess.py` | list_frame_files, resize_and_save_frame, preprocess_frames, extract_video_frames, preprocess_input, build_parser, main | Python module. |
| `src/glitch_detection/r5_tempglitch_eval.py` | _read_json, _load_script_module, _write_json, _write_sha256, _percentile, _aggregate, _float_text, _fpr_at_95_tpr, refuse_locked_test_path, parse_seed_artifact_roots, resolve_seed_artifact, planned_output_paths | Python module. |
| `src/glitch_detection/r5_wob_eval.py` | _load_script_module, _read_json, _read_csv_rows, _write_json, _write_report, _parse_keyed_paths, _render_eval_manifest, _validate_readiness_and_manifest, _load_train_rows, _resolve_source_path, summarize_source_coverage, _build_lance_from_rows | Python module. |
| `src/glitch_detection/r5_wob_staged.py` | _stage_marker_path, _path_sha256, _file_record, _check_runtime_imports, _progress, _repack_seed_artifact, _resolve_seed_inputs, _build_window_manifest, _release_cuda_memory, _smoke_eval_rows, _write_stage_marker, _load_stage_marker | Python module. |
| `src/glitch_detection/r5_xgame_live.py` | partition_manifest_rows, training_roles, train_fresh_seed | Four-role R5-XGame materialization contracts used by the staged runner. |
| `src/glitch_detection/r5_xgame_metrics.py` | _fpr_at_95_tpr, evaluate_r5_xgame_binary_scores | Binary episode-level metrics guarded against one-class evaluation. |
| `src/glitch_detection/r5_xgame_protocol.py` | validate_r5_xgame_manifest | Fail-closed protocol checks for the non-locked R5-XGame evaluation. |
| `src/glitch_detection/repeated_eval.py` | FittedScorer, train_normal_records, fit_scorer_for_split, score_fitted_scorer, clip_score_rows, write_clip_scores_csv, split_rows_as_dicts, source_labels_for_split, build_video_rows | Python module. |
| `src/glitch_detection/run_baseline.py` | run_baseline, build_parser, main | Python module. |
| `src/glitch_detection/score_clips.py` | _frame_diff_scorer, available_scorers, run_scorer, build_parser, main | Python module. |
| `src/glitch_detection/splits.py` | SplitRecord, GroupedSplitRecord, _split_counts_for_group, assign_video_splits, assign_grouped_video_splits, validate_no_group_leakage, write_grouped_split_csv, write_split_csv, read_split_csv, read_grouped_split_csv, sources_for_split, split_counts_by_group | Python module. |
| `src/glitch_detection/statistics.py` | _percentile, _metric, bootstrap_metric_ci | Python module. |
| `src/glitch_detection/tempglitch.py` | TempGlitchVideoRef, TempGlitchSample, normalize_tempglitch_label, encode_tempglitch_video_url, parse_tempglitch_video_url, _load_json, fetch_tempglitch_dataset_info, fetch_tempglitch_rows, fetch_all_tempglitch_metadata, tempglitch_category_counts, _relative_video_path, _write_tempglitch_source_readme | Python module. |
| `src/glitch_detection/video_autoencoder.py` | VideoAutoencoderUnavailableError, VideoAutoencoderConfig, require_torch, resolve_checkpoint, list_clip_frames, select_frame_paths, load_clip_array, ClipTensorDataset, build_model, _resolve_device, _set_deterministic_seed, _data_loader | Python module. |
| `src/glitch_detection/video_eval.py` | _percentile, _aggregate, aggregate_scores_by_source, source_labels_from_intervals, _split_metadata, build_video_level_rows, compute_video_level_metrics, calibrate_video_threshold, evaluate_video_with_fixed_threshold, write_video_rows_csv, write_json, write_video_comparison | Python module. |
| `src/glitch_detection/wob_kaggle_common.py` | resolve_existing_path, resolve_split_csv, resolve_protocol_audit, resolve_split_audit, _path_from_env, _keyword_score, _select_candidate, iter_kaggle_dataset_roots, detect_kaggle_roots, resolve_wob_seed_input, discover_r5_wob_input_overrides, add_tree_to_tar | Python module. |
| `src/glitch_detection/wob_p0_audit.py` | WobP0Config, build_parser, sha256_file, load_csv_rows, load_json, detect_converter_scripts, detect_lance_outputs, resolve_source_path, source_exists, assert_safe_wob_root, build_manifest_rows, write_manifest_preview | Python module. |
| `src/glitch_detection/wob_protocol.py` | parse_wob_inventory, inspect_wob_episode_tar | Python module. |

## Scripts
| Script | Purpose | Related gate |
|---|---|---|
| `scripts/assemble_r5_wob_from_stages.py` | CLI/helper script. | general |
| `scripts/audit_gate6_tempglitch_source.py` | CLI/helper script. | general |
| `scripts/audit_lewm_research_source.py` | CLI/helper script. | Gate 5 |
| `scripts/audit_r5_xgame_split.py` | Audit an R5-XGame manifest and emit a machine-readable leakage report. | general |
| `scripts/build_lewm_lance_dataset.py` | CLI/helper script. | Gate 5 |
| `scripts/build_lewm_split.py` | CLI/helper script. | Gate 5 |
| `scripts/build_tempglitch_lewm_lance.py` | CLI/helper script. | Gate 5 |
| `scripts/build_tempglitch_validation_manifest.py` | CLI/helper script. | general |
| `scripts/build_wob_lewm_lance.py` | CLI/helper script. | Gate 5 |
| `scripts/check_claim_registry.py` | CLI/helper script. | general |
| `scripts/check_wob_kaggle_listing.py` | CLI/helper script. | Gate 5 |
| `scripts/convert_tempglitch_labels.py` | CLI/helper script. | general |
| `scripts/create_dynamics_test_dataset.py` | CLI/helper script. | general |
| `scripts/create_hard_dynamics_dataset.py` | CLI/helper script. | general |
| `scripts/create_test_dataset.py` | CLI/helper script. | general |
| `scripts/diagnose_kaggle_submission.py` | CLI/helper script. | Gate 5 |
| `scripts/doctor.py` | CLI/helper script. | general |
| `scripts/download_glitchbench_subset.py` | CLI/helper script. | general |
| `scripts/download_tempglitch.py` | CLI/helper script. | general |
| `scripts/evaluate_tempglitch_locked_test.py` | CLI/helper script. | general |
| `scripts/freeze_r5_xgame_split.py` | Freeze a deterministic, non-locked R5-XGame manifest from the WOB source split. | general |
| `scripts/freeze_tempglitch_protocol.py` | CLI/helper script. | general |
| `scripts/freeze_wob_protocol.py` | CLI/helper script. | general |
| `scripts/ingest_phase6e_kaggle_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/inspect_lewm_dataset.py` | CLI/helper script. | Gate 5 |
| `scripts/make_paper_tables.py` | CLI/helper script. | general |
| `scripts/plan_frozen_video_representation_baseline.py` | CLI/helper script. | general |
| `scripts/plot_lewm_surprise_timeline.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_lewm_gate6_package.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_lewm_gpu_profile_package.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_lewm_kaggle_package.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_lewm_r3_seed_run.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_phase6e_kaggle_dataset.py` | CLI/helper script. | Gate 5 |
| `scripts/prepare_wob_expansion_readiness.py` | Freeze the seed42 non-locked World of Bugs evaluation-readiness bundle. | general |
| `scripts/repair_kaggle_kernel_write_path.py` | CLI/helper script. | Gate 5 |
| `scripts/run_dynamics_experiments.py` | CLI/helper script. | general |
| `scripts/run_gate7_lance_scoring.py` | CLI/helper script. | general |
| `scripts/run_gate7_lewm_evaluation.py` | CLI/helper script. | Gate 5 |
| `scripts/run_gate8_baselines_from_lance.py` | CLI/helper script. | general |
| `scripts/run_gate9_ablations.py` | CLI/helper script. | general |
| `scripts/run_glitchbench_subset_experiments.py` | CLI/helper script. | general |
| `scripts/run_hard_dynamics_experiments.py` | CLI/helper script. | general |
| `scripts/run_kaggle_lewm.py` | CLI/helper script. | Gate 5 |
| `scripts/run_kaggle_parity_check.py` | CLI/helper script. | Gate 5 |
| `scripts/run_kaggle_video_autoencoder.py` | CLI/helper script. | Gate 5 |
| `scripts/run_lewm_gate6_automation.py` | CLI/helper script. | Gate 5 |
| `scripts/run_lewm_gpu_profile_automation.py` | CLI/helper script. | Gate 5 |
| `scripts/run_lewm_scoring.py` | CLI/helper script. | Gate 5 |
| `scripts/run_phase6e_kaggle_automation.py` | CLI/helper script. | Gate 5 |
| `scripts/run_r5_tempglitch_identical_episode_evaluation.py` | CLI/helper script. | general |
| `scripts/run_r5_wob_identical_episode_evaluation.py` | CLI/helper script. | general |
| `scripts/run_r5_wob_stage.py` | CLI/helper script. | general |
| `scripts/run_r5_xgame_comparison.py` | R5-XGAME: Cross-dataset comparison of TempGlitch R5 and WOB R5 results. | general |
| `scripts/run_r5_xgame_resume_missing_seed44.py` | Resume/finalize an R5-XGame run from a mounted partial output tree. | general |
| `scripts/run_r5_xgame_staged.py` | Fail-closed staged entrypoint for the four-role R5-XGame protocol. | general |
| `scripts/run_r6_tempglitch_ablations.py` | R6 TempGlitch ablation runner. | general |
| `scripts/run_r6_wob_ablations.py` | R6 WOB ablation runner. | general |
| `scripts/run_synthetic_demo.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_repeated_grouped_splits.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_smoke_test.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_split_experiments.py` | CLI/helper script. | general |
| `scripts/run_tempglitch_video_level_experiments.py` | CLI/helper script. | general |
| `scripts/run_wob_p0_materialization_audit.py` | CLI/helper script. | general |
| `scripts/run_worldofbugs_asset_demo.py` | CLI/helper script. | general |
| `scripts/select_tempglitch_protocol_config.py` | CLI/helper script. | general |
| `scripts/smoke_lewm_checkpoint.py` | CLI/helper script. | Gate 5 |
| `scripts/summarize_all_experiments.py` | CLI/helper script. | general |
| `scripts/update_context_cache.py` | CLI/helper script. | general |
| `scripts/validate_cloud_gpu_runtime.py` | CLI/helper script. | general |
| `scripts/validate_context_cache.py` | CLI/helper script. | general |
| `scripts/validate_lewm_gate6_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/validate_lewm_gpu_profile_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/validate_lewm_kaggle_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/validate_lewm_r3_seed_artifacts.py` | CLI/helper script. | Gate 5 |
| `scripts/validate_lewm_research_mvp_config.py` | CLI/helper script. | Gate 5 |
| `scripts/validate_r5_wob_evaluation.py` | CLI/helper script. | general |
| `scripts/validate_r5_wob_stage_outputs.py` | CLI/helper script. | general |

## Tests
| Test | Coverage |
|---|---|
| `tests/conftest.py` | conftest |
| `tests/test_analysis.py` | analysis |
| `tests/test_calibration.py` | calibration |
| `tests/test_check_wob_kaggle_listing.py` | check_wob_kaggle_listing |
| `tests/test_compare_experiments.py` | compare_experiments |
| `tests/test_context_cache.py` | context_cache |
| `tests/test_dataset_protocols.py` | dataset_protocols |
| `tests/test_dataset_report.py` | dataset_report |
| `tests/test_doctor.py` | doctor |
| `tests/test_evaluate.py` | evaluate |
| `tests/test_experiment_protocol.py` | experiment_protocol |
| `tests/test_failure_triage.py` | failure_triage |
| `tests/test_feature_distance.py` | feature_distance |
| `tests/test_frame_diff.py` | frame_diff |
| `tests/test_gate6_data.py` | gate6_data |
| `tests/test_gate7_lance_scoring.py` | gate7_lance_scoring |
| `tests/test_gate7_manifest.py` | gate7_manifest |
| `tests/test_gate8_baselines.py` | gate8_baselines |
| `tests/test_gate9_ablations.py` | gate9_ablations |
| `tests/test_imports.py` | imports |
| `tests/test_ingest_phase6e_kaggle_artifacts.py` | ingest_phase6e_kaggle_artifacts |
| `tests/test_kaggle_automation_foundation.py` | kaggle_automation_foundation |
| `tests/test_kaggle_automation_orchestrator.py` | kaggle_automation_orchestrator |
| `tests/test_kaggle_automation_validation.py` | kaggle_automation_validation |
| `tests/test_kaggle_governance.py` | kaggle_governance |
| `tests/test_kaggle_parity.py` | kaggle_parity |
| `tests/test_kaggle_runtime_environment.py` | kaggle_runtime_environment |
| `tests/test_kaggle_submission_diagnostics.py` | kaggle_submission_diagnostics |
| `tests/test_kaggle_video_autoencoder_runner.py` | kaggle_video_autoencoder_runner |
| `tests/test_leakage_aware_scorers.py` | leakage_aware_scorers |
| `tests/test_lewm_adapter.py` | lewm_adapter |
| `tests/test_lewm_data.py` | lewm_data |
| `tests/test_lewm_gate6.py` | lewm_gate6 |
| `tests/test_lewm_gate6_automation.py` | lewm_gate6_automation |
| `tests/test_lewm_gpu_profile.py` | lewm_gpu_profile |
| `tests/test_lewm_gpu_profile_automation.py` | lewm_gpu_profile_automation |
| `tests/test_lewm_gpu_profile_kaggle.py` | lewm_gpu_profile_kaggle |
| `tests/test_lewm_kaggle.py` | lewm_kaggle |
| `tests/test_lewm_lance_eval.py` | lewm_lance_eval |
| `tests/test_lewm_latent.py` | lewm_latent |
| `tests/test_lewm_protocol.py` | lewm_protocol |
| `tests/test_lewm_research.py` | lewm_research |
| `tests/test_lewm_research_mvp_config.py` | lewm_research_mvp_config |
| `tests/test_lewm_surprise.py` | lewm_surprise |
| `tests/test_lewm_training.py` | lewm_training |
| `tests/test_locked_test_gate.py` | locked_test_gate |
| `tests/test_manifest.py` | manifest |
| `tests/test_materialize_lance_stale_cleanup.py` | materialize_lance_stale_cleanup |
| `tests/test_mini_latent.py` | mini_latent |
| `tests/test_model_selection.py` | model_selection |
| `tests/test_neural_protocol.py` | neural_protocol |
| `tests/test_pairs.py` | pairs |
| `tests/test_phase6e_kaggle_automation_cli.py` | phase6e_kaggle_automation_cli |
| `tests/test_phase6e_kaggle_docs.py` | phase6e_kaggle_docs |
| `tests/test_post_r5_scaffold_gates.py` | post_r5_scaffold_gates |
| `tests/test_prepare_phase6e_kaggle_dataset.py` | prepare_phase6e_kaggle_dataset |
| `tests/test_preprocess.py` | preprocess |
| `tests/test_protocol_splits.py` | protocol_splits |
| `tests/test_r3_seed_runner.py` | r3_seed_runner |
| `tests/test_r5_tempglitch_eval.py` | r5_tempglitch_eval |
| `tests/test_r5_wob_eval.py` | r5_wob_eval |
| `tests/test_r5_wob_postrun.py` | r5_wob_postrun |
| `tests/test_r5_wob_script_entrypoints.py` | r5_wob_script_entrypoints |
| `tests/test_r5_wob_stage.py` | r5_wob_stage |
| `tests/test_r5_xgame_live.py` | r5_xgame_live |
| `tests/test_r5_xgame_metrics.py` | r5_xgame_metrics |
| `tests/test_r5_xgame_protocol.py` | r5_xgame_protocol |
| `tests/test_r5_xgame_resume_missing_seed44.py` | r5_xgame_resume_missing_seed44 |
| `tests/test_r5_xgame_runner.py` | r5_xgame_runner |
| `tests/test_repeated_eval.py` | repeated_eval |
| `tests/test_repeated_grouped_runner.py` | repeated_grouped_runner |
| `tests/test_research_release_tools.py` | research_release_tools |
| `tests/test_run_baseline.py` | run_baseline |
| `tests/test_run_kaggle_lewm.py` | run_kaggle_lewm |
| `tests/test_score_clips.py` | score_clips |
| `tests/test_splits.py` | splits |
| `tests/test_staged_install_completeness.py` | staged_install_completeness |
| `tests/test_statistics.py` | statistics |
| `tests/test_tempglitch.py` | tempglitch |
| `tests/test_tempglitch_split_runner.py` | tempglitch_split_runner |
| `tests/test_validate_r5_wob_evaluation.py` | validate_r5_wob_evaluation |
| `tests/test_validate_r5_xgame_output_bundle.py` | validate_r5_xgame_output_bundle |
| `tests/test_verify_wob_p0_kaggle_evidence.py` | verify_wob_p0_kaggle_evidence |
| `tests/test_video_autoencoder.py` | video_autoencoder |
| `tests/test_video_eval.py` | video_eval |
| `tests/test_wob_calibration_count_regression.py` | wob_calibration_count_regression |
| `tests/test_wob_expansion_readiness.py` | wob_expansion_readiness |
| `tests/test_wob_kaggle_native_common.py` | wob_kaggle_native_common |
| `tests/test_wob_kaggle_native_prepare.py` | wob_kaggle_native_prepare |
| `tests/test_wob_p0_audit.py` | wob_p0_audit |
| `tests/test_wob_p1_seed42_runner.py` | wob_p1_seed42_runner |
| `tests/test_wob_p1_seeds43_44_runner.py` | wob_p1_seeds43_44_runner |
| `tests/test_wob_protocol.py` | wob_protocol |
| `tests/test_wob_r5_runner.py` | wob_r5_runner |
| `tests/test_wob_seed_artifact_validator.py` | wob_seed_artifact_validator |

## Docs
| Doc | Purpose |
|---|---|
| `docs/agents/CLAUDE_OPUS_GITHUB_MASTER_PROMPT.md` | CLAUDE OPUS GITHUB MASTER PROMPT |
| `docs/context/BOOT.md` | BOOT |
| `docs/context/CONTEXT_POLICY.md` | CONTEXT POLICY |
| `docs/context/LAST_HANDOFF.md` | LAST HANDOFF |
| `docs/context/NEXT_ACTION.md` | NEXT ACTION |
| `docs/context/PROJECT_STATE.md` | PROJECT STATE |
| `docs/context/README.md` | README |
| `docs/context/REPO_MAP.md` | REPO MAP |
| `docs/context/TASK_ROUTER.md` | TASK ROUTER |
| `docs/plans/2026-06-12-gate7-to-gate9-lewm-evaluation.md` | 2026-06-12-gate7-to-gate9-lewm-evaluation |
| `docs/plans/2026-06-12-lewm-research-grade-experiment.md` | 2026-06-12-lewm-research-grade-experiment |
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
| `docs/research/44_gate5_cuda_smoke_validation.md` | 44 gate5 cuda smoke validation |
| `docs/research/45_gate6_lewm_normal_training_plan.md` | 45 gate6 lewm normal training plan |
| `docs/research/46_gate6_lewm_training_pilot_results.md` | 46 gate6 lewm training pilot results |
| `docs/research/47_gate7_lewm_surprise_scoring_results.md` | 47 gate7 lewm surprise scoring results |
| `docs/research/48_gate8_same_manifest_baseline_comparison.md` | 48 gate8 same manifest baseline comparison |
| `docs/research/49_gate9_minimal_ablation_results.md` | 49 gate9 minimal ablation results |
| `docs/research/50_results_claim_boundary.md` | 50 results claim boundary |
| `docs/research/52_r3_seed42_failed_p100_cuda_incompatibility.md` | 52 r3 seed42 failed p100 cuda incompatibility |
| `docs/research/53_r3_seed42_live_run_record.md` | 53 r3 seed42 live run record |
| `docs/research/54_r3_seed42_alternative_gpu_execution_plan.md` | 54 r3 seed42 alternative gpu execution plan |
| `docs/research/55_r3_seed42_cloud_run_record.md` | 55 r3 seed42 cloud run record |
| `docs/research/60_paper_claim_audit.md` | 60 paper claim audit |
| `docs/research/61_reproducibility_checklist.md` | 61 reproducibility checklist |
| `docs/research/62_artifact_manifest.md` | 62 artifact manifest |
| `docs/research/63_full_repo_audit_and_gate6_root_cause.md` | 63 full repo audit and gate6 root cause |
| `docs/research/64_kaggle_kernel_write_path_repair.md` | 64 kaggle kernel write path repair |
| `docs/research/65_lewm_research_mvp_source_audit.md` | 65 lewm research mvp source audit |
| `docs/research/66_lewm_gpu_profile_results.md` | 66 lewm gpu profile results |
| `docs/research/67_r3_r4_multiseed_status.md` | 67 r3 r4 multiseed status |
| `docs/research/68_r5_identical_episode_eval_plan.md` | 68 r5 identical episode eval plan |
| `docs/research/68_r5_tempglitch_and_wob_expansion_plan.md` | 68 r5 tempglitch and wob expansion plan |
| `docs/research/69_r5_tempglitch_identical_episode_results.md` | 69 r5 tempglitch identical episode results |
| `docs/research/70_paper_claim_map.md` | 70 paper claim map |
| `docs/research/70_wob_controlled_expansion_plan.md` | 70 wob controlled expansion plan |
| `docs/research/71_paper_source_matrix.md` | 71 paper source matrix |
| `docs/research/71_wob_p0_dataset_materialization_audit.md` | 71 wob p0 dataset materialization audit |
