import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from glitch_detection.kaggle_automation import SecurityGuard

Executor = Callable[[list[str]], tuple[int, str, str]]


def _default_executor(command: list[str]) -> tuple[int, str, str]:
    environment = dict(os.environ)
    environment.setdefault("PYTHONUTF8", "1")
    environment.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    return completed.returncode, completed.stdout, completed.stderr


def parse_kaggle_username(config_path: Path) -> str | None:
    if not config_path.is_file():
        return None
    payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    username = payload.get("username")
    return str(username) if username else None


def collect_package_diagnostics(package_root: Path) -> dict[str, Any]:
    root = package_root.resolve()
    metadata_path = root / "kernel-metadata.json"
    metadata: dict[str, Any] = {}
    metadata_error = None
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            metadata_error = str(exc)
    code_file = metadata.get("code_file")
    inventory = (
        [
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(root.rglob("*"))
            if path.is_file()
        ]
        if root.is_dir()
        else []
    )
    return {
        "package_root": str(root),
        "package_exists": root.is_dir(),
        "metadata_path": str(metadata_path),
        "metadata_exists": metadata_path.is_file(),
        "metadata_error": metadata_error,
        "metadata": {
            key: metadata.get(key)
            for key in (
                "id",
                "title",
                "code_file",
                "language",
                "kernel_type",
                "is_private",
                "enable_gpu",
                "enable_internet",
            )
            if key in metadata
        },
        "code_file_exists": bool(code_file and (root / str(code_file)).is_file()),
        "dataset_sources": metadata.get("dataset_sources", []),
        "inventory": inventory,
        "total_size_bytes": sum(item["size_bytes"] for item in inventory),
    }


def run_redacted_command(
    command: list[str],
    *,
    output_root: Path,
    name: str,
    environment: dict[str, str] | None = None,
    executor: Executor | None = None,
) -> dict[str, Any]:
    guard = SecurityGuard(environment=environment)
    guard.scan_command(" ".join(command))
    returncode, stdout, stderr = (executor or _default_executor)(command)
    stdout = guard.redact(stdout)
    stderr = guard.redact(stderr)
    output_root.mkdir(parents=True, exist_ok=True)
    stdout_path = output_root / f"{name}.stdout.txt"
    stderr_path = output_root / f"{name}.stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        "command": command,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_path": str(stdout_path.resolve()),
        "stderr_path": str(stderr_path.resolve()),
    }


def _kaggle_executable() -> str:
    executable = shutil.which("kaggle")
    if executable:
        return executable
    candidate = Path(sys.executable).parent / "Scripts" / "kaggle.exe"
    if candidate.is_file():
        return str(candidate)
    user_candidate = (
        Path(os.environ.get("APPDATA", ""))
        / "Python"
        / f"Python{sys.version_info.major}{sys.version_info.minor}"
        / "Scripts"
        / "kaggle.exe"
    )
    if user_candidate.is_file():
        return str(user_candidate)
    raise FileNotFoundError("Kaggle executable was not found.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--dataset-slug", required=True)
    parser.add_argument("--kernel-slug", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/gate6/diagnostics/kaggle_submission_diagnosis.json"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_root = args.output.parent / "raw"
    kaggle_exe = _kaggle_executable()
    config_dir = Path(os.environ.get("KAGGLE_CONFIG_DIR", Path.home() / ".kaggle")).resolve()
    config_path = config_dir / "kaggle.json"

    import kaggle

    commands = {
        "version": [kaggle_exe, "--version"],
        "kernels_list": [kaggle_exe, "kernels", "list", "--mine"],
        "datasets_list": [kaggle_exe, "datasets", "list", "--mine"],
        "dataset_status": [kaggle_exe, "datasets", "status", args.dataset_slug],
        "kernel_status": [kaggle_exe, "kernels", "status", args.kernel_slug],
    }
    results = {
        name: run_redacted_command(command, output_root=output_root, name=name)
        for name, command in commands.items()
    }
    payload = {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "kaggle_version": kaggle.__version__,
        "kaggle_executable": kaggle_exe,
        "kaggle_config_dir": str(config_dir),
        "authenticated_username": parse_kaggle_username(config_path),
        "package": collect_package_diagnostics(args.package_root),
        "planned_push_command": [
            kaggle_exe,
            "kernels",
            "push",
            "-p",
            str(args.package_root.resolve()),
        ],
        "commands": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
