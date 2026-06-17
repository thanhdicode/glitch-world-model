import json
import subprocess
import sys
from pathlib import Path

from scripts.diagnose_kaggle_submission import (
    collect_package_diagnostics,
    parse_kaggle_username,
    run_redacted_command,
)
from scripts.repair_kaggle_kernel_write_path import (
    build_submission_variants,
    create_canary_package,
    discover_kaggle_executables,
    safe_file_status,
)


def test_collect_package_diagnostics_reads_metadata_and_inventory(tmp_path: Path):
    package = tmp_path / "kernel"
    package.mkdir()
    (package / "kernel.py").write_text("print('ok')\n", encoding="utf-8")
    (package / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": "owner/example",
                "code_file": "kernel.py",
                "dataset_sources": ["owner/data"],
                "enable_gpu": False,
                "is_private": True,
            }
        ),
        encoding="utf-8",
    )

    result = collect_package_diagnostics(package)

    assert result["package_exists"] is True
    assert result["metadata"]["id"] == "owner/example"
    assert result["code_file_exists"] is True
    assert result["dataset_sources"] == ["owner/data"]
    assert {item["path"] for item in result["inventory"]} == {
        "kernel-metadata.json",
        "kernel.py",
    }


def test_run_redacted_command_captures_raw_files_without_secrets(tmp_path: Path):
    secret = "secret-value-123"

    def executor(command: list[str]):
        assert command == ["kaggle", "--version"]
        return 1, f"token={secret}", f"KAGGLE_API_TOKEN={secret}"

    result = run_redacted_command(
        ["kaggle", "--version"],
        output_root=tmp_path,
        name="version",
        environment={"KAGGLE_API_TOKEN": secret},
        executor=executor,
    )

    assert result["returncode"] == 1
    assert secret not in result["stdout"]
    assert secret not in result["stderr"]
    assert secret not in (tmp_path / "version.stdout.txt").read_text(encoding="utf-8")
    assert secret not in (tmp_path / "version.stderr.txt").read_text(encoding="utf-8")


def test_parse_kaggle_username_uses_config_without_returning_token(tmp_path: Path):
    config = tmp_path / "kaggle.json"
    config.write_text(
        json.dumps({"username": "safe-user", "key": "must-not-leak"}),
        encoding="utf-8",
    )

    assert parse_kaggle_username(config) == "safe-user"


def test_discover_kaggle_executables_deduplicates_resolved_paths(tmp_path: Path):
    first = tmp_path / "one" / "kaggle.exe"
    second = tmp_path / "two" / "kaggle.exe"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"one")
    second.write_bytes(b"two")

    result = discover_kaggle_executables([first, first, second])

    assert result == [str(first.resolve()), str(second.resolve())]


def test_safe_file_status_reports_permissions_without_content(tmp_path: Path):
    config = tmp_path / "kaggle.json"
    config.write_text('{"username":"safe","key":"do-not-return"}', encoding="utf-8")

    result = safe_file_status(config)

    assert result["exists"] is True
    assert result["size_bytes"] > 0
    assert result["readable"] is True
    assert "content" not in result
    assert "do-not-return" not in json.dumps(result)


def test_create_canary_package_is_private_cpu_only_and_dataset_free(tmp_path: Path):
    root = create_canary_package(tmp_path, "owner/canary-one")
    metadata = json.loads((root / "kernel-metadata.json").read_text(encoding="utf-8"))

    assert metadata["id"] == "owner/canary-one"
    assert metadata["is_private"] is True
    assert metadata["enable_gpu"] is False
    assert metadata["enable_internet"] is False
    assert metadata["dataset_sources"] == []
    assert "heartbeat.json" in (root / "canary.py").read_text(encoding="utf-8")


def test_build_submission_variants_uses_absolute_unique_package_paths(tmp_path: Path):
    packages = [tmp_path / f"variant-{name}" for name in "abcd"]
    for package in packages:
        package.mkdir()
    variants = build_submission_variants(
        python_executable=Path("C:/Python/python.exe"),
        kaggle_executable=Path("C:/Tools/kaggle.exe"),
        clean_python=Path("C:/Clean/python.exe"),
        package_roots=packages,
    )

    assert [variant["name"] for variant in variants] == ["A", "B", "C", "D"]
    assert len({variant["package_root"] for variant in variants}) == 4
    assert all(Path(variant["package_root"]).is_absolute() for variant in variants)
    assert variants[0]["command"][:3] == [
        str(Path("C:/Python/python.exe")),
        "-c",
        "from kaggle.cli import main; main()",
    ]
    assert variants[1]["command"][1:3] == ["-m", "kaggle"]
    assert variants[2]["command"][0] == str(Path("C:/Tools/kaggle.exe"))
    assert variants[3]["command"][0] == str(Path("C:/Clean/python.exe"))


def test_repair_script_runs_as_direct_cli():
    completed = subprocess.run(
        [sys.executable, "scripts/repair_kaggle_kernel_write_path.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--variant" in completed.stdout
