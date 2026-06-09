import json
from pathlib import Path

from PIL import Image

from glitch_detection.manifest import ClipRecord, write_manifest
from scripts.run_tempglitch_repeated_grouped_splits import run_repeated_grouped_experiments


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    metadata_path = tmp_path / "metadata.csv"
    labels_path = tmp_path / "labels.csv"
    manifest_path = tmp_path / "manifest.csv"
    metadata_lines = ["row_idx,category,public_label,source,dataset_revision,sample_mode,seed"]
    label_lines = ["source,start_frame,end_frame,label"]
    records = []
    row_idx = 0
    for index in range(1, 6):
        for public_label in ["Buggy", "Normal"]:
            source = f"Godot_Blinking_{public_label}_{index}"
            clip_dir = tmp_path / "clips" / source
            clip_dir.mkdir(parents=True)
            values = [0, 100, 0] if public_label == "Buggy" else [index, index + 1, index + 2]
            for frame_index, value in enumerate(values):
                Image.new("RGB", (4, 4), color=(value, value, value)).save(
                    clip_dir / f"{frame_index:03d}.png"
                )
            records.append(ClipRecord(f"{source}_0", source, str(clip_dir), 0, 2, 3, 30.0))
            metadata_lines.append(
                f"{row_idx},Blinking,{public_label},{source},revision,sequential,42"
            )
            if public_label == "Buggy":
                label_lines.append(f"{source},0,2,1")
            row_idx += 1
    metadata_path.write_text("\n".join(metadata_lines) + "\n", encoding="utf-8")
    labels_path.write_text("\n".join(label_lines) + "\n", encoding="utf-8")
    write_manifest(manifest_path, records)
    return metadata_path, manifest_path, labels_path


def test_repeated_grouped_dry_run_writes_zero_leakage_audit(tmp_path: Path):
    metadata_path, manifest_path, labels_path = _write_fixture(tmp_path)

    summary = run_repeated_grouped_experiments(
        metadata_path=metadata_path,
        manifest_path=manifest_path,
        labels_path=labels_path,
        output_root=tmp_path / "outputs",
        seeds=[42, 43],
        scorers=["frame_diff"],
        aggregations=["mean"],
        n_bootstrap=10,
        dry_run=True,
        declared_sample_mode="sequential",
    )

    assert summary["status"] == "dry-run only"
    assert summary["dataset"]["sample_mode_source"] == "declared-protocol"
    assert summary["seeds_completed"] == [42, 43]
    assert all(row["cross_split_group_count"] == 0 for row in summary["runs"])
    assert (tmp_path / "outputs" / "seed_42" / "split_metadata.json").is_file()
    assert (tmp_path / "outputs" / "seed_42" / "leakage_report.json").is_file()


def test_full_repeated_run_selects_before_testing_and_writes_one_test_score_file(tmp_path: Path):
    metadata_path, manifest_path, labels_path = _write_fixture(tmp_path)
    stale_path = tmp_path / "outputs" / "seed_42" / "test_scores" / "stale_scores.csv"
    stale_path.parent.mkdir(parents=True)
    stale_path.write_text("score\n1\n", encoding="utf-8")

    summary = run_repeated_grouped_experiments(
        metadata_path=metadata_path,
        manifest_path=manifest_path,
        labels_path=labels_path,
        output_root=tmp_path / "outputs",
        seeds=[42],
        scorers=["frame_diff", "feature_distance", "mini_latent"],
        aggregations=["mean", "max"],
        n_bootstrap=20,
        dry_run=False,
    )

    seed_dir = tmp_path / "outputs" / "seed_42"
    selected = json.loads((seed_dir / "selected_protocol_config.json").read_text(encoding="utf-8"))
    locked = json.loads((seed_dir / "locked_test_metrics_with_ci.json").read_text(encoding="utf-8"))
    fit_metadata = json.loads((seed_dir / "fit_metadata.json").read_text(encoding="utf-8"))

    assert summary["status"] == "full run complete"
    assert summary["dataset"]["sample_modes"] == ["sequential"]
    assert summary["dataset"]["dataset_revisions"] == ["revision"]
    assert selected["selection_split"] == "validation"
    assert selected["validation_candidate_count"] == 6
    assert locked["evaluated_config_count"] == 1
    assert len(list((seed_dir / "test_scores").glob("*_scores.csv"))) == 1
    assert all(item["fit_split"] in {"none", "train"} for item in fit_metadata)
    assert locked["confidence_intervals"]["auroc"]["n_bootstrap"] == 20
    assert locked["confidence_intervals"]["auroc"]["group_key"] == "pair_id_heuristic"
    assert locked["confidence_intervals"]["auroc"]["confidence_level"] == 0.95
    repeated_markdown = (tmp_path / "outputs" / "phase6d_repeated_summary.md").read_text(
        encoding="utf-8"
    )
    assert "AUROC 95% CI" in repeated_markdown
    assert "selected-pipeline performance" in repeated_markdown
