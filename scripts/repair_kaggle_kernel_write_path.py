import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    from datetime import timezone

    UTC = timezone.utc
from typing import Any

try:
    from scripts.diagnose_kaggle_submission import (
        parse_kaggle_username,
        run_redacted_command,
    )
except ModuleNotFoundError:
    from diagnose_kaggle_submission import parse_kaggle_username, run_redacted_command


def discover_kaggle_executables(candidates: list[Path] | None = None) -> list[str]:
    if candidates is None:
        candidates = []
        path_executable = shutil.which("kaggle")
        if path_executable:
            candidates.append(Path(path_executable))
        candidates.extend(
            [
                Path(sys.executable).parent / "Scripts" / "kaggle.exe",
                Path(os.environ.get("APPDATA", ""))
                / "Python"
                / f"Python{sys.version_info.major}{sys.version_info.minor}"
                / "Scripts"
                / "kaggle.exe",
            ]
        )
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate.is_file():
            continue
        resolved = str(candidate.resolve())
        key = resolved.casefold()
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def safe_file_status(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        return {"path": str(resolved), "exists": False}
    file_stat = resolved.stat()
    return {
        "path": str(resolved),
        "exists": True,
        "size_bytes": file_stat.st_size,
        "readable": os.access(resolved, os.R_OK),
        "writable": os.access(resolved, os.W_OK),
        "mode": stat.filemode(file_stat.st_mode),
    }


def create_canary_package(root: Path, slug: str) -> Path:
    package_root = (root / slug.split("/", 1)[1]).resolve()
    package_root.mkdir(parents=True, exist_ok=False)
    script = """import json
from datetime import datetime, timezone
from pathlib import Path

Path("/kaggle/working/heartbeat.json").write_text(
    json.dumps(
        {"status": "ok", "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    ) + "\\n",
    encoding="utf-8",
)
print("CANARY_HEARTBEAT_WRITTEN")
"""
    metadata = {
        "id": slug,
        "title": slug.split("/", 1)[1],
        "code_file": "canary.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    (package_root / "canary.py").write_text(script, encoding="utf-8")
    (package_root / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return package_root


def build_submission_variants(
    *,
    python_executable: Path,
    kaggle_executable: Path,
    clean_python: Path,
    package_roots: list[Path],
) -> list[dict[str, Any]]:
    roots = [str(path.resolve()) for path in package_roots]
    python_text = str(python_executable)
    kaggle_text = str(kaggle_executable)
    clean_text = str(clean_python)
    return [
        {
            "name": "A",
            "package_root": roots[0],
            "command": [
                python_text,
                "-c",
                "from kaggle.cli import main; main()",
                "kernels",
                "push",
                "-p",
                roots[0],
            ],
        },
        {
            "name": "B",
            "package_root": roots[1],
            "command": [
                python_text,
                "-m",
                "kaggle",
                "kernels",
                "push",
                "-p",
                roots[1],
            ],
        },
        {
            "name": "C",
            "package_root": roots[2],
            "command": [
                kaggle_text,
                "kernels",
                "push",
                "-p",
                roots[2],
            ],
        },
        {
            "name": "D",
            "package_root": roots[3],
            "command": [
                clean_text,
                "-m",
                "kaggle",
                "kernels",
                "push",
                "-p",
                roots[3],
            ],
        },
    ]


def _run(command: list[str]) -> tuple[int, str, str]:
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


def _diagnostics(args: argparse.Namespace) -> dict[str, Any]:
    import kaggle

    output_root = args.output_root.resolve()
    raw_root = output_root / "raw"
    executables = discover_kaggle_executables()
    kaggle_executable = executables[0] if executables else None
    config_dir_text = os.environ.get("KAGGLE_CONFIG_DIR")
    config_dir = Path(config_dir_text) if config_dir_text else Path.home() / ".kaggle"
    config_path = config_dir / "kaggle.json"
    commands: dict[str, Any] = {}
    if kaggle_executable:
        commands = {
            "pip_show_kaggle": run_redacted_command(
                [sys.executable, "-m", "pip", "show", "kaggle"],
                output_root=raw_root,
                name="pip_show_kaggle",
            ),
            "kernels_list": run_redacted_command(
                [kaggle_executable, "kernels", "list", "--mine"],
                output_root=raw_root,
                name="kernels_list",
            ),
            "datasets_list": run_redacted_command(
                [kaggle_executable, "datasets", "list", "--mine"],
                output_root=raw_root,
                name="datasets_list",
            ),
            "dataset_status": run_redacted_command(
                [kaggle_executable, "datasets", "status", args.dataset_slug],
                output_root=raw_root,
                name="dataset_status",
            ),
        }
    payload = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "os": platform.platform(),
        "shell": os.environ.get("COMSPEC") or os.environ.get("SHELL"),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "kaggle_package_version": kaggle.__version__,
        "kaggle_executables": executables,
        "multiple_kaggle_executables": len(executables) > 1,
        "kaggle_config_dir_env": config_dir_text,
        "kaggle_config": safe_file_status(config_path),
        "authenticated_username": parse_kaggle_username(config_path),
        "commands": commands,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "write_path_diagnostics.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def _canary_slug(variant: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"huynhdieuthanh/lewm-submit-canary-{variant.lower()}-{timestamp}"


def _check_remote(
    kaggle_executable: str,
    slug: str,
    *,
    output_root: Path,
    variant: str,
) -> dict[str, Any]:
    short_slug = slug.split("/", 1)[1]
    list_result = run_redacted_command(
        [kaggle_executable, "kernels", "list", "--mine", "-s", short_slug],
        output_root=output_root,
        name=f"variant_{variant}_list",
    )
    status_result = run_redacted_command(
        [kaggle_executable, "kernels", "status", slug],
        output_root=output_root,
        name=f"variant_{variant}_status",
    )
    appeared = "not found" not in list_result["stdout"].lower() and bool(
        list_result["stdout"].strip()
    )
    return {
        "appeared": appeared,
        "list": list_result,
        "status": status_result,
    }


def _run_variant(args: argparse.Namespace, diagnostics: dict[str, Any]) -> dict[str, Any]:
    executables = diagnostics["kaggle_executables"]
    if not executables:
        raise FileNotFoundError("No Kaggle executable is available.")
    if args.variant == "D" and not args.clean_python:
        raise ValueError("--clean-python is required for variant D.")

    canary_root = args.output_root.resolve() / "canaries"
    package_roots: list[Path] = []
    slugs: list[str] = []
    for name in "ABCD":
        slug = _canary_slug(name)
        slugs.append(slug)
        package_roots.append(create_canary_package(canary_root, slug))
        time.sleep(1.05)
    clean_python = args.clean_python or Path(sys.executable)
    variants = build_submission_variants(
        python_executable=Path(sys.executable),
        kaggle_executable=Path(executables[0]),
        clean_python=clean_python,
        package_roots=package_roots,
    )
    selected_index = "ABCD".index(args.variant)
    selected = variants[selected_index]
    selected["slug"] = slugs[selected_index]
    raw_root = args.output_root.resolve() / "raw"
    push = run_redacted_command(
        selected["command"],
        output_root=raw_root,
        name=f"variant_{args.variant}_push",
    )
    time.sleep(args.poll_delay)
    remote = _check_remote(
        executables[0],
        selected["slug"],
        output_root=raw_root,
        variant=args.variant,
    )
    result = {**selected, "push": push, "remote": remote}
    (args.output_root.resolve() / f"variant_{args.variant}_result.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs/gate6/diagnostics/write_path_repair"),
    )
    parser.add_argument(
        "--dataset-slug",
        default="huynhdieuthanh/lewm-tempglitch-gate6-pilot",
    )
    parser.add_argument("--variant", choices=list("ABCD"))
    parser.add_argument("--clean-python", type=Path)
    parser.add_argument("--poll-delay", type=float, default=30.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    diagnostics = _diagnostics(args)
    result: dict[str, Any] = {"diagnostics": diagnostics}
    if args.variant:
        result["canary"] = _run_variant(args, diagnostics)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
