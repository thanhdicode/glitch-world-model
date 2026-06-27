import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_validator_accepts_required_files_and_safe_tracked_paths(tmp_path: Path):
    validator = load_script("validate_research_release")
    context = load_script("update_context_cache")
    for relative in validator.REQUIRED_PATHS:
        path = tmp_path / relative
        if Path(relative).suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            content = (
                "\n".join(f"## {index}. Section {index}" for index in range(31)) + "\n"
                if relative == "PLAYBOOK.md"
                else "present\n"
            )
            path.write_text(content, encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(tmp_path / "docs/context")
    context.update_context_cache(tmp_path, refresh_boot=True)

    errors = validator.validate_release(
        tmp_path,
        tracked_files=["README.md", "src/glitch_detection/example.py"],
    )

    assert errors == []


def test_release_validator_requires_agent_governance_files(tmp_path: Path):
    validator = load_script("validate_research_release")

    expected = {
        "AGENTS.md",
        "PLAYBOOK.md",
        "RULES.md",
        "CLAUDE.md",
        "CONVENTIONS.md",
        ".aider.conf.yml",
        ".github/copilot-instructions.md",
        ".codex/skills",
        "docs/workflows/agent_task_template.md",
        "docs/workflows/kaggle_automation_policy.md",
        "docs/workflows/locked_test_release.md",
        "docs/workflows/artifact_policy.md",
        "docs/workflows/experiment_tracking.md",
        "docs/workflows/paper_claim_rules.md",
        "docs/workflows/runtime_management.md",
        "docs/workflows/security_checks.md",
        "docs/context/BOOT.md",
        "docs/context/PROJECT_STATE.md",
        "docs/context/NEXT_ACTION.md",
        "docs/context/LAST_HANDOFF.md",
        "docs/context/REPO_MAP.md",
        "docs/context/TASK_ROUTER.md",
        "docs/context/CONTEXT_POLICY.md",
        "docs/context/README.md",
    }

    assert expected <= set(validator.REQUIRED_PATHS)


def test_release_validator_requires_complete_playbook_structure(tmp_path: Path):
    validator = load_script("validate_research_release")
    playbook = tmp_path / "PLAYBOOK.md"
    playbook.write_text(
        "\n".join(f"## {index}. Section {index}" for index in range(31)) + "\n",
        encoding="utf-8",
    )

    errors = validator.validate_playbook_structure(playbook)

    assert errors == []


def test_release_validator_rejects_missing_playbook_section(tmp_path: Path):
    validator = load_script("validate_research_release")
    playbook = tmp_path / "PLAYBOOK.md"
    playbook.write_text(
        "\n".join(f"## {index}. Section {index}" for index in range(30)) + "\n",
        encoding="utf-8",
    )

    errors = validator.validate_playbook_structure(playbook)

    assert errors == ["PLAYBOOK.md missing required section: 30"]


@pytest.mark.parametrize(
    "tracked_path",
    [
        "checkpoints/model.pt",
        "models/model.pth",
        "runs/model.ckpt",
        "kaggle.json",
        ".env",
        "secrets/access_token.txt",
        "outputs/report.json",
        "data/raw/video.mp4",
        "data/processed/manifest.csv",
        "private_key.pem",
    ],
)
def test_release_validator_rejects_prohibited_tracked_paths(tmp_path: Path, tracked_path: str):
    validator = load_script("validate_research_release")

    errors = validator.validate_tracked_files([tracked_path])

    assert errors
    assert tracked_path in errors[0]


def test_release_validator_strict_check_detects_dirty_worktree(tmp_path: Path):
    validator = load_script("validate_research_release")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    errors = validator.working_tree_errors(tmp_path)

    assert errors == ["git working tree is not clean"]


def test_claim_registry_parser_reports_claim_ids_and_valid_statuses(tmp_path: Path):
    checker = load_script("check_claim_registry")
    registry = tmp_path / "claims.md"
    registry.write_text(
        "| ID | Claim | Type | Evidence | Status | Section | Notes |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        "| C-001 | A supported claim. | method | artifact.md | verified | Method | note |\n"
        "| C-002 | Planned experiment. | experiment | none | future-work | Future | note |\n",
        encoding="utf-8",
    )

    claims = checker.parse_claim_registry(registry)
    errors, warnings = checker.validate_claims(claims)

    assert [claim.claim_id for claim in claims] == ["C-001", "C-002"]
    assert errors == []
    assert warnings == []


def test_claim_registry_rejects_duplicate_ids_and_invalid_status(tmp_path: Path):
    checker = load_script("check_claim_registry")
    registry = tmp_path / "claims.md"
    registry.write_text(
        "| C-001 | First. | method | evidence.md | verified | Method | note |\n"
        "| C-001 | Second. | method | evidence.md | unsupported | Method | note |\n",
        encoding="utf-8",
    )

    errors, _warnings = checker.validate_claims(checker.parse_claim_registry(registry))

    assert any("duplicate claim ID: C-001" in error for error in errors)
    assert any("invalid status 'unsupported'" in error for error in errors)


def test_claim_registry_warns_when_verified_claim_has_no_evidence(tmp_path: Path):
    checker = load_script("check_claim_registry")
    registry = tmp_path / "claims.md"
    registry.write_text(
        "| C-001 | Claim. | experiment | none | verified | Results | note |\n",
        encoding="utf-8",
    )

    errors, warnings = checker.validate_claims(checker.parse_claim_registry(registry))

    assert errors == []
    assert warnings == ["C-001: verified claim has no evidence source"]


def test_paper_table_generator_writes_phase7_tables_from_artifact_fixtures(tmp_path: Path):
    generator = load_script("make_paper_tables")
    fixture_root = tmp_path / "fixture"
    output_root = tmp_path / "tables"

    (fixture_root / "outputs/tempglitch_followup_pair_disjoint").mkdir(parents=True)
    (fixture_root / "outputs/learned_baselines_k1/analysis").mkdir(parents=True)
    (fixture_root / "outputs/glitchbench_k2_intake").mkdir(parents=True)
    (fixture_root / "outputs/k3_ablation_intake").mkdir(parents=True)
    (fixture_root / "outputs/demo_timelines").mkdir(parents=True)
    (fixture_root / "docs/research").mkdir(parents=True)
    bundle_root = fixture_root / "external/k3_bundle"
    bundle_root.mkdir(parents=True)

    tempglitch_metrics = {
        "manifest_summary": {
            "calibration_episode_count": 2,
            "evaluation_normal_episode_count": 12,
            "evaluation_buggy_episode_count": 22,
        },
        "results": [
            {
                "method_family": "lewm",
                "method": "lewm",
                "window_scorer": "lewm_l2_max",
                "seed": "44",
                "episode_aggregation": "mean",
                "auroc": "0.715909090909",
                "auprc": "0.802619294928",
                "f1": "0.714285714286",
                "precision": "0.75",
                "recall": "0.681818181818",
                "balanced_accuracy": "0.632575757576",
                "fpr_at_95_tpr": "0.75",
                "auroc_ci_lower": "0.534943181818",
                "auroc_ci_upper": "0.877049910873",
                "f1_ci_lower": "0.585365853659",
                "f1_ci_upper": "0.829268292683",
            },
            {
                "method_family": "baseline",
                "method": "feature_distance",
                "window_scorer": "feature_distance",
                "seed": "",
                "episode_aggregation": "top2_mean",
                "auroc": "0.613636363636",
                "auprc": "0.731004353574",
                "f1": "0.16",
                "precision": "0.666666666667",
                "recall": "0.0909090909091",
                "balanced_accuracy": "0.503787878788",
                "fpr_at_95_tpr": "0.833333333333",
                "auroc_ci_lower": "0.463598484848",
                "auroc_ci_upper": "0.754545454545",
                "f1_ci_lower": "0",
                "f1_ci_upper": "0.357473544974",
            },
        ],
    }
    (fixture_root / "outputs/tempglitch_followup_pair_disjoint/followup_metrics.json").write_text(
        json.dumps(tempglitch_metrics),
        encoding="utf-8",
    )

    k1_summary = {
        "canonical_support": {
            "calibration_episode_count": 2,
            "evaluation_normal_episode_count": 12,
            "evaluation_buggy_episode_count": 22,
        },
        "best_lewm_row": tempglitch_metrics["results"][0],
        "best_frame_diff_row": {
            "method": "frame_diff",
            "episode_aggregation": "mean",
            "auroc": "0.583333333333",
            "auprc": "0.72156446442",
            "f1": "0.615384615385",
            "precision": "0.705882352941",
            "recall": "0.545454545455",
            "balanced_accuracy": "0.564393939394",
            "fpr_at_95_tpr": "0.75",
            "auroc_ci_lower": "0.418143939394",
            "auroc_ci_upper": "0.760337465565",
            "f1_ci_lower": "0.451612903226",
            "f1_ci_upper": "0.75",
        },
        "best_feature_distance_row": tempglitch_metrics["results"][1],
        "best_rows_by_method": {
            "video_autoencoder": {
                "method": "video_autoencoder",
                "episode_aggregation": "mean",
                "auroc": "0.560606060606",
                "auprc": "0.700531883605",
                "f1": "0.681818181818",
                "precision": "0.681818181818",
                "recall": "0.681818181818",
                "balanced_accuracy": "0.549242424242",
                "fpr_at_95_tpr": "0.833333333333",
                "auroc_ci_lower": "0.390890151515",
                "auroc_ci_upper": "0.738636363636",
                "f1_ci_lower": "0.555555555556",
                "f1_ci_upper": "0.790697674419",
            },
            "cnn_lstm": {
                "method": "cnn_lstm",
                "episode_aggregation": "max",
                "auroc": "0.613636363636",
                "auprc": "0.724853164636",
                "f1": "0.711111111111",
                "precision": "0.695652173913",
                "recall": "0.727272727273",
                "balanced_accuracy": "0.57196969697",
                "fpr_at_95_tpr": "0.916666666667",
                "auroc_ci_lower": "0.440454545455",
                "auroc_ci_upper": "0.800041322314",
                "f1_ci_lower": "0.594594594595",
                "f1_ci_upper": "0.816326530612",
            },
            "video_transformer": {
                "method": "video_transformer",
                "episode_aggregation": "mean",
                "auroc": "0.590909090909",
                "auprc": "0.775551078589",
                "f1": "0.24",
                "precision": "1",
                "recall": "0.136363636364",
                "balanced_accuracy": "0.568181818182",
                "fpr_at_95_tpr": "1",
                "auroc_ci_lower": "0.461515151515",
                "auroc_ci_upper": "0.727272727273",
                "f1_ci_lower": "0",
                "f1_ci_upper": "0.428571428571",
            },
        },
    }
    (fixture_root / "outputs/learned_baselines_k1/analysis/k1_followup_summary.json").write_text(
        json.dumps(k1_summary),
        encoding="utf-8",
    )

    k2_summary = {
        "results": [
            {
                "method": "frame_diff",
                "aggregation": "",
                "auroc": "0.5",
                "auprc": "0.5",
                "f1": "0.6666666666666666",
                "balanced_accuracy": "0.5",
                "fpr_at_95_tpr": "1.0",
            },
            {
                "method": "feature_distance",
                "aggregation": "",
                "auroc": "1.0",
                "auprc": "1.0",
                "f1": "0.6666666666666666",
                "balanced_accuracy": "0.5",
                "fpr_at_95_tpr": "0.0",
            },
            {
                "method": "video_autoencoder",
                "aggregation": "",
                "auroc": "1.0",
                "auprc": "1.0",
                "f1": "0.6666666666666666",
                "balanced_accuracy": "0.5",
                "fpr_at_95_tpr": "0.0",
            },
            {
                "method": "cnn_lstm",
                "aggregation": "",
                "auroc": "1.0",
                "auprc": "1.0",
                "f1": "0.6666666666666666",
                "balanced_accuracy": "0.5",
                "fpr_at_95_tpr": "0.0",
            },
            {
                "method": "video_transformer",
                "aggregation": "",
                "auroc": "1.0",
                "auprc": "1.0",
                "f1": "0.6666666666666666",
                "balanced_accuracy": "0.5",
                "fpr_at_95_tpr": "0.0",
            },
        ],
        "best_lewm_row": {
            "auroc": "0.5",
            "auprc": "0.7191499004428067",
            "f1": "0.4",
            "balanced_accuracy": "0.25",
            "fpr_at_95_tpr": "1.0",
        },
        "bundle_validation": {"split_summary": {"validation_source_count": 24}},
    }
    (fixture_root / "outputs/glitchbench_k2_intake/k2_glitchbench_intake_summary.json").write_text(
        json.dumps(k2_summary),
        encoding="utf-8",
    )

    k3_summary = {"bundle_root": str(bundle_root)}
    (fixture_root / "outputs/k3_ablation_intake/k3_ablation_intake_summary.json").write_text(
        json.dumps(k3_summary),
        encoding="utf-8",
    )
    (fixture_root / "docs/research/126_k3_sigreg_action_ablation_results.md").write_text(
        "# placeholder\n",
        encoding="utf-8",
    )

    def write_validation_history(path: Path, prediction_means: list[float]):
        path.parent.mkdir(parents=True, exist_ok=True)
        history = []
        for index, prediction_mean in enumerate(prediction_means, start=1):
            history.append(
                {
                    "update": index * 100,
                    "batches": [
                        {
                            "prediction_loss": prediction_mean,
                            "sigreg_loss": 0.0,
                            "loss": prediction_mean,
                        }
                    ],
                }
            )
        path.write_text(json.dumps(history), encoding="utf-8")

    variant_defs = {
        "seed42_sigreg_off_real_action": (42, False, "real", 0.001100, [0.020000, 0.001100]),
        "seed42_sigreg_off_zero_action": (42, False, "zero_action", 0.001000, [0.020000, 0.001000]),
        "seed42_sigreg_on_real_action": (42, True, "real", 0.280000, [0.017660, 0.050000]),
        "seed42_sigreg_on_zero_action": (42, True, "zero_action", 0.284000, [0.020388, 0.060000]),
        "seed43_sigreg_off_real_action": (43, False, "real", 0.001200, [0.020000, 0.001200]),
        "seed43_sigreg_off_zero_action": (43, False, "zero_action", 0.001100, [0.020000, 0.001100]),
        "seed43_sigreg_on_real_action": (43, True, "real", 0.281000, [0.021877, 0.070000]),
        "seed43_sigreg_on_zero_action": (43, True, "zero_action", 0.285000, [0.018409, 0.080000]),
        "seed44_sigreg_off_real_action": (44, False, "real", 0.001243, [0.020000, 0.001243]),
        "seed44_sigreg_off_zero_action": (44, False, "zero_action", 0.001125, [0.020000, 0.001125]),
        "seed44_sigreg_on_real_action": (44, True, "real", 0.279711, [0.019627, 0.090000]),
        "seed44_sigreg_on_zero_action": (44, True, "zero_action", 0.283585, [0.016671, 0.050000]),
    }
    executed_variants = []
    for name, (
        seed,
        sigreg_enabled,
        action_mode,
        best_validation_loss,
        prediction_means,
    ) in variant_defs.items():
        write_validation_history(bundle_root / name / "validation_history.json", prediction_means)
        executed_variants.append(
            {
                "variant_name": name,
                "seed": seed,
                "training_metadata": {
                    "best_validation_loss": best_validation_loss,
                    "sigreg_enabled": sigreg_enabled,
                    "action_mode": action_mode,
                },
            }
        )

    controlled_pairs = [
        {
            "pair_type": "sigreg",
            "seed": 42,
            "control_variant": "seed42_sigreg_off_real_action",
            "treatment_variant": "seed42_sigreg_on_real_action",
            "action_mode": "real",
        },
        {
            "pair_type": "sigreg",
            "seed": 42,
            "control_variant": "seed42_sigreg_off_zero_action",
            "treatment_variant": "seed42_sigreg_on_zero_action",
            "action_mode": "zero_action",
        },
        {
            "pair_type": "action_conditioning",
            "seed": 42,
            "control_variant": "seed42_sigreg_on_zero_action",
            "treatment_variant": "seed42_sigreg_on_real_action",
            "sigreg_enabled": True,
        },
        {
            "pair_type": "action_conditioning",
            "seed": 42,
            "control_variant": "seed42_sigreg_off_zero_action",
            "treatment_variant": "seed42_sigreg_off_real_action",
            "sigreg_enabled": False,
        },
        {
            "pair_type": "sigreg",
            "seed": 43,
            "control_variant": "seed43_sigreg_off_real_action",
            "treatment_variant": "seed43_sigreg_on_real_action",
            "action_mode": "real",
        },
        {
            "pair_type": "sigreg",
            "seed": 43,
            "control_variant": "seed43_sigreg_off_zero_action",
            "treatment_variant": "seed43_sigreg_on_zero_action",
            "action_mode": "zero_action",
        },
        {
            "pair_type": "action_conditioning",
            "seed": 43,
            "control_variant": "seed43_sigreg_on_zero_action",
            "treatment_variant": "seed43_sigreg_on_real_action",
            "sigreg_enabled": True,
        },
        {
            "pair_type": "action_conditioning",
            "seed": 43,
            "control_variant": "seed43_sigreg_off_zero_action",
            "treatment_variant": "seed43_sigreg_off_real_action",
            "sigreg_enabled": False,
        },
        {
            "pair_type": "sigreg",
            "seed": 44,
            "control_variant": "seed44_sigreg_off_real_action",
            "treatment_variant": "seed44_sigreg_on_real_action",
            "action_mode": "real",
        },
        {
            "pair_type": "sigreg",
            "seed": 44,
            "control_variant": "seed44_sigreg_off_zero_action",
            "treatment_variant": "seed44_sigreg_on_zero_action",
            "action_mode": "zero_action",
        },
        {
            "pair_type": "action_conditioning",
            "seed": 44,
            "control_variant": "seed44_sigreg_on_zero_action",
            "treatment_variant": "seed44_sigreg_on_real_action",
            "sigreg_enabled": True,
        },
        {
            "pair_type": "action_conditioning",
            "seed": 44,
            "control_variant": "seed44_sigreg_off_zero_action",
            "treatment_variant": "seed44_sigreg_off_real_action",
            "sigreg_enabled": False,
        },
    ]
    (bundle_root / "r6_ablation_receipt.json").write_text(
        json.dumps(
            {
                "executed_variants": executed_variants,
                "controlled_pairs": controlled_pairs,
            }
        ),
        encoding="utf-8",
    )

    qualitative_receipt = {
        "selected_config": {
            "seed": "44",
            "window_scorer": "lewm_l2_max",
            "episode_aggregation": "mean",
        },
        "plots": [
            {
                "label": "Buggy",
                "category": "Frozen Animation",
                "source_episode_id": "Buggy_Episode_01",
                "window_count": 1088,
                "episode_score": 1.69640564535,
            },
            {
                "label": "Normal",
                "category": "Shooting Error",
                "source_episode_id": "Normal_Episode_01",
                "window_count": 1408,
                "episode_score": 1.20580431428,
            },
        ],
    }
    (fixture_root / "outputs/demo_timelines/qualitative_timeline_receipt.json").write_text(
        json.dumps(qualitative_receipt),
        encoding="utf-8",
    )

    written = generator.write_tables(output_root, root=fixture_root)

    assert {path.name for path in written} == {
        "r5_bounded_results.tex",
        "k1_learned_baselines.tex",
        "glitchbench_benchmark.tex",
        "k3_ablation_results.tex",
        "qualitative_timeline_summary.tex",
    }
    assert "0.7159" in (output_root / "r5_bounded_results.tex").read_text(encoding="utf-8")
    assert "cnn\\_lstm" in (output_root / "k1_learned_baselines.tex").read_text(encoding="utf-8")
    assert "feature\\_distance" in (output_root / "glitchbench_benchmark.tex").read_text(
        encoding="utf-8"
    )
    k3_text = (output_root / "k3_ablation_results.tex").read_text(encoding="utf-8")
    assert "+0.016560" in k3_text
    assert "Panel C: real-action minus zero-action prediction-loss delta" in k3_text
    qualitative = (output_root / "qualitative_timeline_summary.tex").read_text(encoding="utf-8")
    assert "No temporal-localization metric is claimed" in qualitative
