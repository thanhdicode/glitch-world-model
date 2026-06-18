import importlib.util
import tarfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "cloud" / "wob_kaggle_native" / "common.py"
SPEC = importlib.util.spec_from_file_location("wob_kaggle_common", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_detect_kaggle_roots_finds_nested_dataset_layout(tmp_path: Path):
    base = tmp_path / "kaggle" / "input" / "datasets" / "benedictwilkinsai"
    normal = base / "world-of-bugs-normal" / "NORMAL-TRAIN"
    test = base / "world-of-bugs-test" / "TEST"
    normal.mkdir(parents=True)
    test.mkdir(parents=True)

    detected_normal, detected_test = MODULE.detect_kaggle_roots(tmp_path / "kaggle" / "input")

    assert detected_normal == normal.parent
    assert detected_test == test.parent


def test_resolve_split_csv_prefers_tracked_config(tmp_path: Path):
    repo = tmp_path
    tracked = repo / "configs/wob_protocol"
    tracked.mkdir(parents=True)
    (tracked / "split.csv").write_text("tracked\n", encoding="utf-8")

    resolved = MODULE.resolve_split_csv(repo)

    assert resolved == tracked / "split.csv"


def test_write_debug_tarball_excludes_raw_tar_files(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "ok.txt").write_text("ok", encoding="utf-8")
    (root / "raw.tar").write_bytes(b"x")
    output = tmp_path / "bundle.tar.gz"

    MODULE.write_debug_tarball(output, [(root, "root")], exclude_suffixes=(".tar",))

    with tarfile.open(output, "r:gz") as archive:
        names = archive.getnames()
    assert "root/ok.txt" in names
    assert "root/raw.tar" not in names


def test_readme_references_one_section_entrypoint():
    readme = (
        Path(__file__).resolve().parents[1] / "cloud" / "wob_kaggle_native" / "README.md"
    ).read_text(encoding="utf-8")
    assert "run_kaggle_wob_p0_all.sh" in readme
    assert "%%bash" in readme


def test_scripts_avoid_find_head_pipefail_pattern():
    root = Path(__file__).resolve().parents[1] / "cloud" / "wob_kaggle_native"
    for script_name in [
        "run_kaggle_wob_p0_all.sh",
        "preflight.sh",
        "prepare_wob_root.sh",
        "run_wob_p0_audit.sh",
    ]:
        text = (root / script_name).read_text(encoding="utf-8")
        assert "find " not in text or "head" not in text
