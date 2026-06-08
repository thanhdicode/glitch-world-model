import json
from pathlib import Path

from glitch_detection.dataset_report import build_report, write_markdown_report


def test_build_report_summarizes_experiment(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    manifest_path.write_text(
        "clip_id,source,clip_dir,start_frame,end_frame,frame_count,fps\n"
        "c0,demo,clips/c0,0,7,8,30\n"
        "c1,demo,clips/c1,8,15,8,30\n",
        encoding="utf-8",
    )
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\ndemo,8,15,1\n",
        encoding="utf-8",
    )
    scores_path = tmp_path / "scores.csv"
    scores_path.write_text(
        "clip_id,source,clip_dir,start_frame,end_frame,score\n"
        "c0,demo,clips/c0,0,7,0.1\n"
        "c1,demo,clips/c1,8,15,0.8\n",
        encoding="utf-8",
    )
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"f1": 1.0, "auroc": 1.0}), encoding="utf-8")

    report = build_report(
        name="demo",
        manifest_path=manifest_path,
        labels_path=labels_path,
        scores_path=scores_path,
        metrics_path=metrics_path,
    )

    assert report["name"] == "demo"
    assert report["clip_count"] == 2
    assert report["positive_clip_count"] == 1
    assert report["score_min"] == 0.1
    assert report["score_max"] == 0.8
    assert report["metrics"]["f1"] == 1.0


def test_write_markdown_report(tmp_path: Path):
    output_path = tmp_path / "report.md"
    write_markdown_report(
        {
            "name": "demo",
            "clip_count": 2,
            "positive_clip_count": 1,
            "score_min": 0.1,
            "score_mean": 0.45,
            "score_max": 0.8,
            "metrics": {"f1": 1.0, "auroc": 1.0},
        },
        output_path,
    )

    text = output_path.read_text(encoding="utf-8")
    assert "# Experiment Report: demo" in text
    assert "| F1 | 1 |" in text
