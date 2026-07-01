from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from glitch_detection import r5_wob_eval


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _make_readiness_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    split_rows: list[dict[str, str]] = []
    for index in range(48):
        split_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-normal",
                "source": f"NORMAL-TRAIN/ep-{index:04d}/ep-{index:04d}.tar",
                "episode_id": f"normal/ep-{index:04d}",
                "pair_id": f"normal/ep-{index:04d}",
                "category": "Normal",
                "label": "Normal",
                "split": "train",
                "action_mode": "real",
                "use_for_training": "True",
                "materialize": "True",
            }
        )
    eval_rows: list[dict[str, str]] = []
    for index in range(6):
        eval_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-normal",
                "source": f"NORMAL-TRAIN/ep-{100 + index:04d}/ep-{100 + index:04d}.tar",
                "episode_id": f"normal/ep-{100 + index:04d}",
                "pair_id": f"normal/ep-{100 + index:04d}",
                "category": "Normal",
                "label": "Normal",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
                "evaluation_role": "calibration_normal",
            }
        )
    for index in range(6):
        eval_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-normal",
                "source": f"NORMAL-TRAIN/ep-{106 + index:04d}/ep-{106 + index:04d}.tar",
                "episode_id": f"normal/ep-{106 + index:04d}",
                "pair_id": f"normal/ep-{106 + index:04d}",
                "category": "Normal",
                "label": "Normal",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
                "evaluation_role": "evaluation_normal",
            }
        )
    for index in range(60):
        eval_rows.append(
            {
                "dataset_id": "benedictwilkinsai/world-of-bugs-test",
                "source": f"TEST/Bug/ep-{index:04d}/ep-{index:04d}.tar",
                "episode_id": f"Bug/ep-{index:04d}",
                "pair_id": f"Bug/ep-{index:04d}",
                "category": "Bug",
                "label": "Buggy",
                "split": "validation",
                "action_mode": "real",
                "use_for_training": "False",
                "materialize": "True",
                "evaluation_role": "evaluation_buggy",
            }
        )
    split_path = tmp_path / "split.csv"
    _write_csv(split_path, split_rows)
    manifest_path = tmp_path / "wob_expansion_eval_manifest.csv"
    _write_csv(manifest_path, eval_rows)
    readiness = {
        "phase": "wob_expansion_readiness",
        "seed": 42,
        "status": "frozen",
        "eval_manifest_path": str(manifest_path.relative_to(tmp_path)).replace("\\", "/"),
        "eval_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "eval_manifest_row_count": 72,
        "calibration": {"count": 6},
        "evaluation_normal": {"count": 6},
        "evaluation_buggy": {"count": 60},
        "locked_rows_excluded": 59,
        "train_rows_excluded": 48,
        "recorded_artifact_hashes": {
            "wob_p0_kaggle_audit_sha256": "e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9",
            "wob_p1_seed42_artifact_sha256": "54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03",
        },
        "seed42_selected_checkpoint": {
            "seed": 42,
            "selection_split": "validation_normal",
            "action_dim": 4,
        },
        "reporting": {
            "results_doc": "docs/research/78_r5_wob_identical_episode_results.md",
            "output_dir": "outputs/r5_wob_identical_episode",
            "manifest_output": "outputs/r5_wob_identical_episode/r5_wob_manifest.csv",
            "metrics_output": "outputs/r5_wob_identical_episode/r5_wob_metrics.json",
        },
        "claim_boundary": "frozen",
        "forbidden_claims": ["no locked test"],
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": False,
    }
    readiness_path = tmp_path / "wob_expansion_readiness.json"
    readiness_path.write_text(json.dumps(readiness, indent=2), encoding="utf-8")
    return split_path, manifest_path, readiness_path


def test_summarize_source_coverage_reports_missing_paths(tmp_path: Path):
    rows = [
        {"label": "Normal", "source": "NORMAL-TRAIN/ep-0000/ep-0000.tar"},
        {"label": "Buggy", "source": "TEST/Bug/ep-0001/ep-0001.tar"},
    ]
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    (normal_root / "NORMAL-TRAIN" / "ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN" / "ep-0000" / "ep-0000.tar").write_text("x", encoding="utf-8")
    summary = r5_wob_eval.summarize_source_coverage(
        rows,
        normal_root=normal_root,
        test_root=test_root,
    )
    assert summary["resolved_count"] == 1
    assert summary["missing_count"] == 1


def test_r5_wob_dry_run_reports_missing_local_coverage(tmp_path: Path, monkeypatch):
    split_path, manifest_path, readiness_path = _make_readiness_bundle(tmp_path)

    class _FakeReadinessModule:
        @staticmethod
        def validate_readiness(_readiness_json: Path, *, repo_root: Path) -> dict[str, str]:
            return {"status": "ok", "repo_root": str(repo_root)}

    def fake_load_script_module(stem: str):
        assert stem == "validate_wob_expansion_readiness"
        return _FakeReadinessModule()

    monkeypatch.setattr(r5_wob_eval, "_load_script_module", fake_load_script_module)
    monkeypatch.setattr(
        r5_wob_eval,
        "_resolve_seed_artifacts",
        lambda **kwargs: [
            {"seed": 42},
            {"seed": 43},
            {"seed": 44},
        ],
    )

    result = r5_wob_eval.run_r5_wob_identical_episode_evaluation(
        readiness_json=readiness_path,
        eval_manifest=manifest_path,
        split_csv=split_path,
        normal_root=tmp_path / "attached",
        test_root=tmp_path / "attached",
        output_dir=tmp_path / "outputs",
        seed_tarballs={42: Path("a"), 43: Path("b"), 44: Path("c")},
        seed_sidecars={42: Path("a.sha"), 43: Path("b.sha"), 44: Path("c.sha")},
        dry_run=True,
    )

    assert result["status"] == "dry_run"
    assert result["train_coverage"]["missing_count"] == 48
    assert result["eval_coverage"]["missing_count"] == 72


def test_build_lance_from_rows_streams_episodes_into_writer(tmp_path: Path, monkeypatch):
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    first_tar = normal_root / "NORMAL-TRAIN" / "ep-0000" / "ep-0000.tar"
    second_tar = test_root / "TEST" / "Bug" / "ep-0001" / "ep-0001.tar"
    first_tar.parent.mkdir(parents=True)
    second_tar.parent.mkdir(parents=True)
    first_tar.write_bytes(b"normal")
    second_tar.write_bytes(b"buggy")
    rows = [
        {
            "source": "NORMAL-TRAIN/ep-0000/ep-0000.tar",
            "episode_id": "normal/ep-0000",
            "pair_id": "normal/ep-0000",
            "category": "Normal",
            "label": "Normal",
            "split": "train",
        },
        {
            "source": "TEST/Bug/ep-0001/ep-0001.tar",
            "episode_id": "Bug/ep-0001",
            "pair_id": "Bug/ep-0001",
            "category": "Bug",
            "label": "Buggy",
            "split": "validation",
        },
    ]

    captured: dict[str, object] = {}
    messages: list[str] = []

    def fake_episode_from_wob_tar(path: Path, **kwargs):
        return {"path": path, **kwargs}

    def fake_write_lance_dataset(
        episodes,
        output_path: Path,
        *,
        mode: str = "error",
        batch_size: int = 1,
        progress=None,
    ) -> Path:
        captured["episodes_is_list"] = isinstance(episodes, list)
        captured["mode"] = mode
        captured["batch_size"] = batch_size
        collected = list(episodes)
        captured["episodes"] = collected
        if progress is not None:
            progress(len(collected))
        return output_path

    monkeypatch.setattr(r5_wob_eval, "episode_from_wob_tar", fake_episode_from_wob_tar)
    monkeypatch.setattr(r5_wob_eval, "write_lance_dataset", fake_write_lance_dataset)

    output = r5_wob_eval._build_lance_from_rows(
        rows,
        normal_root=normal_root,
        test_root=test_root,
        output_path=tmp_path / "out.lance",
        write_batch_size=3,
        progress=messages.append,
        progress_label="materialize/train",
        progress_every=1,
    )

    assert output == tmp_path / "out.lance"
    assert captured["episodes_is_list"] is False
    assert captured["mode"] == "error"
    assert captured["batch_size"] == 3
    assert [item["episode_id"] for item in captured["episodes"]] == [
        "normal/ep-0000",
        "Bug/ep-0001",
    ]
    assert any("wrote 2/2 episodes" in message for message in messages)
