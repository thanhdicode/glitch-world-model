from pathlib import Path

from glitch_detection.manifest import ClipRecord, read_labels, read_manifest, write_manifest
from glitch_detection.tempglitch import (
    combine_manifests,
    encode_tempglitch_video_url,
    normalize_tempglitch_label,
    parse_tempglitch_video_url,
    write_tempglitch_full_video_labels,
)


def test_parse_tempglitch_video_url_handles_spaces_and_trailing_label_space():
    ref = parse_tempglitch_video_url(
        "https://huggingface.co/datasets/asgaardlab/TempGlitch/resolve/abc123/"
        "Stuck%20in%20Place/Buggy%20/Godot_Stuck_in_Place_1.mp4"
    )
    assert ref.dataset_revision == "abc123"
    assert ref.category == "Stuck in Place"
    assert ref.public_label_raw == "Buggy "
    assert ref.public_label == "Buggy"
    assert ref.source_name == "Godot_Stuck_in_Place_1"
    assert normalize_tempglitch_label("Normal") == "Normal"


def test_encode_tempglitch_video_url_quotes_category_spaces():
    url = (
        "https://huggingface.co/datasets/asgaardlab/TempGlitch/resolve/abc123/"
        "Frozen Animation/Buggy/video 1.mp4"
    )

    assert encode_tempglitch_video_url(url).endswith("/Frozen%20Animation/Buggy/video%201.mp4")


def test_combine_manifests_and_write_tempglitch_labels(tmp_path: Path):
    manifest_a = tmp_path / "a" / "manifest.csv"
    manifest_b = tmp_path / "b" / "manifest.csv"
    write_manifest(
        manifest_a,
        [
            ClipRecord(
                clip_id="video_a_000000",
                source="video_a",
                clip_dir="clips/video_a_000000",
                start_frame=0,
                end_frame=3,
                frame_count=4,
                fps=60.0,
            ),
            ClipRecord(
                clip_id="video_a_000001",
                source="video_a",
                clip_dir="clips/video_a_000001",
                start_frame=4,
                end_frame=7,
                frame_count=4,
                fps=60.0,
            ),
        ],
    )
    write_manifest(
        manifest_b,
        [
            ClipRecord(
                clip_id="video_b_000000",
                source="video_b",
                clip_dir="clips/video_b_000000",
                start_frame=0,
                end_frame=3,
                frame_count=4,
                fps=60.0,
            )
        ],
    )

    combined_manifest_path = combine_manifests(
        [manifest_a, manifest_b],
        tmp_path / "combined" / "manifest.csv",
    )
    combined_records = read_manifest(combined_manifest_path)
    assert [record.source for record in combined_records] == ["video_a", "video_a", "video_b"]

    metadata_path = tmp_path / "metadata.csv"
    metadata_path.write_text(
        "\n".join(
            [
                "row_idx,category,public_label_raw,public_label,is_glitch,source,file_name,dataset_revision,video_url,local_video_path",
                "0,Blinking,Buggy,Buggy,1,video_a,video_a.mp4,abc,url,videos/Blinking/Buggy/video_a.mp4",
                "1,Blinking,Normal,Normal,0,video_b,video_b.mp4,abc,url,videos/Blinking/Normal/video_b.mp4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    labels_path = write_tempglitch_full_video_labels(
        metadata_path=metadata_path,
        manifest_path=combined_manifest_path,
        output_path=tmp_path / "labels.csv",
    )
    labels = read_labels(labels_path)
    assert len(labels) == 1
    assert labels[0].source == "video_a"
    assert labels[0].start_frame == 0
    assert labels[0].end_frame == 7
