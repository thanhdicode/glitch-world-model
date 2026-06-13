from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _output_root(path_arg: Path | None) -> Path:
    if path_arg is not None:
        return path_arg
    value = os.environ.get("LEWM_OUTPUT_ROOT")
    if not value:
        raise RuntimeError("LEWM_OUTPUT_ROOT is required when --output-root is omitted.")
    return Path(value)


def inspect_runtime(*, min_major: int, min_vram_gb: float) -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - exercised on cloud when torch is missing.
        return {
            "status": "failed",
            "reason": "torch_import_failed",
            "message": str(exc),
            "python": sys.version,
        }

    cuda_available = bool(torch.cuda.is_available())
    gpus: list[dict[str, Any]] = []
    if cuda_available:
        for index in range(torch.cuda.device_count()):
            major, minor = torch.cuda.get_device_capability(index)
            props = torch.cuda.get_device_properties(index)
            total_memory_gb = float(props.total_memory) / 1024**3
            gpus.append(
                {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                    "compute_capability": [int(major), int(minor)],
                    "total_memory_gb": total_memory_gb,
                    "supported_compute": int(major) >= min_major,
                    "supported_memory": total_memory_gb >= min_vram_gb,
                }
            )

    supported = bool(
        cuda_available
        and gpus
        and all(gpu["supported_compute"] and gpu["supported_memory"] for gpu in gpus)
    )
    reason = None
    if not cuda_available:
        reason = "cuda_unavailable"
    elif not gpus:
        reason = "no_cuda_devices"
    elif not supported:
        reason = "unsupported_gpu_runtime"

    return {
        "status": "passed" if supported else "failed",
        "reason": reason,
        "python": sys.version,
        "torch": torch.__version__,
        "cuda_available": cuda_available,
        "gpu_count": len(gpus),
        "gpus": gpus,
        "minimum_compute_capability": [min_major, 0],
        "minimum_vram_gb": min_vram_gb,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate a cloud GPU runtime for LeWM R3.")
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--min-compute-major", type=int, default=7)
    parser.add_argument("--min-vram-gb", type=float, default=14.0)
    args = parser.parse_args(argv)

    output_root = _output_root(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    result = inspect_runtime(
        min_major=args.min_compute_major,
        min_vram_gb=args.min_vram_gb,
    )
    output_path = output_root / "cloud_runtime_preflight.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
