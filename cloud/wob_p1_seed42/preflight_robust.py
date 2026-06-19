"""Comprehensive preflight checks for WOB-P1 seed42 Kaggle runs.

Checks CUDA, VRAM, disk, Python version, required imports, input datasets,
train root, locked-test absence, and output writability. Writes a JSON report.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cloud.wob_kaggle_native.common import detect_kaggle_roots


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_python_version() -> dict[str, Any]:
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "ok": sys.version_info >= (3, 10),
    }


def _check_cuda() -> dict[str, Any]:
    try:
        import torch

        available = torch.cuda.is_available()
        if available:
            gpus: list[dict[str, Any]] = []
            for index in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(index)
                total_memory = getattr(props, "total_memory", None)
                if total_memory is None:
                    total_memory = getattr(props, "total_mem", None)
                if total_memory is None:
                    raise AttributeError(
                        "CUDA device properties expose neither total_memory nor total_mem"
                    )
                capability = torch.cuda.get_device_capability(index)
                gpus.append(
                    {
                        "index": index,
                        "name": torch.cuda.get_device_name(index),
                        "compute_capability": list(capability),
                        "vram_bytes": int(total_memory),
                        "vram_gb": round(int(total_memory) / (1024**3), 2),
                    }
                )
            return {
                "cuda_available": True,
                "gpu_name": gpus[0]["name"],
                "gpu_count": len(gpus),
                "compute_capability": gpus[0]["compute_capability"],
                "vram_bytes": gpus[0]["vram_bytes"],
                "vram_gb": gpus[0]["vram_gb"],
                "gpus": gpus,
                "torch_version": torch.__version__,
                "ok": True,
            }
        return {"cuda_available": False, "ok": False, "reason": "CUDA not available"}
    except Exception as exc:
        return {"cuda_available": False, "ok": False, "reason": str(exc)}


def _check_vram(cuda_info: dict[str, Any], min_gb: float = 14.0) -> dict[str, Any]:
    if not cuda_info.get("cuda_available"):
        return {"ok": False, "reason": "No CUDA"}
    vram_gb = cuda_info.get("vram_gb", 0)
    return {
        "vram_gb": vram_gb,
        "min_required_gb": min_gb,
        "ok": vram_gb >= min_gb,
    }


def _check_disk(path: str = "/kaggle/working") -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(path)
        free_gb = round(usage.free / (1024**3), 2)
        total_gb = round(usage.total / (1024**3), 2)
        return {
            "path": path,
            "free_gb": free_gb,
            "total_gb": total_gb,
            "ok": free_gb >= 5.0,
        }
    except Exception as exc:
        return {"path": path, "ok": False, "reason": str(exc)}


def _check_imports() -> dict[str, Any]:
    required = [
        "torch",
        "numpy",
        "yaml",
        "lance",
        "PIL",
        "cv2",
    ]
    results: dict[str, bool] = {}
    for mod in required:
        try:
            __import__(mod)
            results[mod] = True
        except ImportError:
            results[mod] = False
    return {"imports": results, "ok": all(results.values())}


def _check_kaggle_inputs(input_root: str = "/kaggle/input") -> dict[str, Any]:
    env_normal = os.environ.get("NORMAL_INPUT_ROOT")
    env_test = os.environ.get("TEST_INPUT_ROOT")
    if env_normal and env_test:
        normal_root = Path(env_normal)
        test_root = Path(env_test)
        return {
            "input_root": input_root,
            "normal_input_root": str(normal_root),
            "test_input_root": str(test_root),
            "datasets": {
                "world-of-bugs-normal": (normal_root / "NORMAL-TRAIN").exists(),
                "world-of-bugs-test": (test_root / "TEST").exists(),
            },
            "ok": (normal_root / "NORMAL-TRAIN").exists() and (test_root / "TEST").exists(),
        }

    root = Path(input_root)
    try:
        normal_root, test_root = detect_kaggle_roots(root)
    except Exception as exc:
        return {
            "input_root": input_root,
            "normal_input_root": None,
            "test_input_root": None,
            "ok": False,
            "reason": str(exc),
        }
    return {
        "input_root": input_root,
        "normal_input_root": str(normal_root),
        "test_input_root": str(test_root),
        "datasets": {
            "world-of-bugs-normal": normal_root.exists(),
            "world-of-bugs-test": test_root.exists(),
        },
        "ok": normal_root.exists() and test_root.exists(),
    }


def _check_locked_test_absent() -> dict[str, Any]:
    forbidden = [
        Path("/kaggle/working/locked_test"),
        Path("/kaggle/working/test_outputs"),
        Path("/kaggle/working/test_scores"),
    ]
    violations = [str(p) for p in forbidden if p.exists()]
    return {"violations": violations, "ok": len(violations) == 0}


def _check_output_writable(output_root: str) -> dict[str, Any]:
    root = Path(output_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return {"output_root": output_root, "writable": True, "ok": True}
    except Exception as exc:
        return {"output_root": output_root, "writable": False, "ok": False, "reason": str(exc)}


def _check_nvidia_smi() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {"nvidia_smi": result.stdout.strip(), "ok": result.returncode == 0}
    except Exception as exc:
        return {"nvidia_smi": None, "ok": False, "reason": str(exc)}


def run_preflight(
    repo_root: str,
    output_root: str,
    log_dir: str,
    input_root: str = "/kaggle/input",
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "timestamp": _utc_now(),
        "repo_root": repo_root,
    }

    report["python"] = _check_python_version()
    report["cuda"] = _check_cuda()
    report["vram"] = _check_vram(report["cuda"])
    report["disk"] = _check_disk("/kaggle/working" if os.path.isdir("/kaggle") else ".")
    report["imports"] = _check_imports()
    report["kaggle_inputs"] = _check_kaggle_inputs(input_root)
    report["locked_test_absent"] = _check_locked_test_absent()
    report["output_writable"] = _check_output_writable(output_root)
    report["nvidia_smi"] = _check_nvidia_smi()

    # Git SHA
    try:
        result = subprocess.run(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        report["git_sha"] = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        report["git_sha"] = "unknown"

    # Overall pass
    checks = ["python", "cuda", "vram", "disk", "imports", "locked_test_absent", "output_writable"]
    failed = [c for c in checks if not report.get(c, {}).get("ok", False)]
    # kaggle_inputs is only fatal on actual Kaggle
    if os.path.isdir("/kaggle") and not report["kaggle_inputs"]["ok"]:
        failed.append("kaggle_inputs")

    report["overall_ok"] = len(failed) == 0
    report["failed_checks"] = failed

    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="WOB-P1 robust preflight checks")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--input-root", default="/kaggle/input")
    args = parser.parse_args(argv)

    report = run_preflight(args.repo_root, args.output_root, args.log_dir, args.input_root)

    # Write report
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    report_path = log_dir / "preflight_robust_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Print summary
    print("=== Preflight Robust Report ===")
    print(json.dumps(report, indent=2))

    if not report["overall_ok"]:
        print(f"\nFATAL: Preflight failed checks: {report['failed_checks']}", file=sys.stderr)
        # Don't hard-fail for non-Kaggle environments (local dev)
        if os.path.isdir("/kaggle"):
            raise SystemExit(1)
        else:
            print("WARNING: Running outside Kaggle; continuing despite failures.", file=sys.stderr)


if __name__ == "__main__":
    main()
