from pathlib import Path

from PIL import Image

from glitch_detection.manifest import ClipRecord
from glitch_detection.repeated_eval import fit_scorer_for_split, train_normal_records
from glitch_detection.splits import SplitRecord


def _write_clip(path: Path, values: list[int]) -> None:
    path.mkdir(parents=True)
    for index, value in enumerate(values):
        Image.new("RGB", (4, 4), color=(value, value, value)).save(path / f"{index:03d}.png")


def _records(tmp_path: Path) -> tuple[list[ClipRecord], list[SplitRecord]]:
    records = []
    split_rows = []
    for source, label, split, values in [
        ("train_normal", "Normal", "train", [0, 1, 2]),
        ("train_buggy", "Buggy", "train", [0, 50, 100]),
        ("validation_normal", "Normal", "validation", [3, 4, 5]),
        ("test_normal", "Normal", "test", [6, 7, 8]),
    ]:
        clip_dir = tmp_path / source
        _write_clip(clip_dir, values)
        records.append(ClipRecord(f"{source}_0", source, str(clip_dir), 0, 2, 3, 30.0))
        split_rows.append(SplitRecord(source, "Blinking", label, split))
    return records, split_rows


def test_train_normal_records_excludes_buggy_validation_and_test(tmp_path: Path):
    records, split_rows = _records(tmp_path)

    selected = train_normal_records(records, split_rows)

    assert [record.source for record in selected] == ["train_normal"]


def test_fitted_scorers_record_train_normal_only_fit_metadata(tmp_path: Path):
    records, split_rows = _records(tmp_path)

    for scorer in ["feature_distance", "mini_latent"]:
        fitted = fit_scorer_for_split(scorer, records, split_rows)

        assert fitted.fit_metadata == {
            "scorer": scorer,
            "fit_split": "train",
            "train_sources_used": ["train_normal"],
            "train_normal_clip_count": 1,
            "validation_sources_count": 1,
            "test_sources_count": 1,
            "labels_used_for_fitting": True,
        }


def test_frame_diff_records_that_no_fitting_or_labels_are_used(tmp_path: Path):
    records, split_rows = _records(tmp_path)

    fitted = fit_scorer_for_split("frame_diff", records, split_rows)

    assert fitted.fit_metadata["fit_split"] == "none"
    assert fitted.fit_metadata["train_sources_used"] == []
    assert fitted.fit_metadata["labels_used_for_fitting"] is False
