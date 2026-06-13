from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .kaggle_automation import FingerprintBuilder, SecurityGuard

REQUIRED_OUTPUTS = (
    "run_config.json",
    "environment.json",
    "dataset_metadata.json",
    "training_metadata.json",
    "loss_history.json",
    "collapse_diagnostics.json",
    "checkpoint.sha256",
    "protocol_audit.json",
    "resume_metadata.json",
)
PLACEHOLDER_OWNERS = {"private", "your-username", "user", "username", "owner", ""}
KAGGLE_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$")
REQUIRED_KERNEL_METADATA_FIELDS = {
    "id",
    "title",
    "code_file",
    "language",
    "kernel_type",
    "is_private",
    "enable_gpu",
    "dataset_sources",
}


@dataclass(frozen=True)
class LeWMKaggleConfig:
    dataset_slug: str
    kernel_slug: str
    dataset_id: str
    action_mode: str
    train_dataset_name: str
    validation_dataset_name: str
    batch_size: int = 4
    max_epochs: int = 1
    image_size: int = 112
    sigreg_projections: int = 128
    max_train_steps: int | None = 2
    max_validation_steps: int | None = 2
    seed: int = 42
    num_workers: int = 0
    pin_memory: bool = False
    mixed_precision: bool = False
    early_stopping_patience: int | None = None
    early_stopping_min_delta: float = 0.0
    target_optimizer_updates: int | None = None
    evaluation_interval_updates: int | None = None
    checkpoint_interval_updates: int | None = None
    prove_resume: bool = True
    accelerator: str = "NvidiaTeslaT4"
    validation_only: bool = True

    def __post_init__(self) -> None:
        validate_kaggle_slug(self.dataset_slug, label="dataset_slug")
        validate_kaggle_slug(self.kernel_slug, label="kernel_slug")
        if self.dataset_slug == self.kernel_slug:
            raise ValueError("Kaggle kernel_slug must differ from dataset_slug.")
        if self.action_mode not in {"real", "zero_action"}:
            raise ValueError("Kaggle LeWM action_mode must be real or zero_action.")
        if not self.validation_only:
            raise ValueError(
                "LeWM Kaggle foundation is validation-only until locked-test approval."
            )
        if self.batch_size < 1 or self.max_epochs < 1:
            raise ValueError("LeWM Kaggle batch_size and max_epochs must be positive.")
        if self.max_train_steps is not None and self.max_train_steps < 1:
            raise ValueError("LeWM Kaggle smoke step limits must be positive.")
        if self.max_validation_steps is not None and self.max_validation_steps < 1:
            raise ValueError("LeWM Kaggle smoke step limits must be positive.")
        if self.num_workers < 0:
            raise ValueError("LeWM Kaggle num_workers cannot be negative.")
        if self.early_stopping_patience is not None and self.early_stopping_patience < 1:
            raise ValueError("LeWM Kaggle early_stopping_patience must be positive.")
        if self.early_stopping_min_delta < 0:
            raise ValueError("LeWM Kaggle early_stopping_min_delta cannot be negative.")
        if self.target_optimizer_updates is not None and self.target_optimizer_updates < 1:
            raise ValueError("LeWM Kaggle target_optimizer_updates must be positive.")
        if self.target_optimizer_updates is not None and (
            self.evaluation_interval_updates is None or self.checkpoint_interval_updates is None
        ):
            raise ValueError("LeWM Kaggle update-based training requires update intervals.")


def validate_kaggle_slug(slug: str, *, label: str) -> None:
    if not KAGGLE_SLUG_PATTERN.match(slug):
        raise ValueError(
            f"Kaggle {label} must be explicit owner/slug with lowercase letters, "
            "digits, and hyphens only."
        )
    owner, _name = slug.split("/", 1)
    if owner in PLACEHOLDER_OWNERS:
        raise ValueError(f"Kaggle {label} uses placeholder owner: {owner}")


def quota_allocation(total_hours: float) -> dict[str, float]:
    if total_hours <= 0:
        raise ValueError("Kaggle GPU quota must be positive.")
    return {
        "lewm_dual_primary": total_hours * 0.50,
        "video_baselines": total_hours * 0.25,
        "lewm_ablations": total_hours * 0.15,
        "open_vlm": total_hours * 0.10,
    }


def render_validation_kernel(config: LeWMKaggleConfig) -> str:
    payload = json.dumps(asdict(config), sort_keys=True)
    return f'''"""Generated validation-only LeWM Kaggle entrypoint."""
import json
import platform
import shutil as _shutil
import subprocess
import sys
from pathlib import Path

CONFIG = json.loads({payload!r})
OUTPUT = Path("/kaggle/working")
INPUT_ROOT = Path("/kaggle/input")
REPO = Path("/tmp/glitch-world-model")

if not CONFIG["validation_only"]:
    raise RuntimeError("Locked-test execution is forbidden in this kernel.")

def _find_lance_dataset(name):
    matches = sorted(path for path in INPUT_ROOT.rglob(name) if path.is_dir())
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one Kaggle input directory named {{name!r}}, "
            f"found {{len(matches)}}: {{matches}}"
        )
    return matches[0]

_tmp_input = Path("/tmp/lewm_input")
_tmp_input.mkdir(parents=True, exist_ok=True)
_train_src = _find_lance_dataset(CONFIG["train_dataset_name"])
_val_src = _find_lance_dataset(CONFIG["validation_dataset_name"])
_train_dst = _tmp_input / CONFIG["train_dataset_name"]
_val_dst = _tmp_input / CONFIG["validation_dataset_name"]
if not _train_dst.exists():
    _shutil.copytree(str(_train_src), str(_train_dst))
if not _val_dst.exists():
    _shutil.copytree(str(_val_src), str(_val_dst))
subprocess.check_call([
    "git", "clone", "--depth", "1", "--branch", "main",
    "https://github.com/thanhdicode/glitch-world-model.git", str(REPO)
])
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "--no-cache-dir",
    "stable-worldmodel==0.1.1",
    "stable-pretraining==0.1.7",
    "transformers==4.57.6",
])
sys.path.insert(0, str(REPO / "src"))

import torch
from glitch_detection.lewm_training import LeWMTrainConfig, train_lewm

if not torch.cuda.is_available():
    raise RuntimeError("Gate 5 LeWM smoke requires CUDA.")

(OUTPUT / "run_config.json").write_text(json.dumps(CONFIG, indent=2) + "\\n")
(OUTPUT / "environment.json").write_text(json.dumps({{
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
}}, indent=2) + "\\n")

train_config = LeWMTrainConfig(
    image_size=CONFIG["image_size"],
    batch_size=CONFIG["batch_size"],
    epochs=CONFIG["max_epochs"],
    seed=CONFIG["seed"],
    sigreg_projections=CONFIG["sigreg_projections"],
    max_train_steps=CONFIG["max_train_steps"],
    max_validation_steps=CONFIG["max_validation_steps"],
    run_kind="research" if CONFIG["target_optimizer_updates"] is not None else "engineering_smoke",
    num_workers=CONFIG["num_workers"],
    pin_memory=CONFIG["pin_memory"],
    mixed_precision=CONFIG["mixed_precision"],
    early_stopping_patience=CONFIG["early_stopping_patience"],
    early_stopping_min_delta=CONFIG["early_stopping_min_delta"],
    target_optimizer_updates=CONFIG["target_optimizer_updates"],
    evaluation_interval_updates=CONFIG["evaluation_interval_updates"],
    checkpoint_interval_updates=CONFIG["checkpoint_interval_updates"],
)
first = train_lewm(
    _train_dst,
    _val_dst,
    OUTPUT,
    train_config,
    device="cuda",
)
result = train_lewm(
    _train_dst,
    _val_dst,
    OUTPUT,
    train_config,
    device="cuda",
    resume=True,
) if CONFIG["prove_resume"] and CONFIG["target_optimizer_updates"] is None else first
if (
    CONFIG["prove_resume"]
    and CONFIG["target_optimizer_updates"] is None
    and result["completed_epoch"] <= first["completed_epoch"]
):
    raise RuntimeError("LeWM resume proof did not advance the completed epoch.")
(OUTPUT / "dataset_metadata.json").write_text(json.dumps({{
    "dataset_id": CONFIG["dataset_id"],
    "action_mode": CONFIG["action_mode"],
    "dataset_hashes": result["dataset_hashes"],
}}, indent=2) + "\\n")
(OUTPUT / "protocol_audit.json").write_text(json.dumps({{
    "validation_only": True,
    "locked_test_materialized": False,
    "locked_test_scored": False,
}}, indent=2) + "\\n")
(OUTPUT / "resume_metadata.json").write_text(json.dumps({{
    "resume_supported": True,
    "resume_proved": (
        result.get("completed_epoch", 0) > first.get("completed_epoch", 0)
        if CONFIG["target_optimizer_updates"] is None
        else result["checkpoint_reload"]["reloaded_global_step"] == result["updates_completed"]
    ),
    "config_hash": result["config_hash"],
    "dataset_hashes": result["dataset_hashes"],
    "initial_completed_epoch": first.get("completed_epoch"),
    "completed_epoch": result.get("completed_epoch"),
    "updates_completed": result.get("updates_completed"),
    "target_optimizer_updates": result.get("target_optimizer_updates"),
}}, indent=2) + "\\n")
'''


def prepare_lewm_kaggle_package(
    source_root: Path,
    output_root: Path,
    config: LeWMKaggleConfig,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    required = [
        source_root / config.train_dataset_name,
        source_root / config.validation_dataset_name,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing LeWM Kaggle dataset inputs: {', '.join(missing)}")
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "package complete",
        "config": asdict(config),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "required_outputs": list(REQUIRED_OUTPUTS),
        "locked_test_included": False,
        "locked_test_scored": False,
    }
    if dry_run:
        return summary
    if output_root.exists():
        raise FileExistsError(f"LeWM Kaggle package already exists: {output_root}")
    dataset_root = output_root / "dataset"
    kernel_root = output_root / "kernel"
    dataset_root.mkdir(parents=True)
    kernel_root.mkdir(parents=True)
    for path in required:
        target = dataset_root / path.name
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)
    (dataset_root / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "id": config.dataset_slug,
                "title": config.dataset_id,
                "licenses": [{"name": "other"}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    kernel_script = kernel_root / "lewm_validation_kernel.py"
    kernel_script.write_text(render_validation_kernel(config), encoding="utf-8")
    repo_root = Path(__file__).resolve().parents[2]
    shutil.copytree(
        repo_root / "src" / "glitch_detection",
        kernel_root / "src" / "glitch_detection",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copy2(repo_root / "requirements" / "lewm-runtime.txt", kernel_root / "lewm-runtime.txt")
    (kernel_root / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": config.kernel_slug,
                "title": config.kernel_slug.split("/", 1)[-1],
                "code_file": kernel_script.name,
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
    guard = SecurityGuard()
    guard.scan_package(dataset_root, "dataset")
    guard.scan_package(kernel_root, "kernel")
    summary["dataset_inventory_sha256"] = FingerprintBuilder.inventory_sha256(dataset_root)
    summary["kernel_sha256"] = FingerprintBuilder.sha256_file(kernel_script)
    return summary


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_lewm_kaggle_package(package_root: Path) -> dict[str, Any]:
    dataset_root = package_root / "dataset"
    kernel_root = package_root / "kernel"
    dataset_metadata_path = dataset_root / "dataset-metadata.json"
    kernel_metadata_path = kernel_root / "kernel-metadata.json"
    if not dataset_metadata_path.is_file():
        raise FileNotFoundError(f"Missing dataset metadata: {dataset_metadata_path}")
    if not kernel_metadata_path.is_file():
        raise FileNotFoundError(f"Missing kernel metadata: {kernel_metadata_path}")

    dataset_metadata = _read_json(dataset_metadata_path)
    kernel_metadata = _read_json(kernel_metadata_path)
    missing = sorted(REQUIRED_KERNEL_METADATA_FIELDS - set(kernel_metadata))
    if missing:
        raise ValueError(f"Kernel metadata missing required fields: {', '.join(missing)}")

    dataset_slug = str(dataset_metadata.get("id", ""))
    kernel_slug = str(kernel_metadata.get("id", ""))
    validate_kaggle_slug(dataset_slug, label="dataset_slug")
    validate_kaggle_slug(kernel_slug, label="kernel_slug")
    if dataset_slug == kernel_slug:
        raise ValueError("Kaggle kernel_slug must differ from dataset_slug.")

    code_file = kernel_root / str(kernel_metadata.get("code_file", ""))
    if not code_file.is_file():
        raise FileNotFoundError(f"Kernel code_file does not exist: {code_file.name}")
    if kernel_metadata.get("language") != "python":
        raise ValueError("Kernel metadata language must be python.")
    if kernel_metadata.get("kernel_type") != "script":
        raise ValueError("Kernel metadata kernel_type must be script.")
    if kernel_metadata.get("is_private") is not True:
        raise ValueError("Kernel metadata must keep is_private=true.")
    if kernel_metadata.get("enable_gpu") is not True:
        raise ValueError("Kernel metadata must keep enable_gpu=true.")
    dataset_sources = kernel_metadata.get("dataset_sources")
    if dataset_sources != [dataset_slug]:
        raise ValueError("Kernel metadata dataset_sources must match the dataset slug exactly.")

    SecurityGuard().scan_package(dataset_root, "dataset")
    SecurityGuard().scan_package(kernel_root, "kernel")
    return {
        "dataset_slug": dataset_slug,
        "kernel_slug": kernel_slug,
        "kernel_metadata_sha256": FingerprintBuilder.sha256_file(kernel_metadata_path),
        "kernel_code_sha256": FingerprintBuilder.sha256_file(code_file),
        "kernel_inventory_sha256": FingerprintBuilder.inventory_sha256(kernel_root),
        "dataset_inventory_sha256": FingerprintBuilder.inventory_sha256(dataset_root),
    }


def _kernel_fingerprint_payload(package_root: Path) -> dict[str, Any]:
    validation = validate_lewm_kaggle_package(package_root)
    return {
        "dataset_slug": validation["dataset_slug"],
        "kernel_slug": validation["kernel_slug"],
        "dataset_fingerprint": validation["dataset_inventory_sha256"],
        "kernel_inventory_sha256": validation["kernel_inventory_sha256"],
        "kernel_metadata_sha256": validation["kernel_metadata_sha256"],
        "kernel_script_sha256": validation["kernel_code_sha256"],
    }


def validate_kernel_push_preflight(package_root: Path) -> dict[str, Any]:
    kernel_payload = _kernel_fingerprint_payload(package_root)
    return {
        **kernel_payload,
        "kernel_fingerprint": _sha256_json(kernel_payload),
        "authorization": "standing",
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_package_audit(package_root: Path, output_path: Path) -> dict[str, Any]:
    validation = validate_lewm_kaggle_package(package_root)
    preflight = validate_kernel_push_preflight(package_root)
    payload = {
        **validation,
        **preflight,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "authorization": "standing",
        "live_actions_performed": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _validate_finite_numbers(payload: Any, *, label: str) -> None:
    numeric_values: list[float] = []

    def collect(value: Any) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, int | float):
            numeric_values.append(float(value))
            return
        if isinstance(value, dict):
            for nested in value.values():
                collect(nested)
            return
        if isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(payload)
    if not numeric_values:
        raise ValueError(f"LeWM {label} contains no numeric values.")
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError(f"LeWM {label} contains non-finite values.")


def validate_lewm_smoke_artifacts(root: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_OUTPUTS if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing LeWM smoke artifacts: {', '.join(missing)}")
    environment = json.loads((root / "environment.json").read_text(encoding="utf-8-sig"))
    training = json.loads((root / "training_metadata.json").read_text(encoding="utf-8-sig"))
    dataset = json.loads((root / "dataset_metadata.json").read_text(encoding="utf-8-sig"))
    protocol = json.loads((root / "protocol_audit.json").read_text(encoding="utf-8-sig"))
    resume = json.loads((root / "resume_metadata.json").read_text(encoding="utf-8-sig"))
    loss_history = json.loads((root / "loss_history.json").read_text(encoding="utf-8-sig"))
    diagnostics = json.loads((root / "collapse_diagnostics.json").read_text(encoding="utf-8-sig"))
    checkpoint_hash = (root / "checkpoint.sha256").read_text(encoding="utf-8-sig").strip()
    if environment.get("cuda_available") is not True or training.get("device") != "cuda":
        raise ValueError("LeWM Gate 5 artifacts do not prove CUDA execution.")
    if resume.get("resume_proved") is not True:
        raise ValueError("LeWM Gate 5 artifacts do not prove checkpoint resume.")
    if resume.get("completed_epoch", 0) <= resume.get("initial_completed_epoch", 0):
        raise ValueError("LeWM resume metadata did not advance the completed epoch.")
    if resume.get("config_hash") != training.get("config_hash"):
        raise ValueError("LeWM resume/training config hashes differ.")
    if resume.get("dataset_hashes") != training.get("dataset_hashes"):
        raise ValueError("LeWM resume/training dataset hashes differ.")
    if dataset.get("dataset_hashes") != training.get("dataset_hashes"):
        raise ValueError("LeWM dataset/training hashes differ.")
    if checkpoint_hash != training.get("checkpoint_sha256"):
        raise ValueError("LeWM checkpoint SHA-256 does not match training metadata.")
    if not isinstance(loss_history, list) or not loss_history:
        raise ValueError("LeWM loss history must contain at least one epoch.")
    _validate_finite_numbers(loss_history, label="loss history")
    if diagnostics.get("finite") is not True:
        raise ValueError("LeWM collapse diagnostics are not finite.")
    _validate_finite_numbers(diagnostics, label="collapse diagnostics")
    if protocol.get("locked_test_materialized") or protocol.get("locked_test_scored"):
        raise ValueError("LeWM Gate 5 artifacts indicate locked-test access.")
    if training.get("locked_test_materialized") or training.get("locked_test_scored"):
        raise ValueError("LeWM training metadata indicates locked-test access.")
    return {
        "status": "gate5_cuda_resume_verified",
        "device": training["device"],
        "initial_completed_epoch": resume["initial_completed_epoch"],
        "completed_epoch": resume["completed_epoch"],
        "config_hash": training["config_hash"],
        "dataset_hashes": training["dataset_hashes"],
        "checkpoint_sha256": checkpoint_hash,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
