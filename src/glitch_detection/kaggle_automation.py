from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@dataclass
class AutomationState:
    current_step: str = "preflight"
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    blocked_reason: str | None = None
    last_error_summary: str | None = None
    requires_approval: str | None = None
    attempts: dict[str, int] = field(default_factory=dict)
    dataset_fingerprint: str | None = None
    kernel_fingerprint: str | None = None
    kernel_status: str | None = None
    artifact_paths: dict[str, str] = field(default_factory=dict)
    gpu_push_fingerprints: list[str] = field(default_factory=list)
    dataset_uploaded_fingerprint: str | None = None
    execution_mode: str | None = None


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous_path = path.with_name("state.prev.json")

    def load(self) -> AutomationState:
        if not self.path.is_file():
            return AutomationState()
        return AutomationState(**json.loads(self.path.read_text(encoding="utf-8-sig")))

    def save(self, state: AutomationState) -> None:
        if self.path.is_file():
            self.previous_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.path, self.previous_path)
        _write_json_atomic(self.path, asdict(state))


class ApprovalStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _request_path(self, step: str) -> Path:
        return self.root / f"{step}.request.json"

    def _approved_path(self, step: str) -> Path:
        return self.root / f"{step}.approved.json"

    def request(self, step: str, fingerprint: str) -> dict[str, Any]:
        payload = {
            "step": step,
            "fingerprint": fingerprint,
            "requested_at": _utc_now(),
            "one_time_use": True,
        }
        _write_json_atomic(self._request_path(step), payload)
        return payload

    def approve(self, step: str, fingerprint: str) -> dict[str, Any]:
        request_path = self._request_path(step)
        if not request_path.is_file():
            raise FileNotFoundError(f"Missing approval request: {request_path}")
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
        if request.get("fingerprint") != fingerprint:
            raise ValueError("Approval request fingerprint does not match current fingerprint.")
        payload = {
            **request,
            "approved_at": _utc_now(),
            "consumed_at": None,
            "one_time_use": True,
        }
        _write_json_atomic(self._approved_path(step), payload)
        return payload

    def _read_approved(self, step: str) -> dict[str, Any] | None:
        path = self._approved_path(step)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def is_approved(self, step: str, fingerprint: str) -> bool:
        approved = self._read_approved(step)
        return bool(
            approved
            and approved.get("fingerprint") == fingerprint
            and approved.get("one_time_use") is True
            and approved.get("consumed_at") is None
        )

    def consume(self, step: str, fingerprint: str) -> dict[str, Any]:
        approved = self._read_approved(step)
        if approved is None:
            raise FileNotFoundError(f"Missing approved record for step: {step}")
        if approved.get("fingerprint") != fingerprint:
            raise ValueError("Approved fingerprint does not match current fingerprint.")
        if approved.get("consumed_at") is not None:
            raise ValueError(f"Approval for {step} has already been consumed.")
        approved["consumed_at"] = _utc_now()
        _write_json_atomic(self._approved_path(step), approved)
        return approved


class FingerprintBuilder:
    @staticmethod
    def sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def inventory_sha256(root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            digest.update(f"{relative}\0{path.stat().st_size}\n".encode())
        return digest.hexdigest()

    def build(
        self,
        *,
        git_commit_sha: str,
        branch: str,
        manifest_path: Path,
        split_path: Path,
        dataset_package_root: Path,
        kernel_script_path: Path,
        config: dict[str, Any],
        expected_partition_counts: dict[str, int],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "git_commit_sha": git_commit_sha,
            "branch": branch,
            "manifest_sha256": self.sha256_file(manifest_path),
            "split_sha256": self.sha256_file(split_path),
            "dataset_package_inventory_sha256": self.inventory_sha256(dataset_package_root),
            "kernel_script_sha256": self.sha256_file(kernel_script_path),
            "config_sha256": hashlib.sha256(
                json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "expected_partition_counts": dict(sorted(expected_partition_counts.items())),
        }
        result["combined_sha256"] = hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return result


class SecurityViolation(RuntimeError):
    """Raised when a package, command, or log violates credential/artifact rules."""


class SecurityGuard:
    FORBIDDEN_EXACT_NAMES = {
        "kaggle.json",
        "access_token",
        ".env",
        "id_rsa",
        "id_ed25519",
    }
    FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
    KERNEL_CHECKPOINT_SUFFIXES = {".pt", ".pth", ".ckpt"}
    TEXT_SCAN_SUFFIXES = {
        "",
        ".csv",
        ".env",
        ".json",
        ".md",
        ".py",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    TOKEN_PATTERN = re.compile(
        r"(?i)\b(KAGGLE_API_TOKEN|KAGGLE_KEY|api[_-]?key|access[_-]?token)"
        r"\s*[:=]\s*[\"']?([^\s\"']+)"
    )
    SENSITIVE_ENV_NAME = re.compile(r"(?i)(KAGGLE|TOKEN|KEY|SECRET|PASSWORD)")

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        source = dict(os.environ) if environment is None else environment
        self.sensitive_values = sorted(
            {
                value
                for key, value in source.items()
                if self.SENSITIVE_ENV_NAME.search(key) and len(value) >= 8
            },
            key=len,
            reverse=True,
        )

    @classmethod
    def _forbidden_reason(cls, path: Path, package_kind: str) -> str | None:
        name = path.name.lower()
        parts = {part.lower() for part in path.parts}
        if ".kaggle" in parts:
            return ".kaggle credential directory"
        if name in cls.FORBIDDEN_EXACT_NAMES or name.startswith(".env."):
            return f"forbidden credential filename: {path.name}"
        if path.suffix.lower() in cls.FORBIDDEN_SUFFIXES:
            return f"forbidden credential suffix: {path.suffix}"
        if package_kind == "kernel" and path.suffix.lower() in cls.KERNEL_CHECKPOINT_SUFFIXES:
            return f"checkpoint files are forbidden in kernel packages: {path.name}"
        lowered = path.as_posix().lower()
        if "/data/raw/" in f"/{lowered}/":
            return "data/raw content is forbidden"
        if "outputs" in parts:
            return "nested outputs content is forbidden"
        return None

    def _contains_sensitive_content(self, text: str) -> bool:
        return bool(
            self.TOKEN_PATTERN.search(text)
            or any(value and value in text for value in self.sensitive_values)
        )

    def scan_package(self, root: Path, package_kind: str) -> None:
        if package_kind not in {"dataset", "kernel", "repo"}:
            raise ValueError(f"Unsupported package kind: {package_kind}")
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            reason = self._forbidden_reason(path.relative_to(root), package_kind)
            if reason:
                raise SecurityViolation(reason)
            if (
                path.stat().st_size > 1024 * 1024
                or path.suffix.lower() not in self.TEXT_SCAN_SUFFIXES
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            if self._contains_sensitive_content(text):
                raise SecurityViolation(
                    f"Package contains token-like credential content: {path.relative_to(root)}"
                )

    def scan_tracked_files(self, repo_root: Path, tracked_paths: list[str]) -> None:
        for relative_text in tracked_paths:
            relative = Path(relative_text)
            reason = self._forbidden_reason(relative, "repo")
            if reason:
                raise SecurityViolation(reason)
            path = repo_root / relative
            if not path.is_file() or path.stat().st_size > 1024 * 1024:
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            if self._contains_sensitive_content(text):
                raise SecurityViolation(f"Tracked file contains token-like credential: {relative}")

    def scan_command(self, command: str) -> None:
        if self._contains_sensitive_content(command):
            raise SecurityViolation("Command contains a token-like credential value.")

    def redact(self, text: str) -> str:
        redacted = self.TOKEN_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)
        for value in self.sensitive_values:
            redacted = redacted.replace(value, "<redacted>")
        return redacted


TRANSIENT_PATTERNS = (
    re.compile(r"\b(?:429|500|502|503|504)\b"),
    re.compile(r"(?i)\b(?:timed? out|timeout)\b"),
    re.compile(r"(?i)connection reset"),
    re.compile(r"(?i)temporary (?:failure|dns|network)"),
    re.compile(r"(?i)name resolution"),
)
GPU_BLOCK_PATTERNS = (
    re.compile(r"(?i)gpu quota"),
    re.compile(r"(?i)accelerator unavailable"),
    re.compile(r"(?i)no accelerator"),
)


def is_transient_error(message: str) -> bool:
    return any(pattern.search(message) for pattern in TRANSIENT_PATTERNS)


def _gpu_block_reason(message: str) -> str | None:
    if any(pattern.search(message) for pattern in GPU_BLOCK_PATTERNS):
        return message.strip() or "GPU quota exhausted or accelerator unavailable."
    return None


class AutomationCommandError(RuntimeError):
    def __init__(self, message: str, *, stdout: str = "", stderr: str = "") -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


class AutomationBlockedError(RuntimeError):
    """Raised for non-retryable external-state blockers."""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    attempts: int


class CommandRunner:
    def __init__(
        self,
        *,
        executor: Callable[[list[str]], Any] | None = None,
        security_guard: SecurityGuard | None = None,
        max_attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.executor = executor or self._default_executor
        self.security_guard = security_guard or SecurityGuard()
        self.max_attempts = max_attempts
        self.sleep = sleep

    @staticmethod
    def _default_executor(command: list[str]) -> Any:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise AutomationCommandError(
                f"Command failed with exit code {completed.returncode}: {' '.join(command)}",
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        return completed

    def _write_log(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(self.security_guard.redact(text))

    def run(self, step: str, command: list[str], log_path: Path) -> CommandResult:
        command_text = " ".join(command)
        self.security_guard.scan_command(command_text)
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = self.executor(command)
                stdout = self.security_guard.redact(str(getattr(result, "stdout", "")))
                stderr = self.security_guard.redact(str(getattr(result, "stderr", "")))
                self._write_log(
                    log_path,
                    f"[{_utc_now()}] step={step} attempt={attempt} status=success\n"
                    f"stdout:\n{stdout}\nstderr:\n{stderr}\n",
                )
                return CommandResult(
                    returncode=int(getattr(result, "returncode", 0)),
                    stdout=stdout,
                    stderr=stderr,
                    attempts=attempt,
                )
            except AutomationCommandError as exc:
                combined = "\n".join([str(exc), exc.stdout, exc.stderr])
                redacted = self.security_guard.redact(combined)
                self._write_log(
                    log_path,
                    f"[{_utc_now()}] step={step} attempt={attempt} status=failed\n{redacted}\n",
                )
                blocked_reason = _gpu_block_reason(redacted)
                if blocked_reason:
                    raise AutomationBlockedError(blocked_reason) from exc
                if not is_transient_error(redacted) or attempt >= self.max_attempts:
                    raise
                self.sleep(float(2 ** (attempt - 1)))
        raise RuntimeError("Command retry loop exited unexpectedly.")


class PackageValidator:
    def __init__(self, security_guard: SecurityGuard | None = None) -> None:
        self.security_guard = security_guard or SecurityGuard()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise FileNotFoundError(f"Missing package metadata: {path}")
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def validate_dataset(
        self,
        root: Path,
        *,
        expected_slug: str,
        recursive_mode: str,
        is_private: bool,
    ) -> dict[str, Any]:
        self.security_guard.scan_package(root, package_kind="dataset")
        if not is_private:
            raise ValueError("Phase 6E Kaggle dataset must remain private.")
        if recursive_mode not in {"zip", "tar"}:
            raise ValueError("Dataset recursive mode must be zip or tar.")
        required = [
            root / "tempglitch_phase3b" / "manifest.csv",
            root / "split.csv",
            root / "dataset-metadata.json",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing dataset package files: {', '.join(missing)}")
        metadata = self._read_json(root / "dataset-metadata.json")
        licenses = metadata.get("licenses", [])
        license_name = str(licenses[0].get("name", "")) if licenses else ""
        if metadata.get("id") != expected_slug:
            raise ValueError("Dataset metadata id does not match expected private dataset slug.")
        if license_name != "other":
            raise ValueError("Dataset metadata license must be 'other'.")
        return {
            "dataset_slug": expected_slug,
            "is_private": True,
            "license": license_name,
            "recursive_mode": recursive_mode,
        }

    def validate_kernel(
        self,
        root: Path,
        *,
        expected_slug: str,
        dataset_slug: str,
    ) -> dict[str, Any]:
        self.security_guard.scan_package(root, package_kind="kernel")
        metadata = self._read_json(root / "kernel-metadata.json")
        code_file = root / str(metadata.get("code_file", ""))
        if not code_file.is_file():
            raise FileNotFoundError(f"Missing kernel code file: {code_file}")
        if metadata.get("id") != expected_slug:
            raise ValueError("Kernel metadata id does not match expected slug.")
        if metadata.get("is_private") is not True:
            raise ValueError("Phase 6E Kaggle kernel must remain private.")
        if metadata.get("kernel_type") != "script" or metadata.get("language") != "python":
            raise ValueError("Phase 6E Kaggle kernel must be a Python script.")
        if dataset_slug not in metadata.get("dataset_sources", []):
            raise ValueError("Kernel metadata does not attach the required private dataset.")
        return {
            "kernel_slug": expected_slug,
            "dataset_slug": dataset_slug,
            "is_private": True,
            "code_file": str(code_file),
        }


class ArtifactValidator:
    REQUIRED_FILES = (
        "video_autoencoder.pt",
        "training_metadata.json",
        "validation_scores.csv",
        "phase6e_summary.json",
        "protocol_audit.json",
    )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _write_report(summary: dict[str, Any], output_path: Path) -> None:
        lines = [
            "# Phase 6E Automation Artifact Validation",
            "",
            f"- Status: `{summary['status']}`",
            f"- Device: `{summary['device']}`",
            f"- Validation rows: `{summary['validation_row_count']}`",
            f"- NaN/non-finite scores: `{summary['nan_or_non_finite_score_count']}`",
            f"- Test scored: `{str(summary['test_scored']).lower()}`",
            "",
            "Locked test remains untouched. This report does not establish neural performance.",
        ]
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def locate_root(self, root: Path) -> Path:
        if all((root / name).is_file() for name in self.REQUIRED_FILES):
            return root
        candidates = [
            path.parent
            for path in root.rglob("phase6e_summary.json")
            if all((path.parent / name).is_file() for name in self.REQUIRED_FILES)
        ]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            raise ValueError(f"Multiple Phase 6E artifact roots found under: {root}")
        return root

    def validate(
        self,
        artifact_root: Path,
        output_root: Path,
        *,
        expected_validation_rows: int = 1071,
    ) -> dict[str, Any]:
        artifact_root = self.locate_root(artifact_root)
        missing = [name for name in self.REQUIRED_FILES if not (artifact_root / name).is_file()]
        if missing:
            raise FileNotFoundError(f"Missing required artifact(s): {', '.join(missing)}")
        metadata = self._read_json(artifact_root / "training_metadata.json")
        phase_summary = self._read_json(artifact_root / "phase6e_summary.json")
        audit = self._read_json(artifact_root / "protocol_audit.json")
        device = str(metadata.get("device", ""))
        if "cuda" not in device.lower():
            raise ValueError(
                f"training_metadata.device must contain cuda, got: {device or 'missing'}"
            )
        if audit.get("test_scored") is not False:
            raise ValueError("protocol_audit.json must explicitly contain test_scored=false.")
        test_scored = bool(phase_summary.get("test_scored", False) or audit["test_scored"])
        if test_scored:
            raise ValueError("protocol_audit.json must report test_scored=false.")

        with (artifact_root / "validation_scores.csv").open(
            "r", newline="", encoding="utf-8-sig"
        ) as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != expected_validation_rows:
            raise ValueError(
                f"Expected {expected_validation_rows} validation rows, found {len(rows)}."
            )
        invalid_count = 0
        for row in rows:
            try:
                value = float(row["score"])
            except (KeyError, TypeError, ValueError):
                invalid_count += 1
                continue
            if not math.isfinite(value):
                invalid_count += 1
        if invalid_count:
            raise ValueError(f"Found {invalid_count} non-numeric or non-finite validation scores.")

        summary = {
            "status": "artifact validation complete",
            "artifact_root": str(artifact_root),
            "device": device,
            "validation_row_count": len(rows),
            "nan_or_non_finite_score_count": invalid_count,
            "test_scored": False,
        }
        output_root.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(output_root / "artifact_validation_summary.json", summary)
        self._write_report(summary, output_root / "artifact_validation_report.md")
        return summary


AUTOMATION_STEPS = (
    "preflight",
    "auth_check_or_request_login",
    "repo_and_security_scan",
    "dataset_dry_run",
    "dataset_prepare",
    "dataset_validate_package",
    "dataset_fingerprint",
    "dataset_upload_approval",
    "dataset_create_or_version",
    "kernel_package_generate",
    "kernel_validate_package",
    "kernel_push_approval",
    "kernel_push_once",
    "kernel_poll",
    "artifact_download",
    "artifact_validate",
    "artifact_ingest",
    "complete",
)
APPROVAL_STEPS = {
    "dataset_upload_approval": ("dataset_fingerprint", "dataset_create_or_version"),
    "kernel_push_approval": ("kernel_fingerprint", "kernel_push_once"),
}
LIVE_ACTION_APPROVALS = {
    "dataset_create_or_version": ("dataset_upload_approval", "dataset_fingerprint"),
    "kernel_push_once": ("kernel_push_approval", "kernel_fingerprint"),
}


class Phase6EKaggleOrchestrator:
    def __init__(
        self,
        *,
        root: Path,
        handlers: dict[str, Callable[[AutomationState], dict[str, Any]]],
        dry_run: bool,
        security_guard: SecurityGuard | None = None,
    ) -> None:
        self.root = root
        self.handlers = handlers
        self.dry_run = dry_run
        self.security_guard = security_guard or SecurityGuard()
        self.state_store = StateStore(root / "state.json")
        self.approval_store = ApprovalStore(root / "approvals")

    @staticmethod
    def _next_step(step: str) -> str:
        index = AUTOMATION_STEPS.index(step)
        return AUTOMATION_STEPS[min(index + 1, len(AUTOMATION_STEPS) - 1)]

    @staticmethod
    def _fingerprint_for_step(state: AutomationState, fingerprint_field: str) -> str:
        fingerprint = getattr(state, fingerprint_field)
        if not fingerprint:
            raise ValueError(f"Missing {fingerprint_field} before approval/live action.")
        return str(fingerprint)

    @staticmethod
    def _complete_step(state: AutomationState, step: str) -> None:
        if step not in state.completed_steps:
            state.completed_steps.append(step)
        state.current_step = Phase6EKaggleOrchestrator._next_step(step)
        state.failed_step = None
        state.blocked_reason = None
        state.last_error_summary = None
        state.requires_approval = None

    def approve_step(self, step: str) -> dict[str, Any]:
        if step not in APPROVAL_STEPS:
            raise ValueError(f"Unsupported approval step: {step}")
        state = self.state_store.load()
        expected_mode = "dry-run" if self.dry_run else "live"
        if state.execution_mode != expected_mode:
            raise ValueError(
                f"State mode is {state.execution_mode or 'unset'}; run the orchestrator in "
                f"{expected_mode} mode before approving."
            )
        validation_steps = ["repo_and_security_scan"]
        validation_steps.append(
            "dataset_validate_package"
            if step == "dataset_upload_approval"
            else "kernel_validate_package"
        )
        for validation_step in validation_steps:
            handler = self.handlers.get(validation_step)
            if handler is not None:
                handler(state)
        fingerprint_field, _action = APPROVAL_STEPS[step]
        fingerprint = self._fingerprint_for_step(state, fingerprint_field)
        return self.approval_store.approve(step, fingerprint)

    def _handle_approval(self, state: AutomationState, step: str) -> bool:
        fingerprint_field, _action = APPROVAL_STEPS[step]
        fingerprint = self._fingerprint_for_step(state, fingerprint_field)
        if self.approval_store.is_approved(step, fingerprint):
            self._complete_step(state, step)
            self.state_store.save(state)
            return True
        self.approval_store.request(step, fingerprint)
        state.current_step = step
        state.requires_approval = step
        state.blocked_reason = f"approval required: {step}"
        self.state_store.save(state)
        return False

    def _before_live_action(self, state: AutomationState, step: str) -> None:
        if self.dry_run:
            state.current_step = step
            state.blocked_reason = "dry-run: live action not executed"
            self.state_store.save(state)
            raise AutomationBlockedError(state.blocked_reason)
        approval_step, fingerprint_field = LIVE_ACTION_APPROVALS[step]
        fingerprint = self._fingerprint_for_step(state, fingerprint_field)
        if step == "kernel_push_once" and fingerprint in state.gpu_push_fingerprints:
            if state.kernel_status in {"running", "success"}:
                self._complete_step(state, step)
                self.state_store.save(state)
                return
            raise AutomationBlockedError(
                f"GPU push already used for kernel fingerprint: {fingerprint}"
            )
        self.approval_store.consume(approval_step, fingerprint)
        if step == "kernel_push_once":
            state.gpu_push_fingerprints.append(fingerprint)
        self.state_store.save(state)

    def _apply_updates(self, state: AutomationState, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if not hasattr(state, key):
                raise ValueError(f"Handler returned unsupported state field: {key}")
            old_value = getattr(state, key)
            if key == "artifact_paths":
                value = {**state.artifact_paths, **dict(value)}
            setattr(state, key, value)
            if (
                old_value
                and old_value != value
                and key
                in {
                    "dataset_fingerprint",
                    "kernel_fingerprint",
                }
            ):
                reset_step = (
                    "dataset_upload_approval"
                    if key == "dataset_fingerprint"
                    else "kernel_push_approval"
                )
                reset_index = AUTOMATION_STEPS.index(reset_step)
                state.completed_steps = [
                    step
                    for step in state.completed_steps
                    if AUTOMATION_STEPS.index(step) < reset_index
                ]
                if AUTOMATION_STEPS.index(state.current_step) >= reset_index:
                    state.current_step = reset_step
                state.requires_approval = reset_step

    def _refresh_fingerprints(self, state: AutomationState) -> None:
        for handler_name in ["refresh_dataset_fingerprint", "refresh_kernel_fingerprint"]:
            handler = self.handlers.get(handler_name)
            if handler is not None:
                self._apply_updates(state, handler(state) or {})
        self.state_store.save(state)

    def _reconcile_execution_mode(self, state: AutomationState) -> None:
        mode = "dry-run" if self.dry_run else "live"
        if state.execution_mode == "dry-run" and mode == "live":
            reset_index = AUTOMATION_STEPS.index("auth_check_or_request_login")
            state.completed_steps = [
                step for step in state.completed_steps if AUTOMATION_STEPS.index(step) < reset_index
            ]
            state.current_step = "auth_check_or_request_login"
            state.requires_approval = None
            state.blocked_reason = None
        state.execution_mode = mode
        self.state_store.save(state)

    def run(self) -> AutomationState:
        state = self.state_store.load()
        state.blocked_reason = None
        state.last_error_summary = None
        self._reconcile_execution_mode(state)
        self._refresh_fingerprints(state)
        while True:
            step = state.current_step
            if step in state.completed_steps:
                state.current_step = self._next_step(step)
                self.state_store.save(state)
                continue
            if step in APPROVAL_STEPS:
                if self._handle_approval(state, step):
                    continue
                return state
            if step in LIVE_ACTION_APPROVALS:
                try:
                    before_step = state.current_step
                    self._before_live_action(state, step)
                    if state.current_step != before_step:
                        continue
                except AutomationBlockedError as exc:
                    state.blocked_reason = self.security_guard.redact(str(exc))
                    state.failed_step = step
                    self.state_store.save(state)
                    if self.dry_run:
                        return state
                    raise
            handler = self.handlers.get(step)
            try:
                state.attempts[step] = state.attempts.get(step, 0) + 1
                updates = handler(state) if handler is not None else {}
                self._apply_updates(state, updates or {})
                self._complete_step(state, step)
                self.state_store.save(state)
                if step == "complete":
                    return state
            except AutomationBlockedError as exc:
                state.failed_step = step
                state.blocked_reason = self.security_guard.redact(str(exc))
                state.last_error_summary = state.blocked_reason
                self.state_store.save(state)
                raise
            except Exception as exc:
                state.failed_step = step
                state.last_error_summary = self.security_guard.redact(str(exc))
                self.state_store.save(state)
                raise


@dataclass(frozen=True)
class AutomationConfig:
    repo_root: Path
    automation_root: Path
    processed_root: Path
    split_path: Path
    dataset_package_root: Path
    kernel_package_root: Path
    downloaded_root: Path
    ingested_root: Path
    dataset_slug: str = "thanhhuynhdieu/glitch-world-model-phase6e"
    kernel_slug: str = "thanhhuynhdieu/phase6e-video-autoencoder"
    branch: str = "codex/phase6e-kaggle-video-autoencoder"
    accelerator: str = "NvidiaTeslaT4"
    recursive_mode: str = "zip"
    max_attempts: int = 3
    poll_timeout_seconds: int = 6 * 60 * 60
    expected_train_normal_clips: int = 1724
    expected_validation_clips: int = 1071
    expected_test_clips: int = 1125
    dry_run: bool = True


class DefaultPhase6EHandlers:
    def __init__(
        self,
        config: AutomationConfig,
        *,
        command_runner: CommandRunner | None = None,
        security_guard: SecurityGuard | None = None,
    ) -> None:
        self.config = config
        self.security_guard = security_guard or SecurityGuard()
        self.command_runner = command_runner or CommandRunner(
            security_guard=self.security_guard,
            max_attempts=config.max_attempts,
        )
        self.package_validator = PackageValidator(self.security_guard)
        self.fingerprint_builder = FingerprintBuilder()
        self.artifact_validator = ArtifactValidator()
        self.logs_root = config.automation_root / "logs"
        self.dry_dataset_root = config.automation_root / "dry_run_dataset_package"
        self.planned_kernel_script = config.automation_root / "planned_phase6e_train_kernel.py"

    def _log(self, step: str) -> Path:
        return self.logs_root / f"{step}.log"

    def _kaggle(self, *args: str) -> list[str]:
        return [sys.executable, "-m", "kaggle", *args]

    def _run(self, step: str, command: list[str]) -> CommandResult:
        return self.command_runner.run(step, command, self._log(step))

    def _git_value(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.config.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()

    def _config_payload(self) -> dict[str, Any]:
        return {
            "dataset_slug": self.config.dataset_slug,
            "kernel_slug": self.config.kernel_slug,
            "branch": self.config.branch,
            "accelerator": self.config.accelerator,
            "recursive_mode": self.config.recursive_mode,
            "expected_partition_counts": {
                "train_normal": self.config.expected_train_normal_clips,
                "validation": self.config.expected_validation_clips,
                "test": self.config.expected_test_clips,
            },
        }

    def _expected_counts(self) -> dict[str, int]:
        return {
            "train_normal": self.config.expected_train_normal_clips,
            "validation": self.config.expected_validation_clips,
            "test": self.config.expected_test_clips,
        }

    def _render_kernel_script(self) -> str:
        dataset_name = self.config.dataset_slug.split("/", 1)[1]
        return f"""from pathlib import Path
import subprocess
import sys

repo = Path("/kaggle/working/glitch-world-model")
subprocess.run(
    ["git", "clone", "--branch", "{self.config.branch}",
     "https://github.com/thanhdicode/glitch-world-model.git", str(repo)],
    check=True,
)
common = [
    sys.executable,
    str(repo / "scripts" / "run_kaggle_video_autoencoder.py"),
    "--manifest", "/kaggle/input/{dataset_name}/tempglitch_phase3b/manifest.csv",
    "--split", "/kaggle/input/{dataset_name}/split.csv",
    "--clips-root", "/kaggle/input/{dataset_name}/tempglitch_phase3b",
    "--output-root", "/kaggle/working/tempglitch_phase6e/seed_42",
    "--device", "cuda",
    "--seed", "42",
]
subprocess.run([*common, "--dry-run"], check=True)
subprocess.run(common, check=True)
"""

    def _write_lightweight_dataset_package(self) -> Path:
        root = self.dry_dataset_root
        (root / "tempglitch_phase3b").mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.config.processed_root / "manifest.csv", root / "tempglitch_phase3b")
        shutil.copy2(self.config.split_path, root / "split.csv")
        _write_json_atomic(
            root / "dataset-metadata.json",
            {
                "title": "glitch-world-model-phase6e",
                "id": self.config.dataset_slug,
                "licenses": [{"name": "other"}],
            },
        )
        return root

    def _dataset_root(self) -> Path:
        return self.dry_dataset_root if self.config.dry_run else self.config.dataset_package_root

    def _dataset_fingerprint(self) -> str:
        self.planned_kernel_script.parent.mkdir(parents=True, exist_ok=True)
        self.planned_kernel_script.write_text(self._render_kernel_script(), encoding="utf-8")
        payload = self.fingerprint_builder.build(
            git_commit_sha=self._git_value("rev-parse", "HEAD"),
            branch=self._git_value("branch", "--show-current"),
            manifest_path=self.config.processed_root / "manifest.csv",
            split_path=self.config.split_path,
            dataset_package_root=(
                self.config.processed_root
                if self.config.dry_run
                else self.config.dataset_package_root
            ),
            kernel_script_path=self.planned_kernel_script,
            config=self._config_payload(),
            expected_partition_counts=self._expected_counts(),
        )
        _write_json_atomic(self.config.automation_root / "dataset_fingerprint.json", payload)
        return str(payload["combined_sha256"])

    def preflight(self, _state: AutomationState) -> dict[str, Any]:
        required = [
            self.config.processed_root / "manifest.csv",
            self.config.split_path,
            self.config.repo_root / "scripts" / "prepare_phase6e_kaggle_dataset.py",
            self.config.repo_root / "scripts" / "ingest_phase6e_kaggle_artifacts.py",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing Phase 6E prerequisite(s): {', '.join(missing)}")
        if not self.config.dry_run and importlib.util.find_spec("kaggle") is None:
            self._run(
                "preflight",
                [sys.executable, "-m", "pip", "install", "--upgrade", "kaggle"],
            )
        return {}

    def auth_check_or_request_login(self, _state: AutomationState) -> dict[str, Any]:
        if self.config.dry_run:
            return {}
        try:
            self._run("auth_check_or_request_login", self._kaggle("datasets", "list", "--mine"))
        except AutomationCommandError:
            self._run("auth_check_or_request_login", self._kaggle("auth", "login"))
            self._run("auth_check_or_request_login", self._kaggle("datasets", "list", "--mine"))
        return {}

    def repo_and_security_scan(self, _state: AutomationState) -> dict[str, Any]:
        tracked = self._git_value("ls-files").splitlines()
        self.security_guard.scan_tracked_files(self.config.repo_root, tracked)
        return {}

    def dataset_dry_run(self, _state: AutomationState) -> dict[str, Any]:
        self._run(
            "dataset_dry_run",
            [
                sys.executable,
                str(self.config.repo_root / "scripts" / "prepare_phase6e_kaggle_dataset.py"),
                "--dry-run",
                "--processed-root",
                str(self.config.processed_root),
                "--split",
                str(self.config.split_path),
                "--output-root",
                str(self.config.dataset_package_root),
            ],
        )
        return {}

    def dataset_prepare(self, _state: AutomationState) -> dict[str, Any]:
        if self.config.dry_run:
            self._write_lightweight_dataset_package()
            return {}
        if not self.config.dataset_package_root.exists():
            self._run(
                "dataset_prepare",
                [
                    sys.executable,
                    str(self.config.repo_root / "scripts" / "prepare_phase6e_kaggle_dataset.py"),
                    "--copy",
                    "--processed-root",
                    str(self.config.processed_root),
                    "--split",
                    str(self.config.split_path),
                    "--output-root",
                    str(self.config.dataset_package_root),
                ],
            )
        _write_json_atomic(
            self.config.dataset_package_root / "dataset-metadata.json",
            {
                "title": "glitch-world-model-phase6e",
                "id": self.config.dataset_slug,
                "licenses": [{"name": "other"}],
            },
        )
        return {}

    def dataset_validate_package(self, _state: AutomationState) -> dict[str, Any]:
        self.security_guard.scan_package(self.config.processed_root, package_kind="dataset")
        self.package_validator.validate_dataset(
            self._dataset_root(),
            expected_slug=self.config.dataset_slug,
            recursive_mode=self.config.recursive_mode,
            is_private=True,
        )
        return {}

    def dataset_fingerprint(self, _state: AutomationState) -> dict[str, Any]:
        return {"dataset_fingerprint": self._dataset_fingerprint()}

    def refresh_dataset_fingerprint(self, state: AutomationState) -> dict[str, Any]:
        if not state.dataset_fingerprint:
            return {}
        return {"dataset_fingerprint": self._dataset_fingerprint()}

    def dataset_create_or_version(self, state: AutomationState) -> dict[str, Any]:
        if state.dataset_uploaded_fingerprint == state.dataset_fingerprint:
            return {}
        try:
            self._run(
                "dataset_create_or_version",
                self._kaggle("datasets", "status", self.config.dataset_slug),
            )
            command = self._kaggle(
                "datasets",
                "version",
                "-p",
                str(self.config.dataset_package_root),
                "-m",
                "Phase 6E dataset update",
                "-r",
                self.config.recursive_mode,
            )
        except AutomationCommandError as exc:
            if "not found" not in str(exc).lower():
                raise
            command = self._kaggle(
                "datasets",
                "create",
                "-p",
                str(self.config.dataset_package_root),
                "-r",
                self.config.recursive_mode,
            )
        self._run("dataset_create_or_version", command)
        return {"dataset_uploaded_fingerprint": state.dataset_fingerprint}

    def kernel_package_generate(self, state: AutomationState) -> dict[str, Any]:
        root = self.config.kernel_package_root
        root.mkdir(parents=True, exist_ok=True)
        script_path = root / "phase6e_train_kernel.py"
        script_path.write_text(self._render_kernel_script(), encoding="utf-8")
        _write_json_atomic(
            root / "kernel-metadata.json",
            {
                "id": self.config.kernel_slug,
                "title": "Phase 6E Video Autoencoder",
                "code_file": script_path.name,
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "enable_gpu": True,
                "enable_internet": True,
                "dataset_sources": [self.config.dataset_slug],
            },
        )
        kernel_payload = {
            "dataset_fingerprint": state.dataset_fingerprint,
            "kernel_script_sha256": self.fingerprint_builder.sha256_file(script_path),
            "config": self._config_payload(),
        }
        fingerprint = hashlib.sha256(
            json.dumps(kernel_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        _write_json_atomic(
            self.config.automation_root / "kernel_fingerprint.json",
            {**kernel_payload, "combined_sha256": fingerprint},
        )
        return {"kernel_fingerprint": fingerprint}

    def refresh_kernel_fingerprint(self, state: AutomationState) -> dict[str, Any]:
        script_path = self.config.kernel_package_root / "phase6e_train_kernel.py"
        if not state.kernel_fingerprint or not script_path.is_file():
            return {}
        payload = {
            "dataset_fingerprint": state.dataset_fingerprint,
            "kernel_script_sha256": self.fingerprint_builder.sha256_file(script_path),
            "config": self._config_payload(),
        }
        return {
            "kernel_fingerprint": hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        }

    def kernel_validate_package(self, _state: AutomationState) -> dict[str, Any]:
        self.package_validator.validate_kernel(
            self.config.kernel_package_root,
            expected_slug=self.config.kernel_slug,
            dataset_slug=self.config.dataset_slug,
        )
        return {}

    def kernel_push_once(self, _state: AutomationState) -> dict[str, Any]:
        self._run(
            "kernel_push_once",
            self._kaggle(
                "kernels",
                "push",
                "-p",
                str(self.config.kernel_package_root),
                "--accelerator",
                self.config.accelerator,
            ),
        )
        return {"kernel_status": "running"}

    def kernel_poll(self, _state: AutomationState) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.poll_timeout_seconds
        while time.monotonic() < deadline:
            result = self._run(
                "kernel_poll", self._kaggle("kernels", "status", self.config.kernel_slug)
            )
            status = result.stdout.lower()
            if "complete" in status or "success" in status:
                return {"kernel_status": "success"}
            if "error" in status or "failed" in status:
                raise AutomationBlockedError(f"Kaggle kernel failed: {result.stdout.strip()}")
            time.sleep(60)
        raise AutomationBlockedError("Kaggle kernel polling exceeded the 6-hour timeout.")

    def artifact_download(self, _state: AutomationState) -> dict[str, Any]:
        self.config.downloaded_root.mkdir(parents=True, exist_ok=True)
        self._run(
            "artifact_download",
            self._kaggle(
                "kernels",
                "output",
                self.config.kernel_slug,
                "-p",
                str(self.config.downloaded_root),
                "-o",
            ),
        )
        return {"artifact_paths": {"downloaded_root": str(self.config.downloaded_root)}}

    def artifact_validate(self, _state: AutomationState) -> dict[str, Any]:
        validation_root = self.config.automation_root / "artifact_validation"
        summary = self.artifact_validator.validate(
            self.config.downloaded_root,
            validation_root,
            expected_validation_rows=self.config.expected_validation_clips,
        )
        return {
            "artifact_paths": {
                "downloaded_root": str(self.config.downloaded_root),
                "artifact_root": str(summary["artifact_root"]),
                "validation_root": str(validation_root),
            }
        }

    def artifact_ingest(self, state: AutomationState) -> dict[str, Any]:
        artifact_root = Path(
            state.artifact_paths.get(
                "artifact_root",
                str(self.artifact_validator.locate_root(self.config.downloaded_root)),
            )
        )
        self._run(
            "artifact_ingest",
            [
                sys.executable,
                str(self.config.repo_root / "scripts" / "ingest_phase6e_kaggle_artifacts.py"),
                "--artifact-root",
                str(artifact_root),
                "--output-root",
                str(self.config.ingested_root),
            ],
        )
        return {
            "artifact_paths": {
                "downloaded_root": str(self.config.downloaded_root),
                "artifact_root": str(artifact_root),
                "ingested_root": str(self.config.ingested_root),
            }
        }

    def complete(self, _state: AutomationState) -> dict[str, Any]:
        return {}

    def as_mapping(self) -> dict[str, Callable[[AutomationState], dict[str, Any]]]:
        return {
            name: getattr(self, name)
            for name in [
                "preflight",
                "auth_check_or_request_login",
                "repo_and_security_scan",
                "dataset_dry_run",
                "dataset_prepare",
                "dataset_validate_package",
                "dataset_fingerprint",
                "refresh_dataset_fingerprint",
                "dataset_create_or_version",
                "kernel_package_generate",
                "refresh_kernel_fingerprint",
                "kernel_validate_package",
                "kernel_push_once",
                "kernel_poll",
                "artifact_download",
                "artifact_validate",
                "artifact_ingest",
                "complete",
            ]
        }
