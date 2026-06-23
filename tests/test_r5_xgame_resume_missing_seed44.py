from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest


def _load_resume():
    path = Path("scripts/run_r5_xgame_resume_missing_seed44.py")
    spec = importlib.util.spec_from_file_location("r5_xgame_resume_missing_seed44", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_runner():
    path = Path("scripts/run_r5_xgame_staged.py")
    spec = importlib.util.spec_from_file_location("r5_xgame_runner_for_resume_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


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


def _minimal_partial_output(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    marker_payload = {
        "status": "ok",
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    _write_json(root / "stage_preflight.json", marker_payload)
    _write_json(root / "stage_materialize.json", marker_payload)
    _write_json(root / "stage_baseline_score.json", marker_payload)
    _write_json(
        root / "stage_train_lewm.json",
        {**marker_payload, "status": "train_lewm_complete"},
    )
    rows = [
        {"window_id": "normal-window-0", "dataset_name": "normal_validation"},
        {"window_id": "buggy-window-0", "dataset_name": "buggy_probe"},
    ]
    _write_window_manifest(root / "r5_xgame_window_manifest.csv", rows)
    (root / "r5_xgame_baseline_scores.csv").write_text(
        "window_id,frame_diff\nx,0.1\n", encoding="utf-8"
    )
    score_rows = [
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
    _write_lewm_scores(root / "r5_xgame_lewm_scores_seed42.csv", score_rows)
    _write_lewm_scores(root / "r5_xgame_lewm_scores_seed43.csv", score_rows)
    for seed in (42, 43, 44):
        seed_dir = root / f"_lewm_seed{seed}"
        seed_dir.mkdir()
        (seed_dir / "config.json").write_text("{}", encoding="utf-8")
        (seed_dir / "best_weights.pt").write_bytes(b"weights")
    return root


def test_find_partial_output_dir_refuses_missing_r5_xgame_dir(tmp_path: Path):
    resume = _load_resume()
    with pytest.raises(FileNotFoundError, match="Missing mounted partial R5-XGame directory"):
        resume.find_partial_output_dir(tmp_path / "input")


def test_validate_partial_output_refuses_missing_stage_train_lewm(tmp_path: Path):
    resume = _load_resume()
    partial = _minimal_partial_output(tmp_path / "r5_xgame")
    (partial / "stage_train_lewm.json").unlink()
    with pytest.raises(FileNotFoundError, match="stage_train_lewm.json"):
        resume.validate_partial_output_for_resume(partial)


def test_validate_partial_output_refuses_incomplete_seed42_scores(tmp_path: Path):
    resume = _load_resume()
    partial = _minimal_partial_output(tmp_path / "r5_xgame")
    _write_lewm_scores(
        partial / "r5_xgame_lewm_scores_seed42.csv",
        [
            {
                "window_id": "normal-window-0",
                "mse_t1": "1.0",
                "mse_t2": "1.1",
                "mse_t3": "1.2",
                "l2_t1": "2.0",
                "l2_t2": "2.1",
                "l2_t3": "2.2",
            }
        ],
    )
    with pytest.raises(ValueError, match="Incomplete seed42 score CSV"):
        resume.validate_partial_output_for_resume(partial)


def test_validate_partial_output_refuses_missing_seed44_weights(tmp_path: Path):
    resume = _load_resume()
    partial = _minimal_partial_output(tmp_path / "r5_xgame")
    (partial / "_lewm_seed44" / "best_weights.pt").unlink()
    with pytest.raises(FileNotFoundError, match="best_weights.pt"):
        resume.validate_partial_output_for_resume(partial)


def test_resume_missing_seed44_only_calls_seed44_scoring(tmp_path: Path, monkeypatch):
    resume = _load_resume()
    input_root = tmp_path / "input"
    partial = input_root / "mounted" / "r5_xgame"
    output_dir = tmp_path / "working" / "r5_xgame"
    manifest = Path("configs/wob_protocol/r5_xgame_split.csv")
    call_log: list[tuple[str, object]] = []

    class FakeRunner:
        def run_materialize(self, **kwargs):
            raise AssertionError("resume must not rerun materialize")

        def run_baseline_score(self, **kwargs):
            raise AssertionError("resume must not rerun baseline_score")

        def run_train_lewm(self, **kwargs):
            raise AssertionError("resume must not rerun train_lewm")

        def run_lewm_score(self, **kwargs):
            call_log.append(("run_lewm_score", kwargs))
            return {"status": "lewm_score_complete"}

    monkeypatch.setattr(resume, "find_partial_output_dir", lambda root: partial)
    monkeypatch.setattr(resume, "copy_partial_output_dir", lambda src, dst: dst)
    monkeypatch.setattr(
        resume,
        "validate_partial_output_for_resume",
        lambda out: {"status": "resume_partial_output_validated"},
    )
    monkeypatch.setattr(
        resume,
        "finalize_from_complete_scores",
        lambda **kwargs: {"status": "resume_finalize_complete"},
    )
    monkeypatch.setattr(resume, "_runner", lambda: FakeRunner())

    result = resume.resume_missing_seed44_and_finalize(
        input_root=input_root,
        output_dir=output_dir,
        manifest=manifest,
        device="cuda",
        lewm_batch_size=2,
        bootstrap_seed=42,
        n_bootstrap=1000,
    )

    assert result["status"] == "resume_missing_seed44_complete"
    assert call_log == [
        (
            "run_lewm_score",
            {
                "output_dir": output_dir,
                "seeds": (44,),
                "device": "cuda",
                "batch_size": 2,
            },
        )
    ]


def test_finalize_requires_all_three_score_files_before_downstream(tmp_path: Path, monkeypatch):
    resume = _load_resume()
    output = tmp_path / "output"
    output.mkdir()
    (output / "r5_xgame_window_manifest.csv").write_text(
        "window_id,dataset_name\nnormal-window-0,normal_validation\nbuggy-window-0,buggy_probe\n",
        encoding="utf-8",
    )
    (output / "stage_lewm_score.json").write_text(
        '{"status":"lewm_score_complete"}', encoding="utf-8"
    )
    downstream_calls: list[str] = []

    class FakeRunner:
        WINDOW_MANIFEST_NAME = "r5_xgame_window_manifest.csv"

        def read_csv_rows(self, path: Path):
            return [
                {"window_id": "normal-window-0", "dataset_name": "normal_validation"},
                {"window_id": "buggy-window-0", "dataset_name": "buggy_probe"},
            ]

        def validate_existing_lewm_score_file(self, output_dir: Path, manifest_rows, *, seed: int):
            if seed in (42, 43):
                return {"path": str(output_dir / f"seed{seed}.csv"), "sha256": "x", "row_count": 2}
            raise ValueError("Incomplete seed44 score CSV")

        def run_aggregate_episode(self, **kwargs):
            downstream_calls.append("aggregate_episode")
            return {"status": "aggregate_episode_complete"}

        def run_calibrate_thresholds(self, **kwargs):
            downstream_calls.append("calibrate_thresholds")
            return {"status": "calibrate_thresholds_complete"}

        def run_evaluate_binary(self, **kwargs):
            downstream_calls.append("evaluate_binary")
            return {"status": "evaluate_binary_complete"}

        def run_bootstrap_ci(self, **kwargs):
            downstream_calls.append("bootstrap_ci")
            return {"status": "bootstrap_ci_complete"}

        def run_package(self, **kwargs):
            downstream_calls.append("package")
            return {"status": "package_complete"}

        def run_validate_package(self, **kwargs):
            downstream_calls.append("validate_package")
            return {"status": "validate_package_complete"}

    monkeypatch.setattr(resume, "_runner", lambda: FakeRunner())

    with pytest.raises(ValueError, match="Incomplete seed44 score CSV"):
        resume.finalize_from_complete_scores(
            output_dir=output,
            manifest=Path("configs/wob_protocol/r5_xgame_split.csv"),
            bootstrap_seed=42,
            n_bootstrap=1000,
        )
    assert downstream_calls == []
