import json
from pathlib import Path

from glitch_detection.compare_experiments import build_comparison_rows, write_comparison_markdown


def test_build_comparison_rows(tmp_path: Path):
    frame_metrics = tmp_path / "frame.json"
    feature_metrics = tmp_path / "feature.json"
    frame_metrics.write_text(
        json.dumps({"f1": 0.8, "auroc": 0.9, "precision": 1.0}), encoding="utf-8"
    )
    feature_metrics.write_text(
        json.dumps({"f1": 0.7, "auroc": 0.85, "precision": 0.75}), encoding="utf-8"
    )

    rows = build_comparison_rows(
        [
            ("FrameDiff", frame_metrics),
            ("FeatureDistance", feature_metrics),
        ]
    )

    assert rows[0]["name"] == "FrameDiff"
    assert rows[0]["f1"] == 0.8
    assert rows[1]["auroc"] == 0.85


def test_write_comparison_markdown(tmp_path: Path):
    output_path = tmp_path / "comparison.md"
    write_comparison_markdown(
        [{"name": "FrameDiff", "f1": 0.8, "auroc": 0.9, "precision": 1.0, "recall": 0.7}],
        output_path,
    )

    text = output_path.read_text(encoding="utf-8")
    assert "# Experiment Comparison" in text
    assert "| FrameDiff | 1 | 0.7 | 0.8 |" in text
