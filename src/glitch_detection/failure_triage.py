from __future__ import annotations

import re
from enum import StrEnum


class FailureBucket(StrEnum):
    CUDA_OOM = "cuda_oom"
    GPU_COMPUTE_CAPABILITY = "gpu_compute_capability"
    DATALOADER_SPAWN = "dataloader_spawn"
    ENVIRONMENT_DECODE = "environment_decode"
    PACKAGING_IDEMPOTENCY = "packaging_idempotency"
    INFRA_KAGGLE_TRANSIENT = "infra_kaggle_transient"
    UNKNOWN = "unknown"


_SIGNATURES = (
    (
        FailureBucket.CUDA_OOM,
        re.compile(r"(?i)(cuda out of memory|out of memory|cublas_status_alloc_failed)"),
    ),
    (
        FailureBucket.GPU_COMPUTE_CAPABILITY,
        re.compile(
            r"(?i)(compute capability|sm_60|no kernel image is available for execution|"
            r"not compatible with the current pytorch installation|tesla p100)"
        ),
    ),
    (
        FailureBucket.DATALOADER_SPAWN,
        re.compile(
            r"(?i)(bootstrapping phase|freeze_support|attempt has been made to start a new process)"
        ),
    ),
    (
        FailureBucket.ENVIRONMENT_DECODE,
        re.compile(r"(?i)(unicodedecodeerror|charmap|cp1252|codec can(?:not|'t) decode)"),
    ),
    (
        FailureBucket.PACKAGING_IDEMPOTENCY,
        re.compile(r"(?i)(fileexistserror|already exists)"),
    ),
    (
        FailureBucket.INFRA_KAGGLE_TRANSIENT,
        re.compile(r"(?i)(connection reset|timed? out|timeout|serviceunavailable|\b503\b)"),
    ),
)


def classify_failure(stderr: str, exc_type: str | None = None) -> FailureBucket:
    text = "\n".join(part for part in (exc_type or "", stderr) if part)
    normalized = text.lower().replace("-", "_")
    if "cuda_oom" in normalized:
        return FailureBucket.CUDA_OOM
    for bucket, pattern in _SIGNATURES:
        if pattern.search(text):
            return bucket
    return FailureBucket.UNKNOWN


def allowed_action(bucket: FailureBucket) -> str:
    if bucket is FailureBucket.CUDA_OOM:
        return "oom_ladder_step"
    if bucket is FailureBucket.INFRA_KAGGLE_TRANSIENT:
        return "bounded_retry"
    return "stop_and_fix"


def is_oom(bucket: FailureBucket) -> bool:
    return bucket is FailureBucket.CUDA_OOM
