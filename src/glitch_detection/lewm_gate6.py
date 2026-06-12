from __future__ import annotations

import base64
import io
import json
import math
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import FingerprintBuilder, PublicReleaseSpec, SecurityGuard
from .lewm_kaggle import validate_kaggle_slug

GATE6_REQUIRED_OUTPUTS = (
    "run_config.json",
    "environment.json",
    "dataset_metadata.json",
    "training_metadata.json",
    "loss_history.json",
    "collapse_diagnostics.json",
    "checkpoint.sha256",
    "protocol_audit.json",
    "best_checkpoint_metadata.json",
    "checkpoint_reload.json",
    "encoding_proof.json",
)


@dataclass(frozen=True)
class Gate6KaggleConfig:
    dataset_slug: str
    kernel_slug: str
    dataset_id: str
    train_dataset_name: str
    validation_dataset_name: str
    buggy_probe_dataset_name: str
    image_size: int = 112
    batch_size: int = 2
    max_epochs: int = 1
    max_train_steps: int = 16
    max_validation_steps: int = 8
    sigreg_projections: int = 128
    seed: int = 42
    package_version: str = "v1"
    action_mode: str = "zero_action"
    accelerator: str = "NvidiaTeslaT4"
    validation_only: bool = True
    dataset_visibility: str = "public"
    kernel_visibility: str = "public"
    dataset_license: str = "MIT"
    redistribution_allowed: bool = True

    def __post_init__(self) -> None:
        validate_kaggle_slug(self.dataset_slug, label="dataset_slug")
        validate_kaggle_slug(self.kernel_slug, label="kernel_slug")
        if self.dataset_slug == self.kernel_slug:
            raise ValueError("Kaggle kernel_slug must differ from dataset_slug.")
        if self.action_mode != "zero_action":
            raise ValueError("Gate 6 pilot supports only zero_action.")
        if not self.validation_only:
            raise ValueError("Gate 6 must remain validation-only.")
        if self.dataset_visibility not in {"private", "public"}:
            raise ValueError("dataset_visibility must be private or public.")
        if self.kernel_visibility not in {"private", "public"}:
            raise ValueError("kernel_visibility must be private or public.")
        if self.dataset_visibility == "public" and not self.redistribution_allowed:
            raise ValueError("Public Gate 6 datasets require redistribution permission.")
        if self.dataset_visibility == "public" and not self.dataset_license.strip():
            raise ValueError("Public Gate 6 datasets require a license.")


def build_source_archive(source_root: Path) -> bytes:
    package_root = source_root / "glitch_detection"
    if not (package_root / "__init__.py").is_file():
        raise FileNotFoundError(f"Missing glitch_detection package: {package_root}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(package_root.rglob("*.py")):
            relative = path.relative_to(source_root)
            if "__pycache__" in relative.parts:
                continue
            info = zipfile.ZipInfo(relative.as_posix())
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    return buffer.getvalue()


def render_gate6_kernel(config: Gate6KaggleConfig, source_archive_b64: str) -> str:
    payload = json.dumps(asdict(config), sort_keys=True)
    return f'''"""Generated normal-only Gate 6 LeWM Kaggle entrypoint."""
import base64
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

CONFIG = json.loads({payload!r})
OUTPUT = Path("/kaggle/working")
INPUT_ROOT = Path("/kaggle/input")
SOURCE_ARCHIVE_B64 = {source_archive_b64!r}

if not CONFIG["validation_only"]:
    raise RuntimeError("Locked-test execution is forbidden in this kernel.")

def _select_lance_candidate(candidates):
    \"\"\"Return the deepest-leaf candidate from a list of Paths with the same name.

    If Kaggle mounts a dataset at both the root and a nested same-name directory
    (e.g. /kaggle/input/ds/name  AND  /kaggle/input/ds/name/name), we keep
    only the deepest entry because the shallower one is the parent mount point.
    Raises RuntimeError when multiple *unrelated* same-name leaves remain.
    \"\"\"
    if not candidates:
        return None
    # Remove any candidate that is an ancestor of another candidate.
    filtered = [
        c for c in candidates
        if not any(other != c and str(other).startswith(str(c) + "/") for other in candidates)
    ]
    if len(filtered) == 1:
        return filtered[0]
    raise RuntimeError(
        f"Multiple unrelated Lance candidates found; cannot select one: {{filtered}}"
    )

def materialize_dataset(name, destination_root):
    directories = sorted(path for path in INPUT_ROOT.rglob(name) if path.is_dir())
    archives = sorted(path for path in INPUT_ROOT.rglob(name + ".zip") if path.is_file())
    destination = destination_root / name
    if directories:
        selected = _select_lance_candidate(directories)
        shutil.copytree(selected, destination)
    elif archives:
        selected_archive = archives[0]
        extract_tmp = destination_root / (name + "_extract_tmp")
        extract_tmp.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(selected_archive), str(extract_tmp))
        # Find the extracted directory matching the expected name.
        extracted_dirs = sorted(path for path in extract_tmp.rglob(name) if path.is_dir())
        if not extracted_dirs:
            raise RuntimeError(
                f"Archive {{selected_archive}} did not produce a directory named {{name}}"
            )
        selected_extracted = _select_lance_candidate(extracted_dirs)
        shutil.copytree(selected_extracted, destination)
        shutil.rmtree(extract_tmp)
    else:
        raise RuntimeError(
            f"No input directory or archive named {{name}} found under {{INPUT_ROOT}}"
        )
    if not destination.is_dir():
        raise RuntimeError(f"materialize_dataset did not produce expected Lance directory: {{destination}}")
    return destination

CODE_ROOT = Path(os.environ.get("GATE6_CODE_ROOT", "/tmp/gate6_code"))
SOURCE_ZIP = CODE_ROOT.parent / "gate6_source.zip"
CODE_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ZIP.write_bytes(base64.b64decode(SOURCE_ARCHIVE_B64, validate=True))
if not zipfile.is_zipfile(SOURCE_ZIP):
    raise RuntimeError("Embedded Gate 6 source archive is invalid.")
with zipfile.ZipFile(SOURCE_ZIP) as bundle:
    names = set(bundle.namelist())
    if "glitch_detection/__init__.py" not in names:
        raise RuntimeError("Embedded Gate 6 source archive lacks the package root.")
    bundle.extractall(CODE_ROOT)
sys.path.insert(0, str(CODE_ROOT))

from glitch_detection.lewm_training import LeWMTrainConfig, score_lance_probe, train_lewm

if os.environ.get("GATE6_BOOTSTRAP_ONLY") == "1":
    print("GATE6_BOOTSTRAP_OK")
    raise SystemExit(0)

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "--no-cache-dir",
    "stable-worldmodel==0.1.1",
    "stable-pretraining==0.1.7",
    "transformers==4.57.6",
])

import torch

if not torch.cuda.is_available():
    raise RuntimeError("Gate 6 LeWM pilot requires CUDA.")

local = Path("/tmp/gate6_input")
local.mkdir(parents=True, exist_ok=True)
paths = {{}}
for key in ("train_dataset_name", "validation_dataset_name", "buggy_probe_dataset_name"):
    paths[key] = materialize_dataset(CONFIG[key], local)

(OUTPUT / "run_config.json").write_text(json.dumps(CONFIG, indent=2) + "\\n")
(OUTPUT / "environment.json").write_text(json.dumps({{
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda_available": True,
    "cuda_device": torch.cuda.get_device_name(0),
}}, indent=2) + "\\n")

train_config = LeWMTrainConfig(
    image_size=CONFIG["image_size"],
    batch_size=CONFIG["batch_size"],
    epochs=CONFIG["max_epochs"],
    sigreg_projections=CONFIG["sigreg_projections"],
    seed=CONFIG["seed"],
    max_train_steps=CONFIG["max_train_steps"],
    max_validation_steps=CONFIG["max_validation_steps"],
)
result = train_lewm(
    paths["train_dataset_name"],
    paths["validation_dataset_name"],
    OUTPUT,
    train_config,
    device="cuda",
)
normal_proof = score_lance_probe(
    paths["validation_dataset_name"],
    OUTPUT / "best_weights.pt",
    OUTPUT / "config.json",
    device="cuda",
)
buggy_proof = score_lance_probe(
    paths["buggy_probe_dataset_name"],
    OUTPUT / "best_weights.pt",
    OUTPUT / "config.json",
    device="cuda",
)
(OUTPUT / "encoding_proof.json").write_text(json.dumps({{
    "normal_validation": normal_proof,
    "nonlocked_buggy_validation": buggy_proof,
    "performance_claim": False,
}}, indent=2) + "\\n")
(OUTPUT / "dataset_metadata.json").write_text(json.dumps({{
    "dataset_id": CONFIG["dataset_id"],
    "dataset_hashes": result["dataset_hashes"],
    "normal_only_training": True,
    "normal_only_validation": True,
    "buggy_probe_use": "encoding_proof_only",
    "action_mode": "zero_action",
}}, indent=2) + "\\n")
(OUTPUT / "protocol_audit.json").write_text(json.dumps({{
    "validation_only": True,
    "normal_only_training": True,
    "normal_only_validation": True,
    "locked_test_materialized": False,
    "locked_test_scored": False,
}}, indent=2) + "\\n")
'''


def prepare_gate6_kaggle_package(
    source_root: Path,
    output_root: Path,
    config: Gate6KaggleConfig,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    names = (
        config.train_dataset_name,
        config.validation_dataset_name,
        config.buggy_probe_dataset_name,
    )
    inputs = [source_root / name for name in names]
    missing = [str(path) for path in inputs if not path.is_dir()]
    if missing:
        raise FileNotFoundError(f"Missing Gate 6 Lance inputs: {', '.join(missing)}")
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "package complete",
        "config": asdict(config),
        "required_outputs": list(GATE6_REQUIRED_OUTPUTS),
        "locked_test_included": False,
        "locked_test_scored": False,
    }
    if dry_run:
        return summary
    if output_root.exists():
        raise FileExistsError(f"Gate 6 package already exists: {output_root}")
    dataset_root = output_root / "dataset"
    kernel_root = output_root / "kernel"
    dataset_root.mkdir(parents=True)
    kernel_root.mkdir(parents=True)
    for path in inputs:
        shutil.make_archive(
            str(dataset_root / path.name),
            "zip",
            root_dir=path.parent,
            base_dir=path.name,
        )
    (dataset_root / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "id": config.dataset_slug,
                "title": config.dataset_id,
                "licenses": [{"name": config.dataset_license}],
                "package_version": config.package_version,
                "visibility": config.dataset_visibility,
                "redistribution_allowed": config.redistribution_allowed,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    kernel_script = kernel_root / "lewm_gate6_kernel.py"
    repo_root = Path(__file__).resolve().parents[2]
    source_archive = build_source_archive(repo_root / "src")
    source_archive_b64 = base64.b64encode(source_archive).decode("ascii")
    kernel_script.write_text(
        render_gate6_kernel(config, source_archive_b64),
        encoding="utf-8",
    )
    (kernel_root / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": config.kernel_slug,
                "title": config.kernel_slug.split("/", 1)[-1],
                "code_file": kernel_script.name,
                "language": "python",
                "kernel_type": "script",
                "is_private": config.kernel_visibility == "private",
                "enable_gpu": True,
                "enable_internet": True,
                "dataset_sources": [config.dataset_slug],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    guard = SecurityGuard()
    guard.scan_public_release(
        dataset_root,
        package_kind="dataset",
        spec=PublicReleaseSpec(
            visibility=config.dataset_visibility,
            license_name=config.dataset_license,
            redistribution_allowed=config.redistribution_allowed,
        ),
    )
    guard.scan_public_release(
        kernel_root,
        package_kind="kernel",
        spec=PublicReleaseSpec(
            visibility=config.kernel_visibility,
            license_name=config.dataset_license,
            redistribution_allowed=config.redistribution_allowed,
        ),
    )
    summary["dataset_inventory_sha256"] = FingerprintBuilder.inventory_sha256(dataset_root)
    summary["kernel_script_sha256"] = FingerprintBuilder.sha256_file(kernel_script)
    return summary


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _finite_numbers(payload: Any) -> bool:
    values: list[float] = []

    def collect(value: Any) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, int | float):
            values.append(float(value))
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(payload)
    return bool(values) and all(math.isfinite(value) for value in values)


def validate_gate6_kaggle_package(package_root: Path) -> dict[str, Any]:
    dataset_root = package_root / "dataset"
    kernel_root = package_root / "kernel"
    dataset_metadata = _load_json(dataset_root / "dataset-metadata.json")
    kernel_metadata = _load_json(kernel_root / "kernel-metadata.json")
    code_file = kernel_root / str(kernel_metadata.get("code_file", ""))
    if not code_file.is_file():
        raise FileNotFoundError(f"Missing Gate 6 kernel code file: {code_file}")
    extra_kernel_files = sorted(
        path.name
        for path in kernel_root.iterdir()
        if path.is_file() and path.name not in {"kernel-metadata.json", code_file.name}
    )
    if extra_kernel_files:
        raise ValueError(f"Gate 6 kernel package contains auxiliary files: {extra_kernel_files}")
    kernel_text = code_file.read_text(encoding="utf-8")
    if "SOURCE_ARCHIVE_B64" not in kernel_text:
        raise ValueError("Gate 6 kernel does not embed its source archive.")
    if re.search(r"[A-Za-z]:\\+", kernel_text):
        raise ValueError("Gate 6 kernel contains a Windows absolute path.")
    if kernel_metadata.get("dataset_sources") != [dataset_metadata.get("id")]:
        raise ValueError("Gate 6 kernel dataset_sources do not match dataset metadata.")
    guard = SecurityGuard()
    dataset_visibility = str(dataset_metadata.get("visibility", "private"))
    kernel_visibility = "private" if kernel_metadata.get("is_private", True) else "public"
    license_entries = dataset_metadata.get("licenses") or [{}]
    license_name = str(license_entries[0].get("name", ""))
    redistribution_allowed = bool(dataset_metadata.get("redistribution_allowed", False))
    guard.scan_public_release(
        dataset_root,
        package_kind="dataset",
        spec=PublicReleaseSpec(
            visibility=dataset_visibility,
            license_name=license_name,
            redistribution_allowed=redistribution_allowed,
        ),
    )
    guard.scan_public_release(
        kernel_root,
        package_kind="kernel",
        spec=PublicReleaseSpec(
            visibility=kernel_visibility,
            license_name=license_name,
            redistribution_allowed=redistribution_allowed,
        ),
    )
    return {
        "dataset_slug": dataset_metadata["id"],
        "kernel_slug": kernel_metadata["id"],
        "dataset_inventory_sha256": FingerprintBuilder.inventory_sha256(dataset_root),
        "kernel_inventory_sha256": FingerprintBuilder.inventory_sha256(kernel_root),
        "kernel_code_sha256": FingerprintBuilder.sha256_file(code_file),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def validate_gate6_artifacts(root: Path) -> dict[str, Any]:
    missing = [name for name in GATE6_REQUIRED_OUTPUTS if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Gate 6 artifacts: {', '.join(missing)}")
    environment = _load_json(root / "environment.json")
    training = _load_json(root / "training_metadata.json")
    dataset = _load_json(root / "dataset_metadata.json")
    protocol = _load_json(root / "protocol_audit.json")
    history = _load_json(root / "loss_history.json")
    diagnostics = _load_json(root / "collapse_diagnostics.json")
    reload_proof = _load_json(root / "checkpoint_reload.json")
    encoding = _load_json(root / "encoding_proof.json")
    if environment.get("cuda_available") is not True or training.get("device") != "cuda":
        raise ValueError("Gate 6 artifacts do not prove CUDA execution.")
    if not _finite_numbers(history):
        raise ValueError("Gate 6 loss history is empty or non-finite.")
    if diagnostics.get("finite") is not True or not _finite_numbers(diagnostics):
        raise ValueError("Gate 6 collapse diagnostics are invalid.")
    if reload_proof.get("checkpoint_reload_verified") is not True:
        raise ValueError("Gate 6 checkpoint reload was not verified.")
    for key in ("normal_validation", "nonlocked_buggy_validation"):
        if encoding.get(key, {}).get("finite") is not True:
            raise ValueError(f"Gate 6 {key} encoding proof is invalid.")
    if not dataset.get("normal_only_training") or not dataset.get("normal_only_validation"):
        raise ValueError("Gate 6 dataset metadata is not normal-only.")
    if not protocol.get("normal_only_training") or not protocol.get("normal_only_validation"):
        raise ValueError("Gate 6 protocol is not normal-only.")
    if any(
        payload.get(flag)
        for payload in (training, protocol)
        for flag in ("locked_test_materialized", "locked_test_scored")
    ):
        raise ValueError("Gate 6 artifacts indicate locked-test access.")
    checkpoint_hash = (root / "checkpoint.sha256").read_text(encoding="utf-8-sig").strip()
    if checkpoint_hash != training.get("checkpoint_sha256"):
        raise ValueError("Gate 6 checkpoint hash does not match training metadata.")
    return {
        "status": "gate6_passed",
        "device": training["device"],
        "completed_epoch": training["completed_epoch"],
        "checkpoint_sha256": checkpoint_hash,
        "best_weights_sha256": reload_proof["best_weights_sha256"],
        "normal_only_training": True,
        "normal_only_validation": True,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
