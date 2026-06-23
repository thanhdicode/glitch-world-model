from __future__ import annotations

import csv
import importlib.util
import json
import tarfile
from pathlib import Path

import pytest


def _runner():
    path = Path("scripts/run_r5_xgame_staged.py")
    spec = importlib.util.spec_from_file_location("r5_xgame_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preflight_reports_missing_archives_by_role(tmp_path: Path):
    runner = _runner()
    result = runner.preflight(
        Path("configs/wob_protocol/r5_xgame_split.csv"),
        tmp_path / "missing",
        tmp_path / "out",
        [42, 43, 44],
    )
    assert result["status"] == "preflight_missing_inputs"
    assert len(result["missing_by_role"]["train_normal"]) == 36
    assert len(result["missing_by_role"]["evaluation_normal_negative"]) == 12
    assert len(result["missing_by_role"]["calibration_normal"]) == 12
    assert len(result["missing_by_role"]["evaluation_buggy_positive"]) == 60
    assert (tmp_path / "out" / "stage_preflight.json").is_file()


def test_preflight_resolves_all_sources_from_a_matching_root(tmp_path: Path):
    runner = _runner()
    manifest = Path("configs/wob_protocol/r5_xgame_split.csv")
    for row in __import__("csv").DictReader(manifest.open(encoding="utf-8")):
        target = tmp_path / row["source"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x")
    result = runner.preflight(manifest, tmp_path, tmp_path / "out", [42, 43, 44])
    assert result["status"] == "preflight_complete"
    assert not any(result["missing_by_role"].values())


def test_preflight_rejects_old_r5_wob_artifact_roots(tmp_path: Path):
    runner = _runner()
    input_root = tmp_path / "input"
    (input_root / "r5_wob_seed42_artifacts").mkdir(parents=True)
    with pytest.raises(ValueError, match="R5-WOB"):
        runner.preflight(
            Path("configs/wob_protocol/r5_xgame_split.csv"),
            input_root,
            tmp_path / "out",
            [42, 43, 44],
        )


def test_package_writes_tarball_and_sidecar(tmp_path: Path, monkeypatch):
    runner = _runner()
    manifest = Path("configs/wob_protocol/r5_xgame_split.csv")
    output = tmp_path / "out"
    output.mkdir()
    for name in runner.PLANNED_OUTPUTS:
        if name.endswith(".tar.gz") or name.endswith(".sha256"):
            continue
        (output / name).write_text("x\n", encoding="utf-8")
    (output / "r5_xgame_metrics.json").write_text(
        json.dumps(
            {
                "summary_row": {
                    "method": "frame_diff",
                    "seed": "",
                    "window_scorer": "frame_diff",
                    "episode_aggregation": "mean",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "runtime_provenance",
        lambda include_lewm: {"git_sha": "abc"} if not include_lewm else {"git_sha": "abc"},
    )
    result = runner.run_package(manifest=manifest, output_dir=output)
    assert result["status"] == "package_complete"
    assert (output / "r5_xgame_outputs.tar.gz").is_file()
    assert (output / "r5_xgame_outputs.tar.gz.sha256").is_file()
    with tarfile.open(output / "r5_xgame_outputs.tar.gz", "r:gz") as archive:
        assert "r5_xgame_manifest.csv" in archive.getnames()


def test_kaggle_launch_script_and_required_input_doc_exist():
    script = Path("cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh")
    doc = Path("docs/research/r5_xgame_required_kaggle_inputs.md")
    assert script.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "benedictwilkinsai/world-of-bugs-normal" in text
    assert "benedictwilkinsai/world-of-bugs-test" in text
    assert "NORMAL-TRAIN/" in text
    assert "TEST/" in text


def test_kaggle_launch_script_passes_audit_output_path():
    script_text = Path("cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh").read_text(
        encoding="utf-8"
    )
    assert "scripts/audit_r5_xgame_split.py" in script_text
    assert "--output" in script_text
    assert "r5_xgame_leakage_audit.json" in script_text
    assert 'mkdir -p "$OUTPUT_DIR"' in script_text


def _write_window_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("window_id", "dataset_name"))
        writer.writeheader()
        writer.writerows(rows)


def _write_lewm_scores(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("window_id", "mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3"),
        )
        writer.writeheader()
        writer.writerows(rows)


def test_lewm_score_can_resume_only_missing_seed44(tmp_path: Path, monkeypatch):
    runner = _runner()
    output = tmp_path / "output"
    output.mkdir()
    manifest_rows = [
        {"window_id": "normal-window-0", "dataset_name": runner.NORMAL_DATASET_NAME},
        {"window_id": "buggy-window-0", "dataset_name": runner.BUGGY_DATASET_NAME},
    ]
    _write_window_manifest(output / runner.WINDOW_MANIFEST_NAME, manifest_rows)
    seed42_rows = [
        {
            "window_id": "normal-window-0",
            "mse_t1": "1.0",
            "mse_t2": "1.1",
            "mse_t3": "1.2",
            "l2_t1": "2.0",
            "l2_t2": "2.1",
            "l2_t3": "2.2",
        },
        {
            "window_id": "buggy-window-0",
            "mse_t1": "3.0",
            "mse_t2": "3.1",
            "mse_t3": "3.2",
            "l2_t1": "4.0",
            "l2_t2": "4.1",
            "l2_t3": "4.2",
        },
    ]
    seed43_rows = [
        {
            "window_id": "normal-window-0",
            "mse_t1": "5.0",
            "mse_t2": "5.1",
            "mse_t3": "5.2",
            "l2_t1": "6.0",
            "l2_t2": "6.1",
            "l2_t3": "6.2",
        },
        {
            "window_id": "buggy-window-0",
            "mse_t1": "7.0",
            "mse_t2": "7.1",
            "mse_t3": "7.2",
            "l2_t1": "8.0",
            "l2_t2": "8.1",
            "l2_t3": "8.2",
        },
    ]
    seed42_path = output / "r5_xgame_lewm_scores_seed42.csv"
    seed43_path = output / "r5_xgame_lewm_scores_seed43.csv"
    _write_lewm_scores(seed42_path, seed42_rows)
    _write_lewm_scores(seed43_path, seed43_rows)
    seed42_before = seed42_path.read_text(encoding="utf-8")
    seed43_before = seed43_path.read_text(encoding="utf-8")

    def fake_stage_marker(_output_dir: Path, stage: str):
        if stage == "materialize":
            return {
                "files": {
                    runner.WINDOW_MANIFEST_NAME: {
                        "path": str(output / runner.WINDOW_MANIFEST_NAME)
                    },
                    runner.NORMAL_LANCE_NAME: {"path": str(output / runner.NORMAL_LANCE_NAME)},
                    runner.BUGGY_LANCE_NAME: {"path": str(output / runner.BUGGY_LANCE_NAME)},
                },
                "validation_buggy_used_for_fit_select": False,
                "locked_test_materialized": False,
                "locked_test_scored": False,
            }
        if stage == "train_lewm":
            return {
                "status": "train_lewm_complete",
                "seed_outputs": [
                    {
                        "seed": 42,
                        "weights_path": "seed42.pt",
                        "config_path": "seed42.json",
                        "checkpoint_sha256": "seed42",
                    },
                    {
                        "seed": 43,
                        "weights_path": "seed43.pt",
                        "config_path": "seed43.json",
                        "checkpoint_sha256": "seed43",
                    },
                    {
                        "seed": 44,
                        "weights_path": "seed44.pt",
                        "config_path": "seed44.json",
                        "checkpoint_sha256": "seed44",
                    },
                ],
                "validation_buggy_used_for_fit_select": False,
                "locked_test_materialized": False,
                "locked_test_scored": False,
            }
        raise AssertionError(f"Unexpected stage: {stage}")

    score_calls: list[tuple[str, tuple[str, ...], int, str]] = []

    class FakeLeWMAdapter:
        def __init__(self, spec):
            self.spec = spec

        def load(self):
            return {"weights_path": str(self.spec.weights_path)}

    def fake_score_dataset(path: Path, window_ids, adapter, batch_size: int, device: str):
        score_calls.append((Path(path).name, tuple(window_ids), batch_size, device))
        return [
            {
                "window_id": window_id,
                "mse_t1": "9.0",
                "mse_t2": "9.1",
                "mse_t3": "9.2",
                "l2_t1": "10.0",
                "l2_t2": "10.1",
                "l2_t3": "10.2",
            }
            for window_id in window_ids
        ]

    stage_payload: dict[str, object] = {}

    def fake_write_stage_marker(_output_dir: Path, stage: str, payload: dict[str, object]):
        stage_payload["stage"] = stage
        stage_payload["payload"] = payload
        return payload

    monkeypatch.setattr(runner, "_load_stage_marker", fake_stage_marker)
    monkeypatch.setattr(runner, "LeWMAdapter", FakeLeWMAdapter)
    monkeypatch.setattr(runner, "_score_dataset", fake_score_dataset)
    monkeypatch.setattr(runner, "_write_stage_marker", fake_write_stage_marker)

    result = runner.run_lewm_score(output_dir=output, seeds=(44,), device="cpu", batch_size=3)

    assert result["status"] == "lewm_score_complete"
    assert score_calls == [
        (runner.NORMAL_LANCE_NAME, ("normal-window-0",), 3, "cpu"),
        (runner.BUGGY_LANCE_NAME, ("buggy-window-0",), 3, "cpu"),
    ]
    assert seed42_path.read_text(encoding="utf-8") == seed42_before
    assert seed43_path.read_text(encoding="utf-8") == seed43_before
    seed44_rows = runner.read_csv_rows(output / "r5_xgame_lewm_scores_seed44.csv")
    assert [row["window_id"] for row in seed44_rows] == [
        "normal-window-0",
        "buggy-window-0",
    ]
    assert stage_payload["stage"] == "lewm_score"
    payload = stage_payload["payload"]
    assert isinstance(payload, dict)
    assert sorted(item["seed"] for item in payload["seed_outputs"]) == [42, 43, 44]
    assert set(payload["files"]) == {
        "r5_xgame_lewm_scores_seed42.csv",
        "r5_xgame_lewm_scores_seed43.csv",
        "r5_xgame_lewm_scores_seed44.csv",
    }


def test_resume_kaggle_launch_script_skips_early_stages():
    script_text = Path(
        "cloud/wob_r5_xgame/run_kaggle_r5_xgame_resume_missing_seed44_and_finalize.sh"
    ).read_text(encoding="utf-8")
    assert "scripts/run_r5_xgame_resume_missing_seed44.py" in script_text
    assert "--stage materialize" not in script_text
    assert "--stage baseline_score" not in script_text
    assert "--stage train_lewm" not in script_text
