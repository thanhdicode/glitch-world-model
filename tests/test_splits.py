import csv
from pathlib import Path

from glitch_detection.manifest import (
    ClipRecord,
    LabelInterval,
    read_labels,
    read_manifest,
    write_manifest,
)
from glitch_detection.splits import (
    assign_video_splits,
    filter_labels_by_sources,
    filter_manifest_by_sources,
    filter_scores_by_sources,
    read_split_csv,
    write_split_csv,
)


def _metadata_rows() -> list[dict[str, str]]:
    return [
        {
            "source": f"{category}_{label}_{index}",
            "category": category,
            "public_label": label,
        }
        for category in ["Blinking", "Frozen Animation"]
        for label in ["Buggy", "Normal"]
        for index in range(3)
    ]


def test_assign_video_splits_is_deterministic_and_source_disjoint():
    first = assign_video_splits(_metadata_rows(), seed=42)
    second = assign_video_splits(_metadata_rows(), seed=42)

    assert first == second
    assert len({row.source for row in first}) == len(first)
    for category in ["Blinking", "Frozen Animation"]:
        for label in ["Buggy", "Normal"]:
            group_splits = {
                row.split for row in first if row.category == category and row.label == label
            }
            assert group_splits == {"train", "validation", "test"}


def test_assign_video_splits_uses_train_test_fallback_for_two_sources():
    rows = [
        {"source": f"Blinking_Buggy_{index}", "category": "Blinking", "public_label": "Buggy"}
        for index in range(2)
    ]

    splits = assign_video_splits(rows, seed=42)

    assert {row.split for row in splits} == {"train", "test"}


def test_write_and_read_split_csv_preserves_schema(tmp_path: Path):
    rows = assign_video_splits(_metadata_rows(), seed=42)
    split_path = write_split_csv(tmp_path / "split.csv", rows)

    assert read_split_csv(split_path) == rows
    assert split_path.read_text(encoding="utf-8").splitlines()[0] == "source,category,label,split"


def test_filter_manifest_labels_and_scores_by_sources(tmp_path: Path):
    manifest_path = tmp_path / "manifest.csv"
    write_manifest(
        manifest_path,
        [
            ClipRecord("a_0", "a", "a/0", 0, 3, 4, 30.0),
            ClipRecord("b_0", "b", "b/0", 0, 3, 4, 30.0),
        ],
    )
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\na,0,3,1\nb,0,3,1\n",
        encoding="utf-8",
    )
    scores_path = tmp_path / "scores.csv"
    scores_path.write_text(
        "clip_id,source,clip_dir,start_frame,end_frame,score\n"
        "a_0,a,a/0,0,3,0.8\n"
        "b_0,b,b/0,0,3,0.2\n",
        encoding="utf-8",
    )

    filtered_manifest = filter_manifest_by_sources(
        manifest_path, {"a"}, tmp_path / "a_manifest.csv"
    )
    filtered_labels = filter_labels_by_sources(labels_path, {"a"}, tmp_path / "a_labels.csv")
    filtered_scores = filter_scores_by_sources(scores_path, {"a"}, tmp_path / "a_scores.csv")

    assert [record.source for record in read_manifest(filtered_manifest)] == ["a"]
    assert read_labels(filtered_labels) == [LabelInterval("a", 0, 3, 1)]
    with filtered_scores.open("r", newline="", encoding="utf-8") as handle:
        assert [row["source"] for row in csv.DictReader(handle)] == ["a"]
