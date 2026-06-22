from __future__ import annotations

import csv
import json
import tarfile
from pathlib import Path
from unittest.mock import patch

from glitch_detection import r5_wob_staged


def test_resolve_seed_inputs_repacks_extracted_seed_folder(tmp_path: Path):
    input_root = tmp_path / "input"
    extracted_root = input_root / "dataset" / "wob_seed42_artifacts" / "wob_outputs" / "wob_seed42"
    extracted_root.mkdir(parents=True)
    (extracted_root / "training_metadata.json").write_text("{}", encoding="utf-8")
    repack_root = tmp_path / "repacked"

    result = r5_wob_staged._resolve_seed_inputs(input_root, seed=42, repack_root=repack_root)

    assert result["mode"] == "repacked_extracted_folder"
    tarball = Path(result["tarball"])
    sidecar = Path(result["sidecar"])
    assert tarball.is_file()
    assert sidecar.is_file()
    with tarfile.open(tarball, "r:gz") as archive:
        assert "wob_outputs/wob_seed42/training_metadata.json" in archive.getnames()


def test_resolve_seed_inputs_direct_tarball_avoids_recursive_scan(tmp_path: Path, monkeypatch):
    input_root = tmp_path / "input"
    artifact_root = input_root / "wob-artifacts"
    artifact_root.mkdir(parents=True)
    (artifact_root / "wob_seed42_artifacts.tar.gz").write_bytes(b"seed42")
    (artifact_root / "wob_seed42_artifacts.tar.gz.sha256").write_text("hash\n", encoding="utf-8")
    repack_root = tmp_path / "repacked"

    def explode(self: Path, pattern: str):
        raise AssertionError(f"unexpected recursive scan for {self} / {pattern}")

    monkeypatch.setattr(Path, "rglob", explode)

    result = r5_wob_staged._resolve_seed_inputs(input_root, seed=42, repack_root=repack_root)

    assert result["mode"] == "direct_tarball"
    assert result["tarball"].endswith("wob_seed42_artifacts.tar.gz")


def test_validate_stage_outputs_reports_missing_markers(tmp_path: Path):
    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)
    assert result["stages"]["preflight"]["status"] == "missing"
    assert result["stages"]["validate_package"]["status"] == "missing"


def test_validate_stage_outputs_accepts_complete_marker(tmp_path: Path):
    file_path = tmp_path / "artifact.txt"
    file_path.write_text("ok", encoding="utf-8")
    marker_path = tmp_path / "stage_preflight.json"
    marker_path.write_text(
        json.dumps(
            {
                "stage": "preflight",
                "schema_version": 1,
                "status": "preflight_complete",
                "smoke": False,
                "files": {"artifact": r5_wob_staged._file_record(file_path)},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)

    assert result["stages"]["preflight"]["status"] == "complete"
    assert result["stages"]["preflight"]["summary_status"] == "preflight_complete"


def test_file_record_and_stage_validation_accept_lance_directory(tmp_path: Path):
    lance_dir = tmp_path / "_wob_train_normal.lance"
    (lance_dir / "data").mkdir(parents=True)
    (lance_dir / "data" / "part-0.bin").write_bytes(b"lance bytes")

    record = r5_wob_staged._file_record(lance_dir)
    assert record["path_type"] == "directory"

    marker_path = tmp_path / "stage_materialize_lance.json"
    marker_path.write_text(
        json.dumps(
            {
                "stage": "materialize_lance",
                "schema_version": 1,
                "status": "materialize_lance_complete",
                "smoke": False,
                "files": {"train_lance": record},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)

    assert result["stages"]["materialize_lance"]["status"] == "complete"


def test_validate_stage_outputs_rejects_smoke_mismatch(tmp_path: Path):
    marker_path = tmp_path / "stage_preflight.json"
    marker_path.write_text(
        json.dumps(
            {
                "stage": "preflight",
                "schema_version": 1,
                "status": "preflight_complete",
                "smoke": True,
                "files": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = r5_wob_staged.validate_stage_outputs(tmp_path, smoke=False)

    assert result["stages"]["preflight"]["status"] == "invalid"
    assert "smoke mismatch" in result["stages"]["preflight"]["error"]


def test_staged_pipeline_uses_core_lance_eval_module_not_cli_wrapper():
    source = Path("src/glitch_detection/r5_wob_staged.py").read_text(encoding="utf-8")
    assert '_load_script_module("run_gate7_lance_scoring")' not in source


def test_materialize_lance_logs_dataset_boundaries_and_counts(tmp_path: Path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    manifest_path = tmp_path / "eval_manifest.csv"
    split_path = tmp_path / "split.csv"
    readiness_path = tmp_path / "readiness.json"
    preflight = {
        "stage": "preflight",
        "schema_version": 1,
        "smoke": False,
        "normal_root": str(tmp_path / "normal"),
        "test_root": str(tmp_path / "test"),
        "files": {},
    }
    eval_rows = [
        {"evaluation_role": "calibration_normal", "episode_id": "n1"},
        {"evaluation_role": "evaluation_buggy", "episode_id": "b1"},
    ]
    train_rows = [{"episode_id": "t1"}]
    built_paths = {
        r5_wob_staged.TRAIN_LANCE_NAME: output_dir / r5_wob_staged.TRAIN_LANCE_NAME,
        r5_wob_staged.NORMAL_LANCE_NAME: output_dir / r5_wob_staged.NORMAL_LANCE_NAME,
        r5_wob_staged.BUGGY_LANCE_NAME: output_dir / r5_wob_staged.BUGGY_LANCE_NAME,
    }
    for path in built_paths.values():
        path.mkdir(parents=True)
        (path / "part-0.bin").write_bytes(b"x")
    window_manifest = output_dir / r5_wob_staged.WINDOW_MANIFEST_NAME
    window_manifest.write_text("window_id\nw1\n", encoding="utf-8")

    def fake_build_lance_from_rows(
        rows,
        *,
        output_path: Path,
        progress=None,
        progress_label: str | None = None,
        **kwargs,
    ) -> Path:
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "part-0.bin").write_bytes(b"x")
        if progress is not None:
            progress(f"{progress_label}: wrote {len(rows)}/{len(rows)} episodes to {output_path}")
        return output_path

    progress_messages: list[str] = []
    with (
        patch("glitch_detection.r5_wob_staged._maybe_skip", return_value=None),
        patch(
            "glitch_detection.r5_wob_staged._validate_stage_marker",
            return_value=preflight,
        ),
        patch(
            "glitch_detection.r5_wob_staged._validate_readiness_and_manifest",
            return_value=({"eval_manifest_sha256": "abc"}, eval_rows),
        ),
        patch("glitch_detection.r5_wob_staged._load_train_rows", return_value=train_rows),
        patch("glitch_detection.r5_wob_staged._render_eval_manifest", return_value="episode_id\n"),
        patch(
            "glitch_detection.r5_wob_staged._build_lance_from_rows",
            side_effect=fake_build_lance_from_rows,
        ),
        patch(
            "glitch_detection.r5_wob_staged._build_window_manifest",
            return_value=(1, {"normal": "n", "buggy": "b"}),
        ),
        patch("glitch_detection.r5_wob_staged._progress", side_effect=progress_messages.append),
    ):
        result = r5_wob_staged.run_materialize_lance(
            readiness_json=readiness_path,
            eval_manifest=manifest_path,
            split_csv=split_path,
            output_dir=output_dir,
            smoke=False,
            force=False,
        )

    assert result["status"] == "materialize_complete"
    assert any("train lance start rows=1" in message for message in progress_messages)
    assert any("train lance complete rows=1" in message for message in progress_messages)
    assert any("normal lance start rows=1" in message for message in progress_messages)
    assert any("normal lance complete rows=1" in message for message in progress_messages)
    assert any("buggy lance start rows=1" in message for message in progress_messages)
    assert any("buggy lance complete rows=1" in message for message in progress_messages)
    assert any("window manifest complete rows=1" in message for message in progress_messages)


class _RecordingSample:
    def __init__(self, data: dict[str, str], accessed: list[str]) -> None:
        self._data = data
        self._accessed = accessed

    def __getitem__(self, key: str) -> str:
        self._accessed.append(key)
        return self._data[key]


class _FakeDataset:
    def __init__(self, samples: list[dict[str, str]]) -> None:
        self._samples = samples
        self.read_indices: list[int] = []
        self.accessed_keys: list[str] = []

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int):
        self.read_indices.append(index)
        return _RecordingSample(self._samples[index], self.accessed_keys)


def _wob_sample(episode: str, label: str) -> dict[str, str]:
    return {
        "source": "wob",
        "source_episode_id": episode,
        "pair_id": f"pair/{episode}",
        "category": "category",
        "label": label,
        "split": "validation",
        "action_mode": "zero_action",
        "pixels": "PIXELS",
        "action": "ACTION",
    }


def test_build_window_manifest_streams_to_csv_without_pixels(tmp_path: Path, monkeypatch):
    normal = _FakeDataset(
        [
            _wob_sample("normal-a", "normal"),
            _wob_sample("normal-a", "normal"),
            _wob_sample("normal-b", "normal"),
        ]
    )
    buggy = _FakeDataset([_wob_sample("buggy-a", "buggy")])

    def fake_open(path):
        return (normal, True) if "normal" in str(path) else (buggy, True)

    monkeypatch.setattr(r5_wob_staged, "open_metadata_dataset", fake_open)
    monkeypatch.setattr(
        r5_wob_staged.FingerprintBuilder,
        "inventory_sha256",
        staticmethod(lambda path: "fp"),
    )

    eval_rows = [
        {"episode_id": "normal-a", "evaluation_role": "calibration_normal"},
        {"episode_id": "normal-b", "evaluation_role": "calibration_normal"},
        {"episode_id": "buggy-a", "evaluation_role": "evaluation"},
    ]
    output_path = tmp_path / "_window_manifest.csv"

    row_count, fingerprints = r5_wob_staged._build_window_manifest(
        normal_lance=tmp_path / "normal.lance",
        buggy_lance=tmp_path / "buggy.lance",
        eval_rows=eval_rows,
        output_path=output_path,
    )

    assert row_count == 4
    assert normal.read_indices == [0, 1, 2]
    assert buggy.read_indices == [0]
    assert "pixels" not in normal.accessed_keys + buggy.accessed_keys
    assert "action" not in normal.accessed_keys + buggy.accessed_keys
    assert set(fingerprints) == {"normal_validation", "buggy_probe"}

    written = list(csv.DictReader(output_path.open("r", encoding="utf-8")))
    assert len(written) == 4
    telemetry_path = output_path.parent / "resource_telemetry_materialize_lance.json"
    assert telemetry_path.exists()
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["phase"] == "materialize_lance_window_manifest"
    assert telemetry["checkpoints"][-1]["checkpoint"] == "complete"
