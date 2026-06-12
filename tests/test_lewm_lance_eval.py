from __future__ import annotations

import pytest

from glitch_detection.lewm_lance_eval import (
    canonical_rows_from_samples,
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
