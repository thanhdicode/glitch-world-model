from __future__ import annotations

from pathlib import Path

import pytest

from glitch_detection import lewm_lance_eval as lewm
from glitch_detection.lewm_lance_eval import (
    METADATA_KEYS,
    ResourceTelemetry,
    build_canonical_manifest,
    canonical_rows_from_samples,
    capture_resource_usage,
    iter_metadata_samples,
    open_metadata_dataset,
    read_csv_rows,
    runtime_provenance,
    select_calibration_episodes,
    validate_manifest_rows,
    validate_score_alignment,
)


def _sample(source: str, label: str) -> dict[str, str]:
    return {
        "source": source,
        "source_episode_id": source,
        "pair_id": f"pair/{source}",
        "category": "category",
        "label": label,
        "split": "validation",
        "action_mode": "zero_action",
    }


def _full_sample(source: str, label: str) -> dict[str, str]:
    """Metadata sample plus the heavyweight pixel/action columns."""
    sample = _sample(source, label)
    sample["pixels"] = "PIXELS"
    sample["action"] = "ACTION"
    return sample


class _RecordingSample:
    def __init__(self, data: dict[str, str], accessed: list[str]) -> None:
        self._data = data
        self._accessed = accessed

    def __getitem__(self, key: str) -> str:
        self._accessed.append(key)
        return self._data[key]


class _FakeDataset:
    """In-memory stand-in for ``swm.data.LanceDataset`` used in tests."""

    def __init__(self, samples: list[dict[str, str]]) -> None:
        self._samples = samples
        self.read_indices: list[int] = []
        self.accessed_keys: list[str] = []

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int) -> _RecordingSample:
        self.read_indices.append(index)
        return _RecordingSample(self._samples[index], self.accessed_keys)


def test_select_calibration_episodes_is_deterministic_and_grouped():
    episodes = [f"normal-{index}" for index in range(10)]

    selected = select_calibration_episodes(episodes, count=2, seed=42)

    assert selected == select_calibration_episodes(reversed(episodes), count=2, seed=42)
    assert len(selected) == 2
    assert len(set(selected)) == 2


def test_runtime_provenance_records_git_and_python_environment():
    provenance = runtime_provenance(include_lewm=False)

    assert len(provenance["git_sha"]) == 40
    assert provenance["python_version"]
    assert provenance["platform"]


def test_canonical_rows_assign_calibration_by_episode_and_buggy_to_evaluation():
    normal_samples = [
        _sample("normal-a", "Normal"),
        _sample("normal-a", "Normal"),
        _sample("normal-b", "Normal"),
        _sample("normal-c", "Normal"),
    ]
    buggy_samples = [_sample("buggy-a", "Buggy")]

    normal_rows = canonical_rows_from_samples(
        dataset_name="normal_validation",
        dataset_fingerprint="normal-fingerprint",
        samples=normal_samples,
        calibration_episodes={"normal-a", "normal-b"},
    )
    buggy_rows = canonical_rows_from_samples(
        dataset_name="buggy_probe",
        dataset_fingerprint="buggy-fingerprint",
        samples=buggy_samples,
        calibration_episodes={"normal-a", "normal-b"},
    )
    rows = [*normal_rows, *buggy_rows]

    assert [row["window_id"] for row in rows] == [
        "normal_validation:00000000",
        "normal_validation:00000001",
        "normal_validation:00000002",
        "normal_validation:00000003",
        "buggy_probe:00000000",
    ]
    assert {row["evaluation_role"] for row in normal_rows[:3]} == {"calibration_normal"}
    assert normal_rows[3]["evaluation_role"] == "evaluation"
    assert buggy_rows[0]["evaluation_role"] == "evaluation"
    validate_manifest_rows(rows, expected_calibration_episode_count=2)


def test_manifest_validation_rejects_locked_test_and_duplicate_window_ids():
    rows = canonical_rows_from_samples(
        dataset_name="normal_validation",
        dataset_fingerprint="fingerprint",
        samples=[_sample("normal-a", "Normal"), _sample("normal-b", "Normal")],
        calibration_episodes={"normal-a", "normal-b"},
    )
    duplicate = [*rows, dict(rows[0])]
    with pytest.raises(ValueError, match="duplicate"):
        validate_manifest_rows(duplicate, expected_calibration_episode_count=2)

    locked = [dict(row) for row in rows]
    locked[0]["split"] = "locked_test"
    with pytest.raises(ValueError, match="locked"):
        validate_manifest_rows(locked, expected_calibration_episode_count=2)


def test_score_alignment_rejects_reordered_or_non_finite_scores():
    manifest = canonical_rows_from_samples(
        dataset_name="normal_validation",
        dataset_fingerprint="fingerprint",
        samples=[_sample("normal-a", "Normal"), _sample("normal-b", "Normal")],
        calibration_episodes={"normal-a", "normal-b"},
    )
    scores = [
        {
            "window_id": row["window_id"],
            "mse_t1": "0.1",
            "mse_t2": "0.2",
            "mse_t3": "0.3",
            "l2_t1": "1.0",
            "l2_t2": "2.0",
            "l2_t3": "3.0",
        }
        for row in manifest
    ]

    validate_score_alignment(manifest, scores)
    with pytest.raises(ValueError, match="ordered"):
        validate_score_alignment(manifest, list(reversed(scores)))
    scores[0]["mse_t1"] = "nan"
    with pytest.raises(ValueError, match="finite"):
        validate_score_alignment(manifest, scores)


def test_iter_metadata_samples_reads_each_window_once_without_pixels():
    dataset = _FakeDataset(
        [_full_sample("normal-a", "Normal"), _full_sample("normal-b", "Normal")]
    )

    samples = list(iter_metadata_samples(dataset))

    assert dataset.read_indices == [0, 1]
    assert all(set(sample) == set(METADATA_KEYS) for sample in samples)
    assert "pixels" not in dataset.accessed_keys
    assert "action" not in dataset.accessed_keys


def test_open_metadata_dataset_prefers_metadata_only(monkeypatch):
    dataset = _FakeDataset([_full_sample("normal-a", "Normal")])
    calls: list[bool] = []

    def fake_lance(path, *, include_metadata, metadata_only=False):
        calls.append(metadata_only)
        return dataset

    monkeypatch.setattr(lewm, "_lance_dataset", fake_lance)

    opened, metadata_only = open_metadata_dataset(Path("normal.lance"))

    assert opened is dataset
    assert metadata_only is True
    assert calls == [True]
    assert dataset.read_indices == []
    assert dataset.accessed_keys == []


def test_open_metadata_dataset_then_iter_reads_each_window_exactly_once(monkeypatch):
    dataset = _FakeDataset(
        [
            _full_sample("normal-a", "Normal"),
            _full_sample("normal-b", "Normal"),
            _full_sample("normal-c", "Normal"),
        ]
    )
    monkeypatch.setattr(
        lewm, "_lance_dataset", lambda path, *, include_metadata, metadata_only=False: dataset
    )

    opened, _metadata_only = open_metadata_dataset(Path("normal.lance"))
    list(iter_metadata_samples(opened))

    assert dataset.read_indices == [0, 1, 2]
    assert dataset.read_indices.count(0) == 1
    assert "pixels" not in dataset.accessed_keys
    assert "action" not in dataset.accessed_keys


def test_open_metadata_dataset_falls_back_when_metadata_only_rejected(monkeypatch):
    full = _FakeDataset([_full_sample("normal-a", "Normal")])
    calls: list[bool] = []

    def fake_lance(path, *, include_metadata, metadata_only=False):
        calls.append(metadata_only)
        if metadata_only:
            raise KeyError("metadata-only projection not supported")
        return full

    monkeypatch.setattr(lewm, "_lance_dataset", fake_lance)

    opened, metadata_only = open_metadata_dataset(Path("normal.lance"))

    assert opened is full
    assert metadata_only is False
    assert calls == [True, False]


def test_open_metadata_dataset_reraises_runtime_error(monkeypatch):
    def fake_lance(path, *, include_metadata, metadata_only=False):
        raise RuntimeError("Gate 7 Lance evaluation requires the isolated LeWM runtime.")

    monkeypatch.setattr(lewm, "_lance_dataset", fake_lance)

    with pytest.raises(RuntimeError, match="isolated LeWM runtime"):
        open_metadata_dataset(Path("normal.lance"))


def test_build_canonical_manifest_streams_metadata_only(monkeypatch):
    normal = _FakeDataset(
        [
            _full_sample("normal-a", "Normal"),
            _full_sample("normal-b", "Normal"),
            _full_sample("normal-c", "Normal"),
        ]
    )
    buggy = _FakeDataset([_full_sample("buggy-a", "Buggy")])

    def fake_open(path):
        return (normal, True) if "normal" in str(path) else (buggy, True)

    monkeypatch.setattr(lewm, "open_metadata_dataset", fake_open)
    monkeypatch.setattr(lewm.FingerprintBuilder, "inventory_sha256", staticmethod(lambda path: "fp"))

    rows, fingerprints = build_canonical_manifest(
        Path("normal.lance"),
        Path("buggy.lance"),
        calibration_episode_count=2,
    )

    assert len(rows) == 4
    assert normal.read_indices == [0, 1, 2]
    assert buggy.read_indices == [0]
    assert "pixels" not in normal.accessed_keys + buggy.accessed_keys
    assert "action" not in normal.accessed_keys + buggy.accessed_keys
    calibration = {row["source_episode_id"] for row in rows if row["evaluation_role"] == "calibration_normal"}
    assert len(calibration) == 2
    assert all(row["evaluation_role"] == "evaluation" for row in rows if row["label"] == "Buggy")
    assert set(fingerprints) == {"normal_validation", "buggy_probe"}


def test_resource_telemetry_records_and_persists(tmp_path):
    telemetry = ResourceTelemetry("materialize_lance_window_manifest")
    telemetry.record("start")
    telemetry.record("done", row_count=3)

    payload = telemetry.to_dict()
    assert payload["phase"] == "materialize_lance_window_manifest"
    assert [point["checkpoint"] for point in payload["checkpoints"]] == ["start", "done"]
    assert payload["checkpoints"][1]["row_count"] == 3

    out = telemetry.write(tmp_path / "resource_telemetry.json")
    assert out.exists()
    assert "checkpoints" in out.read_text(encoding="utf-8")


def test_capture_resource_usage_returns_bounded_snapshot():
    snapshot = capture_resource_usage()

    assert snapshot["source"] in {"psutil", "resource.getrusage"}
    assert any(key in snapshot for key in ("rss_bytes", "max_rss_kib"))
