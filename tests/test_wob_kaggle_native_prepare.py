import csv
import hashlib
import importlib.util
import json
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "cloud" / "wob_kaggle_native" / "prepare_wob_root.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_wob_root", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def _write_split(path: Path) -> None:
    rows = [
        {
            "dataset_id": "normal",
            "source": "NORMAL-TRAIN/ep-0000/ep-0000.tar",
            "episode_id": "n0",
            "pair_id": "n0",
            "category": "Normal",
            "label": "Normal",
            "split": "train",
            "action_mode": "real",
            "use_for_training": "True",
            "materialize": "True",
        },
        {
            "dataset_id": "normal",
            "source": "NORMAL-TRAIN/ep-0001/ep-0001.tar",
            "episode_id": "n1",
            "pair_id": "n1",
            "category": "Normal",
            "label": "Normal",
            "split": "validation",
            "action_mode": "real",
            "use_for_training": "False",
            "materialize": "True",
        },
        {
            "dataset_id": "bug",
            "source": "TEST/BlackScreen/ep-0000/ep-0000.tar",
            "episode_id": "b0",
            "pair_id": "b0",
            "category": "BlackScreen",
            "label": "Buggy",
            "split": "validation",
            "action_mode": "real",
            "use_for_training": "False",
            "materialize": "True",
        },
        {
            "dataset_id": "bug",
            "source": "TEST/BlackScreen/ep-0001/ep-0001.tar",
            "episode_id": "b1",
            "pair_id": "b1",
            "category": "BlackScreen",
            "label": "Buggy",
            "split": "test",
            "action_mode": "real",
            "use_for_training": "False",
            "materialize": "False",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_exact_nested_layout_works(tmp_path: Path):
    split = tmp_path / "split.csv"
    _write_split(split)
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    (normal_root / "NORMAL-TRAIN/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0001").mkdir(parents=True)
    (test_root / "TEST/BlackScreen/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0000/ep-0000.tar").write_bytes(b"a")
    (normal_root / "NORMAL-TRAIN/ep-0001/ep-0001.tar").write_bytes(b"b")
    (test_root / "TEST/BlackScreen/ep-0000/ep-0000.tar").write_bytes(b"c")
    output = tmp_path / "out"

    meta = MODULE.run_prepare(
        split_csv=split,
        normal_input_root=normal_root,
        test_input_root=test_root,
        output_root=output,
        mode="copy",
        phase="p0_full_nonlocked",
        no_locked=True,
    )

    assert meta["resolved_rows"] == 3
    assert meta["missing_rows"] == 0


def test_flattened_unique_basename_layout_works(tmp_path: Path):
    split = tmp_path / "split.csv"
    _write_split(split)
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    normal_root.mkdir()
    test_root.mkdir()
    (normal_root / "ep-0000.tar").write_bytes(b"a")
    (normal_root / "ep-0001.tar").write_bytes(b"b")
    (test_root / "ep-0000.tar").write_bytes(b"c")

    meta = MODULE.run_prepare(
        split_csv=split,
        normal_input_root=normal_root,
        test_input_root=test_root,
        output_root=tmp_path / "out",
        mode="copy",
        phase="p0_full_nonlocked",
        no_locked=True,
    )

    assert meta["resolved_rows"] == 3


def test_ambiguous_flattened_basename_fails(tmp_path: Path):
    split = tmp_path / "split.csv"
    _write_split(split)
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    (normal_root / "a").mkdir(parents=True)
    (normal_root / "b").mkdir(parents=True)
    (test_root / "c").mkdir(parents=True)
    (normal_root / "a/ep-0000.tar").write_bytes(b"a")
    (normal_root / "b/ep-0000.tar").write_bytes(b"b")
    (normal_root / "ep-0001.tar").write_bytes(b"c")
    (test_root / "c/ep-0000.tar").write_bytes(b"d")

    try:
        MODULE.run_prepare(
            split_csv=split,
            normal_input_root=normal_root,
            test_input_root=test_root,
            output_root=tmp_path / "out",
            mode="copy",
            phase="p0_full_nonlocked",
            no_locked=True,
        )
    except ValueError as exc:
        assert "Ambiguous" in str(exc)
    else:
        raise AssertionError("Expected ambiguous flattened basename failure")


def test_p1_train_only_excludes_validation_buggy(tmp_path: Path):
    split = tmp_path / "split.csv"
    _write_split(split)
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    (normal_root / "NORMAL-TRAIN/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0001").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0000/ep-0000.tar").write_bytes(b"a")
    (normal_root / "NORMAL-TRAIN/ep-0001/ep-0001.tar").write_bytes(b"b")

    meta = MODULE.run_prepare(
        split_csv=split,
        normal_input_root=normal_root,
        test_input_root=test_root,
        output_root=tmp_path / "out",
        mode="copy",
        phase="p1_train_only",
        no_locked=True,
    )

    assert meta["selected_rows"] == 2
    assert meta["resolved_rows"] == 2


def test_locked_rows_are_skipped(tmp_path: Path):
    split = tmp_path / "split.csv"
    _write_split(split)
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    (normal_root / "NORMAL-TRAIN/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0001").mkdir(parents=True)
    (test_root / "TEST/BlackScreen/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0000/ep-0000.tar").write_bytes(b"a")
    (normal_root / "NORMAL-TRAIN/ep-0001/ep-0001.tar").write_bytes(b"b")
    (test_root / "TEST/BlackScreen/ep-0000/ep-0000.tar").write_bytes(b"c")

    meta = MODULE.run_prepare(
        split_csv=split,
        normal_input_root=normal_root,
        test_input_root=test_root,
        output_root=tmp_path / "out",
        mode="copy",
        phase="p0_full_nonlocked",
        no_locked=True,
    )

    assert meta["locked_rows_skipped"] == 1


def test_manifest_and_metadata_are_deterministic(tmp_path: Path):
    split = tmp_path / "split.csv"
    _write_split(split)
    normal_root = tmp_path / "normal"
    test_root = tmp_path / "test"
    (normal_root / "NORMAL-TRAIN/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0001").mkdir(parents=True)
    (test_root / "TEST/BlackScreen/ep-0000").mkdir(parents=True)
    (normal_root / "NORMAL-TRAIN/ep-0000/ep-0000.tar").write_bytes(b"a")
    (normal_root / "NORMAL-TRAIN/ep-0001/ep-0001.tar").write_bytes(b"b")
    (test_root / "TEST/BlackScreen/ep-0000/ep-0000.tar").write_bytes(b"c")

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    meta1 = MODULE.run_prepare(
        split_csv=split,
        normal_input_root=normal_root,
        test_input_root=test_root,
        output_root=out1,
        mode="copy",
        phase="p0_full_nonlocked",
        no_locked=True,
    )
    meta2 = MODULE.run_prepare(
        split_csv=split,
        normal_input_root=normal_root,
        test_input_root=test_root,
        output_root=out2,
        mode="copy",
        phase="p0_full_nonlocked",
        no_locked=True,
    )

    sha1 = hashlib.sha256((out1 / "wob_root_manifest.csv").read_bytes()).hexdigest()
    sha2 = hashlib.sha256((out2 / "wob_root_manifest.csv").read_bytes()).hexdigest()
    assert sha1 == sha2 == meta1["manifest_sha256"] == meta2["manifest_sha256"]
    assert json.loads((out1 / "wob_root_metadata.json").read_text()) == json.loads(
        (out2 / "wob_root_metadata.json").read_text()
    )
