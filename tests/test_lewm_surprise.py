import csv
from pathlib import Path

import pytest

from glitch_detection.lewm_surprise import (
    LeWMUnavailableError,
    aggregate_scores,
    score_direction_check,
    score_manifest,
)
from glitch_detection.manifest import ClipRecord, write_manifest
from glitch_detection.score_clips import available_scorers
from scripts.run_lewm_scoring import main


def test_lewm_surprise_is_registered():
    assert "lewm_surprise" in available_scorers()


@pytest.mark.parametrize(
    ("aggregation", "expected"),
    [("mean", 2.5), ("max", 4.0), ("topk_mean", 3.0), ("top2_mean", 3.5)],
)
def test_aggregation_modes(aggregation: str, expected: float):
    assert aggregate_scores([1.0, 2.0, 3.0, 4.0], aggregation) == expected


def test_percentile95_aggregation():
    values = [float(v) for v in range(1, 101)]
    assert aggregate_scores(values, "percentile95") == pytest.approx(95.05)


def test_max_plus_std_aggregation():
    import numpy as np

    values = [1.0, 2.0, 3.0, 4.0]
    expected = 4.0 + 0.5 * float(np.std(np.asarray(values)))
    assert aggregate_scores(values, "max_plus_std") == pytest.approx(expected)


def test_unknown_aggregation_is_rejected():
    with pytest.raises(ValueError, match="Unknown LeWM surprise aggregation"):
        aggregate_scores([1.0, 2.0], "does_not_exist")


def test_topk_mean_uses_available_values():
    assert aggregate_scores([1.0, 3.0], "topk_mean") == 2.0


def test_non_finite_scores_are_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        aggregate_scores([1.0, float("nan")], "mean")


def test_score_direction_structure():
    result = score_direction_check([0.1, 0.4])
    assert result["higher_is_more_anomalous"] is True
    assert result["finite"] is True


def test_real_action_mode_fails_without_action_source(tmp_path: Path):
    checkpoint = tmp_path / "weights.pt"
    config = tmp_path / "config.json"
    checkpoint.write_bytes(b"weights")
    config.write_text("{}")
    with pytest.raises(LeWMUnavailableError, match="synchronized action"):
        score_manifest(
            tmp_path / "manifest.csv",
            None,
            tmp_path / "scores.csv",
            checkpoint,
            config,
            action_mode="real",
        )


def test_run_scoring_dry_run_does_not_score(tmp_path: Path, capsys):
    clip = tmp_path / "clip"
    clip.mkdir()
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [ClipRecord("c", "s", str(clip), 0, 3, 4, 30.0)])
    checkpoint = tmp_path / "weights.pt"
    config = tmp_path / "config.json"
    checkpoint.write_bytes(b"weights")
    config.write_text("{}")
    output = tmp_path / "scores.csv"

    main(
        [
            "--manifest",
            str(manifest),
            "--output",
            str(output),
            "--checkpoint",
            str(checkpoint),
            "--config",
            str(config),
            "--dry-run",
        ]
    )

    assert '"status": "dry-run"' in capsys.readouterr().out
    assert not output.exists()


def test_run_scoring_rejects_hash_mismatch(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "clip_id",
                "source",
                "clip_dir",
                "start_frame",
                "end_frame",
                "frame_count",
                "fps",
            ],
        )
        writer.writeheader()
    checkpoint = tmp_path / "weights.pt"
    config = tmp_path / "config.json"
    checkpoint.write_bytes(b"weights")
    config.write_text("{}")

    with pytest.raises(ValueError, match="SHA-256"):
        main(
            [
                "--manifest",
                str(manifest),
                "--output",
                str(tmp_path / "scores.csv"),
                "--checkpoint",
                str(checkpoint),
                "--config",
                str(config),
                "--expected-sha256",
                "wrong",
                "--dry-run",
            ]
        )
