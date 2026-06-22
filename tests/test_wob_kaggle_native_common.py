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


def test_detect_kaggle_roots_accepts_train_named_dataset_slug(tmp_path: Path):
    normal = tmp_path / "kaggle" / "input" / "world-of-bugs-train" / "NORMAL-TRAIN"
    test = tmp_path / "kaggle" / "input" / "world-of-bugs-test" / "TEST"
    normal.mkdir(parents=True)
    test.mkdir(parents=True)

    detected_normal, detected_test = MODULE.detect_kaggle_roots(tmp_path / "kaggle" / "input")

    assert detected_normal == normal.parent
    assert detected_test == test.parent


def test_detect_kaggle_roots_exact_match_avoids_recursive_scan(tmp_path: Path, monkeypatch):
    normal = tmp_path / "kaggle" / "input" / "world-of-bugs-normal" / "NORMAL-TRAIN"
    test = tmp_path / "kaggle" / "input" / "world-of-bugs-test" / "TEST"
    normal.mkdir(parents=True)
    test.mkdir(parents=True)

    def explode(self: Path, pattern: str):
        raise AssertionError(f"unexpected recursive scan for {self} / {pattern}")

    monkeypatch.setattr(Path, "rglob", explode)

    detected_normal, detected_test = MODULE.detect_kaggle_roots(tmp_path / "kaggle" / "input")

    assert detected_normal == normal.parent
    assert detected_test == test.parent


def test_detect_kaggle_roots_prefers_environment_overrides(tmp_path: Path, monkeypatch):
    normal = tmp_path / "mounted-normal"
    test = tmp_path / "mounted-test"
    (normal / "NORMAL-TRAIN").mkdir(parents=True)
    (test / "TEST").mkdir(parents=True)
    monkeypatch.setenv("NORMAL_INPUT_ROOT", str(normal))
    monkeypatch.setenv("TEST_INPUT_ROOT", str(test))

    detected_normal, detected_test = MODULE.detect_kaggle_roots(tmp_path / "unused-input")

    assert detected_normal == normal
    assert detected_test == test


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


def test_discover_r5_wob_input_overrides_reports_direct_seed_tarballs(tmp_path: Path):
    input_root = tmp_path / "kaggle" / "input"
    normal = input_root / "world-of-bugs-normal" / "NORMAL-TRAIN"
    test = input_root / "world-of-bugs-test" / "TEST"
    normal.mkdir(parents=True)
    test.mkdir(parents=True)
    artifacts = input_root / "wob-seed-artifacts"
    artifacts.mkdir(parents=True)
    for seed in (42, 43, 44):
        (artifacts / f"wob_seed{seed}_artifacts.tar.gz").write_bytes(b"seed")
        (artifacts / f"wob_seed{seed}_artifacts.tar.gz.sha256").write_text(
            "deadbeef\n", encoding="utf-8"
        )

    discovered = MODULE.discover_r5_wob_input_overrides(input_root)

    assert discovered["NORMAL_INPUT_ROOT"] == str(normal.parent)
    assert discovered["TEST_INPUT_ROOT"] == str(test.parent)
    assert discovered["WOB_SEED42_TARBALL"].endswith("wob_seed42_artifacts.tar.gz")
    assert discovered["WOB_SEED44_SHA256"].endswith("wob_seed44_artifacts.tar.gz.sha256")


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
