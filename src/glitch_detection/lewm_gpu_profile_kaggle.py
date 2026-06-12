from __future__ import annotations

import io
import json
import re
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import FingerprintBuilder, SecurityGuard, SecurityViolation
from .lewm_gpu_profile import (
    LeWMGPUProfileConfig,
    build_dataset_manifest,
    build_profile_fingerprint,
)
from .lewm_kaggle import validate_kaggle_slug

TRAIN_DATASET_NAME = "tempglitch_train_normal_all_local.lance"
VALIDATION_DATASET_NAME = "tempglitch_validation_normal_all_local.lance"
SNAPSHOT_EXCLUDED_PREFIXES = (
    ".git/",
    "data/",
    "outputs/",
    "external/",
    ".venv/",
    "venv/",
)
SNAPSHOT_EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
DATASET_FILES = {
    "train-normal.lance.zip",
    "validation-normal.lance.zip",
    "project_snapshot.zip",
    "project_snapshot_manifest.json",
    "profile_input_metadata.json",
    "dataset-metadata.json",
}


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_permitted_project_snapshot(
    repo_root: Path, tracked_paths: list[str]
) -> tuple[bytes, dict[str, Any]]:
    guard = SecurityGuard()
    included: list[str] = []
    excluded: list[dict[str, str]] = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative_text in sorted(tracked_paths):
            normalized = relative_text.replace("\\", "/")
            relative = Path(normalized)
            reason = None
            if normalized.startswith(SNAPSHOT_EXCLUDED_PREFIXES):
                reason = "excluded_prefix"
            elif SNAPSHOT_EXCLUDED_PARTS.intersection(relative.parts):
                reason = "cache"
            elif SecurityGuard.LOCKED_TEST_PATH_PATTERN.search(normalized):
                reason = "locked_test"
            elif relative.suffix.lower() in {".pt", ".pth", ".ckpt"}:
                reason = "checkpoint"
            path = repo_root / relative
            if reason or not path.is_file():
                excluded.append({"path": normalized, "reason": reason or "not_file"})
                continue
            try:
                guard.scan_tracked_files(repo_root, [normalized])
            except SecurityViolation:
                excluded.append({"path": normalized, "reason": "security_scan"})
                continue
            bundle.writestr(_zip_info(normalized), path.read_bytes())
            included.append(normalized)
    manifest = {"included": included, "excluded": excluded}
    return buffer.getvalue(), manifest


def _bytes_sha256(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class LeWMGPUProfileKaggleConfig:
    dataset_slug: str
    kernel_slug: str
    batch_size: int
    git_sha: str
    branch: str
    amp: bool = False
    dataset_id: str = "lewm-research-mvp-gpu-profile"
    accelerator: str = "NvidiaTeslaT4"
    dataset_visibility: str = "private"
    kernel_visibility: str = "private"

    def __post_init__(self) -> None:
        validate_kaggle_slug(self.dataset_slug, label="dataset_slug")
        validate_kaggle_slug(self.kernel_slug, label="kernel_slug")
        if self.dataset_slug == self.kernel_slug:
            raise ValueError("Profile dataset and kernel slugs must differ.")
        if self.dataset_visibility != "private" or self.kernel_visibility != "private":
            raise ValueError("LeWM GPU profile dataset and kernel must remain private.")
        LeWMGPUProfileConfig(batch_size=self.batch_size, amp=self.amp)


def _git_tracked(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.splitlines()


def _archive_directory(source: Path, output: Path, archive_root: str) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            bundle.writestr(
                _zip_info(f"{archive_root}/{path.relative_to(source).as_posix()}"),
                path.read_bytes(),
            )


def render_profile_kernel(
    config: LeWMGPUProfileKaggleConfig, input_metadata: dict[str, Any]
) -> str:
    config_payload = json.dumps(asdict(config), sort_keys=True)
    metadata_payload = json.dumps(input_metadata, sort_keys=True)
    return f'''"""Generated fail-closed LeWM 500-update GPU profile."""
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

CONFIG = json.loads({config_payload!r})
INPUT_METADATA = json.loads({metadata_payload!r})
INPUT = Path("/kaggle/input")
OUTPUT = Path("/kaggle/working")
CODE = Path("/tmp/glitch-world-model")
LOCAL = Path("/tmp/lewm_profile_input")

if CONFIG["dataset_visibility"] != "private" or CONFIG["kernel_visibility"] != "private":
    raise RuntimeError("Profile resources must remain private.")
if INPUT_METADATA["optimizer_updates"] != 500 or INPUT_METADATA["validation_batches"] != 8:
    raise RuntimeError("Profile contract changed.")

def find_one_file(name):
    matches = sorted(path for path in INPUT.rglob(name) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {{name}}, found {{matches}}")
    return matches[0]

def find_one_dir(name):
    matches = sorted(path for path in INPUT.rglob(name) if path.is_dir())
    leaves = [
        path for path in matches
        if not any(other != path and str(other).startswith(str(path) + "/") for other in matches)
    ]
    if len(leaves) != 1:
        raise RuntimeError(f"Expected exactly one directory {{name}}, found {{leaves}}")
    return leaves[0]

def materialize(archive_name, directory_name, destination):
    directories = sorted(path for path in INPUT.rglob(directory_name) if path.is_dir())
    if directories:
        shutil.copytree(find_one_dir(directory_name), destination, dirs_exist_ok=True)
        return
    shutil.unpack_archive(str(find_one_file(archive_name)), str(destination.parent))

if os.environ.get("LEWM_PROFILE_BOOTSTRAP_ONLY") == "1":
    print("LEWM_PROFILE_BOOTSTRAP_OK")
    raise SystemExit(0)
CODE.mkdir(parents=True, exist_ok=True)
LOCAL.mkdir(parents=True, exist_ok=True)
snapshot_dirs = sorted(path for path in INPUT.rglob("project_snapshot") if path.is_dir())
if snapshot_dirs:
    shutil.copytree(find_one_dir("project_snapshot"), CODE, dirs_exist_ok=True)
else:
    shutil.unpack_archive(str(find_one_file("project_snapshot.zip")), str(CODE))
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "--no-cache-dir",
    "stable-worldmodel==0.1.1", "stable-pretraining==0.1.7", "transformers==4.57.6",
])
sys.path.insert(0, str(CODE / "src"))
import torch
from glitch_detection.lewm_gpu_profile import LeWMGPUProfileConfig, run_lewm_gpu_profile
if not torch.cuda.is_available():
    raise RuntimeError("LeWM GPU profile requires CUDA.")
train = LOCAL / "{TRAIN_DATASET_NAME}"
validation = LOCAL / "{VALIDATION_DATASET_NAME}"
materialize("train-normal.lance.zip", "{TRAIN_DATASET_NAME}", train)
materialize("validation-normal.lance.zip", "{VALIDATION_DATASET_NAME}", validation)
preflight = {{
    **INPUT_METADATA,
    "python": sys.version,
    "platform": platform.platform(),
    "pytorch": torch.__version__,
    "cuda_version": torch.version.cuda,
    "kaggle_runtime": True,
}}
(OUTPUT / "preflight_metadata.json").write_text(json.dumps(preflight, indent=2) + "\\n")
try:
    run_lewm_gpu_profile(
        train, validation, OUTPUT,
        LeWMGPUProfileConfig(batch_size=CONFIG["batch_size"], amp=CONFIG["amp"]),
        preflight_metadata=preflight,
    )
except Exception as exc:
    failure = {{
        "classification": "cuda_oom" if isinstance(exc, torch.cuda.OutOfMemoryError) else "runtime_error",
        "error_type": type(exc).__name__,
        "message": str(exc),
    }}
    (OUTPUT / "failure.json").write_text(json.dumps(failure, indent=2) + "\\n")
    (OUTPUT / "traceback.log").write_text(traceback.format_exc())
    raise
'''


def prepare_profile_kaggle_package(
    repo_root: Path,
    source_root: Path,
    output_root: Path,
    config: LeWMGPUProfileKaggleConfig,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    train = source_root / TRAIN_DATASET_NAME
    validation = source_root / VALIDATION_DATASET_NAME
    dataset_manifest = build_dataset_manifest(train, validation)
    profile_config = LeWMGPUProfileConfig(batch_size=config.batch_size, amp=config.amp)
    fingerprint_payload = {
        "git_sha": config.git_sha,
        "dataset_manifest_hash": dataset_manifest["dataset_manifest_hash"],
        "train_dataset_hash": dataset_manifest["train_dataset_hash"],
        "validation_dataset_hash": dataset_manifest["validation_dataset_hash"],
        "config_hash": profile_config.config_hash,
        "batch_size": config.batch_size,
        "amp": config.amp,
    }
    fingerprint = build_profile_fingerprint(fingerprint_payload)
    input_metadata = {
        **fingerprint_payload,
        "fingerprint": fingerprint,
        "branch": config.branch,
        "optimizer_updates": 500,
        "validation_batches": 8,
        "attempts": [],
    }
    summary = {
        "status": "dry-run only" if dry_run else "package complete",
        "config": asdict(config),
        "profile_fingerprint": fingerprint,
        "input_metadata": input_metadata,
        "dataset_manifest": dataset_manifest,
        "training_command": "run_lewm_gpu_profile(... optimizer_updates=500 ...)",
        "locked_test_included": False,
        "locked_test_scored": False,
    }
    if dry_run:
        return summary
    if output_root.exists():
        raise FileExistsError(f"Profile package already exists: {output_root}")
    dataset_root, kernel_root = output_root / "dataset", output_root / "kernel"
    dataset_root.mkdir(parents=True)
    kernel_root.mkdir(parents=True)
    _archive_directory(train, dataset_root / "train-normal.lance.zip", TRAIN_DATASET_NAME)
    _archive_directory(
        validation,
        dataset_root / "validation-normal.lance.zip",
        VALIDATION_DATASET_NAME,
    )
    archive, snapshot_manifest = build_permitted_project_snapshot(
        repo_root, _git_tracked(repo_root)
    )
    snapshot_manifest["archive_sha256"] = _bytes_sha256(archive)
    (dataset_root / "project_snapshot.zip").write_bytes(archive)
    (dataset_root / "project_snapshot_manifest.json").write_text(
        json.dumps(snapshot_manifest, indent=2) + "\n", encoding="utf-8"
    )
    (dataset_root / "profile_input_metadata.json").write_text(
        json.dumps(input_metadata, indent=2) + "\n", encoding="utf-8"
    )
    (dataset_root / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "id": config.dataset_slug,
                "title": config.dataset_id,
                "licenses": [{"name": "other"}],
                "visibility": "private",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    script = kernel_root / "lewm_gpu_profile_kernel.py"
    script.write_text(render_profile_kernel(config, input_metadata), encoding="utf-8")
    (kernel_root / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": config.kernel_slug,
                "title": config.kernel_slug.split("/", 1)[1],
                "code_file": script.name,
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "enable_gpu": True,
                "enable_internet": True,
                "dataset_sources": [config.dataset_slug],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary.update(validate_profile_kaggle_package(output_root))
    return summary


def validate_profile_kaggle_package(root: Path) -> dict[str, Any]:
    dataset, kernel = root / "dataset", root / "kernel"
    actual = {path.name for path in dataset.iterdir() if path.is_file()}
    if actual != DATASET_FILES:
        raise ValueError(f"Profile dataset package has unexpected files: {sorted(actual)}")
    metadata = json.loads((dataset / "dataset-metadata.json").read_text(encoding="utf-8"))
    kernel_metadata = json.loads((kernel / "kernel-metadata.json").read_text(encoding="utf-8"))
    if metadata.get("visibility") != "private" or kernel_metadata.get("is_private") is not True:
        raise ValueError("Profile Kaggle resources must remain private.")
    if kernel_metadata.get("dataset_sources") != [metadata.get("id")]:
        raise ValueError("Profile kernel dataset source mismatch.")
    code = kernel / str(kernel_metadata.get("code_file", ""))
    if not code.is_file() or len(list(kernel.iterdir())) != 2:
        raise ValueError("Profile kernel package must contain only metadata and code.")
    text = code.read_text(encoding="utf-8")
    if re.search(r"[A-Za-z]:\\+", text) or 'git", "clone"' in text:
        raise ValueError("Profile kernel contains mutable clone or local Windows path.")
    SecurityGuard().scan_package(dataset, "dataset")
    SecurityGuard().scan_package(kernel, "kernel")
    return {
        "dataset_inventory_sha256": FingerprintBuilder.inventory_sha256(dataset),
        "kernel_inventory_sha256": FingerprintBuilder.inventory_sha256(kernel),
        "kernel_code_sha256": FingerprintBuilder.sha256_file(code),
        "dataset_slug": metadata["id"],
        "kernel_slug": kernel_metadata["id"],
    }
