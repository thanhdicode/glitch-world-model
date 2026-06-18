from __future__ import annotations

import csv
import json
import sys
import tarfile
from importlib import util
from pathlib import Path

from cloud.wob_p1_seed42.common import (
    build_p1_selected_rows,
    package_artifacts,
    write_selected_split_csv,
)


def _load_preflight_robust():
    path = Path(__file__).resolve().parents[1] / "cloud" / "wob_p1_seed42" / "preflight_robust.py"
    spec = util.spec_from_file_location("wob_p1_preflight_robust", path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_finalize_artifacts():
    path = Path(__file__).resolve().parents[1] / "cloud" / "wob_p1_seed42" / "finalize_artifacts.py"
    spec = util.spec_from_file_location("wob_p1_finalize_artifacts", path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_split(path: Path) -> None:
    rows = [
        {
            "dataset_id": "normal",
            "source": "NORMAL-TRAIN/ep-0000/ep-0000.tar",
            "episode_id": "normal/ep-0000",
            "pair_id": "normal/ep-0000",
            "category": "Normal",
            "label": "Normal",
            "split": "train",
            "action_mode": "real",
            "use_for_training": "True",
            "materialize": "True",
        },
        {
            "dataset_id": "normal",
            "source": "NORMAL-TRAIN/ep-0001/ep-0001.tar",
            "episode_id": "normal/ep-0001",
            "pair_id": "normal/ep-0001",
            "category": "Normal",
            "label": "Normal",
            "split": "validation",
            "action_mode": "real",
            "use_for_training": "False",
            "materialize": "True",
        },
        {
            "dataset_id": "buggy",
            "source": "TEST/Bug/ep-0000/ep-0000.tar",
            "episode_id": "Bug/ep-0000",
            "pair_id": "Bug/ep-0000",
            "category": "Bug",
            "label": "Buggy",
            "split": "validation",
            "action_mode": "real",
            "use_for_training": "False",
            "materialize": "True",
        },
        {
            "dataset_id": "buggy",
            "source": "TEST/Bug/ep-0001/ep-0001.tar",
            "episode_id": "Bug/ep-0001",
            "pair_id": "Bug/ep-0001",
            "category": "Bug",
            "label": "Buggy",
            "split": "test",
            "action_mode": "real",
            "use_for_training": "False",
            "materialize": "False",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_p1_selection_excludes_validation_buggy_and_locked_rows(tmp_path: Path):
    split_csv = tmp_path / "split.csv"
    _write_split(split_csv)
    rows = list(csv.DictReader(split_csv.open("r", newline="", encoding="utf-8")))
    selected, summary = build_p1_selected_rows(rows)
    assert [row["source"] for row in selected] == [
        "NORMAL-TRAIN/ep-0000/ep-0000.tar",
        "NORMAL-TRAIN/ep-0001/ep-0001.tar",
    ]
    assert summary["train_normal_count"] == 1
    assert summary["validation_normal_count"] == 1
    assert summary["validation_buggy_excluded_count"] == 1
    assert summary["locked_rows_skipped"] == 1


def test_write_selected_split_csv_writes_only_p1_normal_rows(tmp_path: Path):
    split_csv = tmp_path / "split.csv"
    selected_csv = tmp_path / "selected.csv"
    _write_split(split_csv)
    summary = write_selected_split_csv(split_csv, selected_csv)
    selected_rows = list(csv.DictReader(selected_csv.open("r", newline="", encoding="utf-8")))
    assert len(selected_rows) == 2
    assert all(row["label"] == "Normal" for row in selected_rows)
    assert summary["validation_buggy_excluded_count"] == 1


def test_package_artifacts_excludes_raw_tar_files(tmp_path: Path):
    root = tmp_path / "artifact_root"
    root.mkdir()
    (root / "training_metadata.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (root / "raw.tar").write_text("raw", encoding="utf-8")
    archive = tmp_path / "artifacts.tar.gz"
    package_artifacts(archive, [(root, "artifact_root")])
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert "artifact_root/training_metadata.json" in names
    assert "artifact_root/raw.tar" not in names


def test_wob_p1_readme_contains_one_section_kaggle_command():
    readme = (
        Path(__file__).resolve().parents[1] / "cloud" / "wob_p1_seed42" / "README.md"
    ).read_text(encoding="utf-8")
    assert "run_kaggle_wob_p1_seed42_all.sh" in readme
    assert "%%bash" in readme


def test_wob_p1_preflight_checks_reject_sm60_runtime():
    script = (
        Path(__file__).resolve().parents[1] / "cloud" / "wob_p1_seed42" / "preflight.sh"
    ).read_text(encoding="utf-8")
    assert "--min-compute-major 7" in script
    assert "--min-vram-gb 14" in script


def test_robust_preflight_uses_total_memory_cuda_property(monkeypatch):
    module = _load_preflight_robust()

    class _Props:
        total_memory = 16 * 1024**3

    class _FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def device_count():
            return 1

        @staticmethod
        def get_device_properties(index):
            return _Props()

        @staticmethod
        def get_device_capability(index):
            return (7, 5)

        @staticmethod
        def get_device_name(index):
            return "Tesla T4"

    class _FakeTorch:
        __version__ = "fake"
        cuda = _FakeCuda()

    monkeypatch.setitem(sys.modules, "torch", _FakeTorch())

    report = module._check_cuda()

    assert report["ok"] is True
    assert report["vram_bytes"] == 16 * 1024**3
    assert report["gpus"][0]["vram_gb"] == 16.0


def test_robust_preflight_detects_nested_kaggle_inputs(tmp_path: Path):
    module = _load_preflight_robust()
    base = tmp_path / "kaggle" / "input" / "datasets" / "benedictwilkinsai"
    (base / "world-of-bugs-normal" / "NORMAL-TRAIN").mkdir(parents=True)
    (base / "world-of-bugs-test" / "TEST").mkdir(parents=True)

    report = module._check_kaggle_inputs(str(tmp_path / "kaggle" / "input"))

    assert report["ok"] is True
    assert report["normal_input_root"].endswith("world-of-bugs-normal")
    assert report["test_input_root"].endswith("world-of-bugs-test")


def test_finalize_removes_stale_failure_debug_after_success(tmp_path: Path):
    module = _load_finalize_artifacts()
    output_root = tmp_path / "out"
    metadata_root = tmp_path / "meta"
    log_dir = tmp_path / "logs"
    output_root.mkdir()
    metadata_root.mkdir()
    log_dir.mkdir()
    (output_root / "training_metadata.json").write_text(
        json.dumps(
            {
                "status": "research_update_run_complete_unvalidated",
                "updates_completed": 4000,
                "best_validation_loss": 0.6093359693480057,
            }
        ),
        encoding="utf-8",
    )
    (output_root / "validator_report.json").write_text(
        json.dumps({"status": "wob_seed42_validated"}),
        encoding="utf-8",
    )
    stale_debug = tmp_path / "wob_seed42_failure_debug.tar.gz"
    stale_debug.write_bytes(b"stale")

    manifest = module.finalize(
        str(output_root),
        str(metadata_root),
        str(log_dir),
        str(tmp_path / "wob_seed42_artifacts.tar.gz"),
        failure_debug_path=str(stale_debug),
    )

    assert manifest["stale_failure_debug_removed"] is True
    assert not stale_debug.exists()


def test_wob_docs_do_not_claim_wob_performance():
    repo_root = Path(__file__).resolve().parents[1]
    docs = [
        repo_root / "docs" / "research" / "70_wob_controlled_expansion_plan.md",
        repo_root / "docs" / "research" / "71_wob_p0_dataset_materialization_audit.md",
        repo_root / "cloud" / "wob_p1_seed42" / "README.md",
    ]
    forbidden = [
        "outperforms",
        "cross-game result",
        "wob achieves",
        "action-conditioning improves",
        "wob significantly improves",
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in docs)
    for phrase in forbidden:
        assert phrase not in text
