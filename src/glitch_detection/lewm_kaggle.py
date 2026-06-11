from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import ApprovalStore, FingerprintBuilder, SecurityGuard

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
    max_train_steps: int = 2
    max_validation_steps: int = 2
    prove_resume: bool = True
    accelerator: str = "NvidiaTeslaT4"
    validation_only: bool = True

    def __post_init__(self) -> None:
        if self.action_mode not in {"real", "zero_action"}:
            raise ValueError("Kaggle LeWM action_mode must be real or zero_action.")
        if not self.validation_only:
            raise ValueError(
                "LeWM Kaggle foundation is validation-only until locked-test approval."
            )
        if self.batch_size < 1 or self.max_epochs < 1:
            raise ValueError("LeWM Kaggle batch_size and max_epochs must be positive.")
        if self.max_train_steps < 1 or self.max_validation_steps < 1:
            raise ValueError("LeWM Kaggle smoke step limits must be positive.")


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
import subprocess
import sys
from pathlib import Path

CONFIG = json.loads({payload!r})
OUTPUT = Path("/kaggle/working")
ROOT = Path(__file__).resolve().parent
DATASET = Path("/kaggle/input") / CONFIG["dataset_slug"].split("/")[-1]

if not CONFIG["validation_only"]:
    raise RuntimeError("Locked-test execution is forbidden in this kernel.")

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-r", str(ROOT / "lewm-runtime.txt")
])
sys.path.insert(0, str(ROOT / "src"))

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
    sigreg_projections=CONFIG["sigreg_projections"],
    max_train_steps=CONFIG["max_train_steps"],
    max_validation_steps=CONFIG["max_validation_steps"],
)
first = train_lewm(
    DATASET / CONFIG["train_dataset_name"],
    DATASET / CONFIG["validation_dataset_name"],
    OUTPUT,
    train_config,
    device="cuda",
)
result = train_lewm(
    DATASET / CONFIG["train_dataset_name"],
    DATASET / CONFIG["validation_dataset_name"],
    OUTPUT,
    train_config,
    device="cuda",
    resume=True,
) if CONFIG["prove_resume"] else first
if CONFIG["prove_resume"] and result["completed_epoch"] <= first["completed_epoch"]:
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
    "resume_proved": result["completed_epoch"] > first["completed_epoch"],
    "config_hash": result["config_hash"],
    "dataset_hashes": result["dataset_hashes"],
    "initial_completed_epoch": first["completed_epoch"],
    "completed_epoch": result["completed_epoch"],
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


def request_package_approvals(package_root: Path, approvals_root: Path) -> dict[str, Any]:
    dataset_root = package_root / "dataset"
    kernel_root = package_root / "kernel"
    kernel_script = kernel_root / "lewm_validation_kernel.py"
    SecurityGuard().scan_package(dataset_root, "dataset")
    SecurityGuard().scan_package(kernel_root, "kernel")
    dataset_fingerprint = FingerprintBuilder.inventory_sha256(dataset_root)
    kernel_payload = {
        "dataset_fingerprint": dataset_fingerprint,
        "kernel_inventory_sha256": FingerprintBuilder.inventory_sha256(kernel_root),
        "kernel_script_sha256": FingerprintBuilder.sha256_file(kernel_script),
    }
    kernel_fingerprint = hashlib.sha256(
        json.dumps(kernel_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    store = ApprovalStore(approvals_root)
    dataset_request = store.request("dataset_upload_approval", dataset_fingerprint)
    kernel_request = store.request("kernel_push_approval", kernel_fingerprint)
    return {
        "dataset_upload_approval": dataset_request,
        "kernel_push_approval": kernel_request,
        "live_actions_performed": False,
    }


def validate_lewm_smoke_artifacts(root: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_OUTPUTS if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing LeWM smoke artifacts: {', '.join(missing)}")
    environment = json.loads((root / "environment.json").read_text(encoding="utf-8-sig"))
    training = json.loads((root / "training_metadata.json").read_text(encoding="utf-8-sig"))
    dataset = json.loads((root / "dataset_metadata.json").read_text(encoding="utf-8-sig"))
    protocol = json.loads((root / "protocol_audit.json").read_text(encoding="utf-8-sig"))
    resume = json.loads((root / "resume_metadata.json").read_text(encoding="utf-8-sig"))
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
    if protocol.get("locked_test_materialized") or protocol.get("locked_test_scored"):
        raise ValueError("LeWM Gate 5 artifacts indicate locked-test access.")
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
