from pathlib import Path

from glitch_detection.manifest import (
    ClipRecord,
    LabelInterval,
    clip_has_glitch,
    read_labels,
    read_manifest,
    write_manifest,
)


def test_manifest_round_trip(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    records = [
        ClipRecord(
            clip_id="clip_000001",
            source="demo",
            clip_dir="clips/clip_000001",
            start_frame=4,
            end_frame=19,
            frame_count=16,
            fps=30.0,
        )
    ]

    write_manifest(manifest_path, records)

    assert read_manifest(manifest_path) == records


def test_read_labels_and_overlap(tmp_path: Path):
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\ndemo,10,20,1\ndemo,30,40,0\nother,0,99,1\n",
        encoding="utf-8",
    )
    labels = read_labels(labels_path)

    assert labels == [
        LabelInterval(source="demo", start_frame=10, end_frame=20, label=1),
        LabelInterval(source="other", start_frame=0, end_frame=99, label=1),
    ]
    assert clip_has_glitch("demo", 0, 9, labels) is False
    assert clip_has_glitch("demo", 9, 12, labels) is True
    assert clip_has_glitch("demo", 21, 25, labels) is False
    assert clip_has_glitch("other", 9, 12, labels) is True
