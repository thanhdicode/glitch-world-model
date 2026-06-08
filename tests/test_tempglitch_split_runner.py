from pathlib import Path

from glitch_detection.manifest import ClipRecord, write_manifest
from glitch_detection.splits import SplitRecord
from scripts.run_tempglitch_split_experiments import normal_train_records


def test_normal_train_records_excludes_buggy_and_non_train_sources(tmp_path: Path):
    manifest_path = tmp_path / "train_manifest.csv"
    write_manifest(
        manifest_path,
        [
            ClipRecord("normal_0", "normal", "normal/0", 0, 3, 4, 30.0),
            ClipRecord("buggy_0", "buggy", "buggy/0", 0, 3, 4, 30.0),
            ClipRecord("validation_normal_0", "validation_normal", "validation/0", 0, 3, 4, 30.0),
        ],
    )
    split_records = [
        SplitRecord("normal", "Blinking", "Normal", "train"),
        SplitRecord("buggy", "Blinking", "Buggy", "train"),
        SplitRecord("validation_normal", "Blinking", "Normal", "validation"),
    ]

    records = normal_train_records(manifest_path, split_records)

    assert [record.source for record in records] == ["normal"]
