import json
from pathlib import Path

from scripts.diagnose_kaggle_submission import (
    collect_package_diagnostics,
    parse_kaggle_username,
    run_redacted_command,
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
