from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.ingest_k2_glitchbench_benchmark import (
    ingest_k2_glitchbench_benchmark,
    locate_bundle_root,
)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _manifest_rows(prefix: str, count: int) -> list[dict[str, str]]:
    return [
        {
            "clip_id": f"{prefix}_clip_{index}",
            "source": f"{prefix}_source_{index}",
            "clip_dir": f"/tmp/{prefix}_{index}",
            "start_frame": "0",
            "end_frame": "7",
            "frame_count": "8",
            "fps": "1.0",
        }
        for index in range(count)
    ]


def _score_rows(prefix: str, count: int, *, score: float) -> list[dict[str, str]]:
    return [
        {
            "clip_id": f"{prefix}_clip_{index}",
            "source": f"{prefix}_source_{index}",
            "clip_dir": f"/tmp/{prefix}_{index}",
            "start_frame": "0",
            "end_frame": "7",
            "score": f"{score + index * 0.01:.6f}",
        }
        for index in range(count)
    ]


def _bundle_root(tmp_path: Path) -> Path:
    bundle_root = tmp_path / "download" / "glitchbench_k2"
    train_count = 2
    validation_count = 4
    train_rows = _manifest_rows("train", train_count)
    validation_rows = _manifest_rows("validation", validation_count)

    _write_csv(bundle_root / "train_normal_manifest.csv", train_rows)
    _write_csv(bundle_root / "validation_manifest.csv", validation_rows)
    (bundle_root / "bundle_validation.json").write_text(
        json.dumps(
            {
                "status": "validated",
                "manifest_summary": {
                    "record_count": train_count + validation_count,
                    "image_level_only": True,
                    "temporal_label_available": False,
                    "locked_test_materialized": False,
                    "locked_test_scored": False,
                },
                "split_summary": {
                    "train_source_count": train_count,
                    "validation_source_count": validation_count,
                    "test_source_count": 0,
                    "leakage_audit": {"cross_split_group_count": 0},
                    "locked_test_materialized": False,
                    "locked_test_scored": False,
                },
                "locked_test_materialized": False,
                "locked_test_scored": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (bundle_root / "lewm_artifact_validation.json").write_text(
        json.dumps(
            {
                "artifact_root": "/kaggle/input/lewm-k2-lewm-seed-artifacts",
                "seeds": [
                    {
                        "seed": seed,
                        "seed_root": f"/kaggle/input/seed{seed}",
                        "checkpoint_path": f"/kaggle/input/seed{seed}/best_weights.pt",
                        "config_path": f"/kaggle/input/seed{seed}/config.json",
                        "checkpoint_sha256": f"checkpoint-{seed}",
                        "config_sha256": "config",
                        "aggregations": ["mean", "max"],
                        "checkpoint_sha256_sidecar": f"checkpoint-{seed}",
                    }
                    for seed in (42, 43, 44)
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    metrics_rows = [
        {
            "method": "frame_diff",
            "seed": "",
            "aggregation": "",
            "threshold": "0.0",
            "threshold_source": "train_normal_p95",
            "auroc": "0.5",
            "auprc": "0.5",
            "f1": "0.6666666666666666",
            "precision": "0.5",
            "recall": "1.0",
            "balanced_accuracy": "0.5",
            "fpr_at_95_tpr": "1.0",
            "auroc_ci_lower": "0.5",
            "auroc_ci_upper": "0.5",
            "f1_ci_lower": "0.4",
            "f1_ci_upper": "0.8",
            "validation_count": str(validation_count),
            "locked_test_materialized": "False",
            "locked_test_scored": "False",
        },
        {
            "method": "feature_distance",
            "seed": "",
            "aggregation": "",
            "threshold": "0.1",
            "threshold_source": "train_normal_p95",
            "auroc": "1.0",
            "auprc": "1.0",
            "f1": "0.6666666666666666",
            "precision": "0.5",
            "recall": "1.0",
            "balanced_accuracy": "0.5",
            "fpr_at_95_tpr": "0.0",
            "auroc_ci_lower": "1.0",
            "auroc_ci_upper": "1.0",
            "f1_ci_lower": "0.4",
            "f1_ci_upper": "0.8",
            "validation_count": str(validation_count),
            "locked_test_materialized": "False",
            "locked_test_scored": "False",
        },
    ]
    for method in ("video_autoencoder", "cnn_lstm", "video_transformer"):
        metrics_rows.append(
            {
                "method": method,
                "seed": "",
                "aggregation": "",
                "threshold": "0.1",
                "threshold_source": "train_normal_p95",
                "auroc": "1.0",
                "auprc": "1.0",
                "f1": "0.6666666666666666",
                "precision": "0.5",
                "recall": "1.0",
                "balanced_accuracy": "0.5",
                "fpr_at_95_tpr": "0.0",
                "auroc_ci_lower": "1.0",
                "auroc_ci_upper": "1.0",
                "f1_ci_lower": "0.4",
                "f1_ci_upper": "0.8",
                "validation_count": str(validation_count),
                "locked_test_materialized": "False",
                "locked_test_scored": "False",
            }
        )
    for seed, mean_auroc, max_auroc in ((42, 0.5, 0.45), (43, 0.4, 0.35), (44, 0.45, 0.4)):
        for aggregation, auroc in (("mean", mean_auroc), ("max", max_auroc)):
            metrics_rows.append(
                {
                    "method": "lewm",
                    "seed": str(seed),
                    "aggregation": aggregation,
                    "threshold": "0.2",
                    "threshold_source": "train_normal_p95",
                    "auroc": str(auroc),
                    "auprc": str(0.6 + auroc / 10),
                    "f1": "0.4",
                    "precision": "0.3333333333333333",
                    "recall": "0.5",
                    "balanced_accuracy": "0.25",
                    "fpr_at_95_tpr": "1.0",
                    "auroc_ci_lower": "0.2",
                    "auroc_ci_upper": "0.7",
                    "f1_ci_lower": "0.1",
                    "f1_ci_upper": "0.6",
                    "validation_count": str(validation_count),
                    "locked_test_materialized": "False",
                    "locked_test_scored": "False",
                }
            )
    _write_csv(bundle_root / "glitchbench_benchmark_metrics.csv", metrics_rows)

    summary = {
        "status": "k2_complete_lewm_and_baselines",
        "train_normal_clip_count": train_count,
        "validation_clip_count": validation_count,
        "device": "cuda",
        "baseline_only": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "lewm_aggregations": ["mean", "max"],
        "bundle_validation": json.loads((bundle_root / "bundle_validation.json").read_text()),
        "claim_boundary": "bounded",
        "simple_results": metrics_rows[:2],
        "learned_results": metrics_rows[2:5],
        "lewm_results": metrics_rows[5:],
    }
    (bundle_root / "glitchbench_benchmark_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    for baseline_name in (
        "frame_diff",
        "feature_distance",
        "video_autoencoder",
        "cnn_lstm",
        "video_transformer",
    ):
        _write_csv(
            bundle_root / f"{baseline_name}_train_scores.csv",
            _score_rows("train", train_count, score=0.1),
        )
        _write_csv(
            bundle_root / f"{baseline_name}_validation_scores.csv",
            _score_rows("validation", validation_count, score=0.2),
        )
    for baseline_name in ("video_autoencoder", "cnn_lstm", "video_transformer"):
        (bundle_root / f"{baseline_name}.pt").write_text("checkpoint\n", encoding="utf-8")
        (bundle_root / f"{baseline_name}_training_metadata.json").write_text(
            json.dumps({"method": baseline_name}, indent=2),
            encoding="utf-8",
        )
    for seed in (42, 43, 44):
        seed_dir = bundle_root / "lewm" / f"seed{seed}"
        for aggregation in ("mean", "max"):
            _write_csv(
                seed_dir / f"lewm_seed{seed}_{aggregation}_train_scores.csv",
                _score_rows("train", train_count, score=0.3),
            )
            _write_csv(
                seed_dir / f"lewm_seed{seed}_{aggregation}_validation_scores.csv",
                _score_rows("validation", validation_count, score=0.4),
            )
            (seed_dir / f"lewm_seed{seed}_{aggregation}_train_scores_metadata.json").write_text(
                json.dumps({"seed": seed, "aggregation": aggregation}, indent=2),
                encoding="utf-8",
            )
            (
                seed_dir / f"lewm_seed{seed}_{aggregation}_validation_scores_metadata.json"
            ).write_text(
                json.dumps({"seed": seed, "aggregation": aggregation}, indent=2),
                encoding="utf-8",
            )
    return bundle_root


def test_locate_bundle_root_finds_nested_extract_root(tmp_path: Path):
    bundle_root = _bundle_root(tmp_path)

    located = locate_bundle_root(tmp_path / "download")

    assert located == bundle_root


def test_ingest_k2_glitchbench_benchmark_summarizes_bundle(tmp_path: Path):
    bundle_root = _bundle_root(tmp_path)
    tarball_path = tmp_path / "glitchbench_k2_outputs.tar.gz"
    tarball_path.write_text("fake tarball\n", encoding="utf-8")
    sidecar_path = tmp_path / "glitchbench_k2_outputs.tar.gz.sha256"
    sidecar_path.write_text(
        f"{tarball_path.read_bytes().hex()}  /kaggle/working/glitchbench_k2_outputs.tar.gz\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="tarball SHA256 does not match"):
        ingest_k2_glitchbench_benchmark(
            bundle_root=bundle_root,
            output_dir=tmp_path / "intake",
            tarball_path=tarball_path,
            tarball_sha256_sidecar_path=sidecar_path,
        )


def test_ingest_k2_glitchbench_benchmark_accepts_matching_tarball_sidecar(tmp_path: Path):
    bundle_root = _bundle_root(tmp_path)
    tarball_path = tmp_path / "glitchbench_k2_outputs.tar.gz"
    tarball_path.write_text("fake tarball\n", encoding="utf-8")

    digest = hashlib.sha256(tarball_path.read_bytes()).hexdigest()
    sidecar_path = tmp_path / "glitchbench_k2_outputs.tar.gz.sha256"
    sidecar_path.write_text(
        f"{digest}  /kaggle/working/glitchbench_k2_outputs.tar.gz\n",
        encoding="utf-8",
    )

    summary = ingest_k2_glitchbench_benchmark(
        bundle_root=bundle_root,
        output_dir=tmp_path / "intake",
        tarball_path=tarball_path,
        tarball_sha256_sidecar_path=sidecar_path,
    )

    assert summary["status"] == "k2_glitchbench_bundle_ingested"
    assert summary["best_simple_row"]["method"] == "feature_distance"
    assert summary["best_learned_row"]["method"] == "video_autoencoder"
    assert summary["best_lewm_aggregation"] == "mean"
    assert summary["top_method_names"] == [
        "feature_distance",
        "video_autoencoder",
        "cnn_lstm",
        "video_transformer",
    ]
