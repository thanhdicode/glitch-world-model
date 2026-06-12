from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import (
    AutomationBlockedError,
    AutomationCommandError,
    AutomationState,
    CommandRunner,
    FingerprintBuilder,
    KaggleAction,
    KaggleExecutionPolicy,
    PublicReleaseSpec,
    SecurityGuard,
)
from .lewm_gate6 import (
    Gate6KaggleConfig,
    prepare_gate6_kaggle_package,
    validate_gate6_artifacts,
    validate_gate6_kaggle_package,
)

GATE6_TRAIN_DATASET = "tempglitch_train_zero_action.lance"
GATE6_VALIDATION_DATASET = "tempglitch_validation_zero_action.lance"
GATE6_BUGGY_PROBE_DATASET = "tempglitch_nonlocked_buggy_encoding.lance"

GATE6_AUTOMATION_STEPS = (
    "preflight",
    "package_prepare",
    "package_validate",
    "dataset_fingerprint",
    "dataset_create_or_version",
    "dataset_ready",
    "kernel_package_generate",
    "kernel_validate_package",
    "kernel_push_once",
    "kernel_poll",
    "artifact_download",
    "artifact_validate",
    "complete",
)
GATE6_LIVE_ACTION_FINGERPRINTS = {
    "dataset_create_or_version": "dataset_fingerprint",
    "kernel_push_once": "kernel_fingerprint",
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class Gate6AutomationConfig:
    repo_root: Path
    source_root: Path
    run_root: Path
    dataset_slug: str
    kernel_slug: str
    dataset_visibility: str = "public"
    kernel_visibility: str = "public"
    dataset_license: str = "MIT"
    redistribution_allowed: bool = True
    accelerator: str = "NvidiaTeslaT4"
    poll_interval_seconds: int = 60
    poll_timeout_seconds: int = 6 * 60 * 60
    max_attempts: int = 3
    live: bool = False
    python_executable: Path = Path(sys.executable)

    @property
    def package_root(self) -> Path:
        return self.run_root / "package"

    @property
    def downloaded_root(self) -> Path:
        return self.run_root / "downloaded"


class Gate6AutomationHandlers:
    def __init__(
        self,
        config: Gate6AutomationConfig,
        *,
        command_runner: CommandRunner | None = None,
        security_guard: SecurityGuard | None = None,
        policy: KaggleExecutionPolicy | None = None,
    ) -> None:
        self.config = config
        self.security_guard = security_guard or SecurityGuard()
        self.policy = policy or KaggleExecutionPolicy()
        self.command_runner = command_runner or CommandRunner(
            security_guard=self.security_guard,
            max_attempts=config.max_attempts,
        )
        self.fingerprints = FingerprintBuilder()
        self.logs_root = config.run_root / "logs"

    def _log(self, step: str) -> Path:
        return self.logs_root / f"{step}.log"

    def _run(self, step: str, command: list[str]) -> Any:
        return self.command_runner.run(step, command, self._log(step))

    def _kaggle(self, *args: str) -> list[str]:
        return [
            str(self.config.python_executable),
            "-c",
            "from kaggle.cli import main; main()",
            *args,
        ]

    def _git_value(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.config.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()

    def _gate6_config(self) -> Gate6KaggleConfig:
        return Gate6KaggleConfig(
            dataset_slug=self.config.dataset_slug,
            kernel_slug=self.config.kernel_slug,
            dataset_id="tempglitch-lewm-gate6-v7",
            train_dataset_name=GATE6_TRAIN_DATASET,
            validation_dataset_name=GATE6_VALIDATION_DATASET,
            buggy_probe_dataset_name=GATE6_BUGGY_PROBE_DATASET,
            package_version="v7",
            accelerator=self.config.accelerator,
            dataset_visibility=self.config.dataset_visibility,
            kernel_visibility=self.config.kernel_visibility,
            dataset_license=self.config.dataset_license,
            redistribution_allowed=self.config.redistribution_allowed,
        )

    @staticmethod
    def _status(text: str) -> str:
        lowered = text.lower()
        if "not found" in lowered or "404" in lowered:
            return "missing"
        if "error" in lowered or "failed" in lowered:
            return "error"
        if "complete" in lowered or "success" in lowered:
            return "success"
        if "running" in lowered or "queued" in lowered:
            return "running"
        if lowered.strip() == "ready":
            return "ready"
        return "unknown"

    def _download_output(self, step: str) -> None:
        self.config.downloaded_root.mkdir(parents=True, exist_ok=True)
        self._run(
            step,
            self._kaggle(
                "kernels",
                "output",
                self.config.kernel_slug,
                "-p",
                str(self.config.downloaded_root),
                "-o",
            ),
        )

    def _package_validation(self) -> dict[str, Any]:
        validation = validate_gate6_kaggle_package(self.config.package_root)
        if validation["dataset_slug"] != self.config.dataset_slug:
            raise ValueError("Gate 6 package dataset slug does not match automation config.")
        if validation["kernel_slug"] != self.config.kernel_slug:
            raise ValueError("Gate 6 package kernel slug does not match automation config.")
        return validation

    def preflight(self, _state: AutomationState) -> dict[str, Any]:
        required = [
            self.config.source_root / GATE6_TRAIN_DATASET,
            self.config.source_root / GATE6_VALIDATION_DATASET,
            self.config.source_root / GATE6_BUGGY_PROBE_DATASET,
            self.config.repo_root / "src" / "glitch_detection" / "lewm_gate6.py",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Missing Gate 6 prerequisite(s): {', '.join(missing)}")
        if self.config.live:
            try:
                importlib.metadata.version("kaggle")
            except importlib.metadata.PackageNotFoundError:
                self._run(
                    "preflight",
                    [
                        str(self.config.python_executable),
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        "kaggle",
                    ],
                )
            try:
                self._run("preflight", self._kaggle("datasets", "list", "--mine"))
            except AutomationCommandError as exc:
                raise AutomationBlockedError(
                    "Kaggle authentication is unavailable; configure credentials outside the repo."
                ) from exc
        return {}

    def package_prepare(self, _state: AutomationState) -> dict[str, Any]:
        if self.config.package_root.exists():
            self._package_validation()
            return {}
        prepare_gate6_kaggle_package(
            self.config.source_root,
            self.config.package_root,
            self._gate6_config(),
            dry_run=False,
        )
        return {}

    def package_validate(self, _state: AutomationState) -> dict[str, Any]:
        validation = self._package_validation()
        dataset_release = self.security_guard.scan_public_release(
            self.config.package_root / "dataset",
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility=self.config.dataset_visibility,
                license_name=self.config.dataset_license,
                redistribution_allowed=self.config.redistribution_allowed,
            ),
        )
        kernel_release = self.security_guard.scan_public_release(
            self.config.package_root / "kernel",
            package_kind="kernel",
            spec=PublicReleaseSpec(
                visibility=self.config.kernel_visibility,
                license_name="repository-source",
                redistribution_allowed=True,
            ),
        )
        script = self.config.package_root / "kernel" / "lewm_gate6_kernel.py"
        bootstrap_root = self.config.run_root / "bootstrap_code"
        environment = dict(os.environ)
        environment["GATE6_BOOTSTRAP_ONLY"] = "1"
        environment["GATE6_CODE_ROOT"] = str(bootstrap_root.resolve())
        completed = subprocess.run(
            [str(self.config.python_executable), str(script.resolve())],
            cwd=self.config.run_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode or "GATE6_BOOTSTRAP_OK" not in completed.stdout:
            raise RuntimeError(
                "Gate 6 embedded bootstrap failed: "
                + self.security_guard.redact(completed.stderr or completed.stdout)
            )
        audit = {
            **validation,
            "dataset_release": dataset_release,
            "kernel_release": kernel_release,
            "git_commit_sha": self._git_value("rev-parse", "HEAD"),
            "branch": self._git_value("branch", "--show-current"),
            "dataset_visibility": self.config.dataset_visibility,
            "kernel_visibility": self.config.kernel_visibility,
            "dataset_license": self.config.dataset_license,
            "redistribution_allowed": self.config.redistribution_allowed,
            "authorization": "standing",
            "locked_test_materialized": False,
            "locked_test_scored": False,
            "bootstrap_verified": True,
        }
        _write_json(self.config.run_root / "audit" / "preflight.json", audit)
        return {}

    def dataset_fingerprint(self, _state: AutomationState) -> dict[str, Any]:
        fingerprint = self.fingerprints.inventory_sha256(self.config.package_root / "dataset")
        _write_json(
            self.config.run_root / "dataset_fingerprint.json",
            {"dataset_inventory_sha256": fingerprint},
        )
        return {"dataset_fingerprint": fingerprint}

    def refresh_dataset_fingerprint(self, state: AutomationState) -> dict[str, Any]:
        dataset_root = self.config.package_root / "dataset"
        if not state.dataset_fingerprint or not dataset_root.is_dir():
            return {}
        return {"dataset_fingerprint": self.fingerprints.inventory_sha256(dataset_root)}

    def dataset_create_or_version(self, state: AutomationState) -> dict[str, Any]:
        fingerprint = state.dataset_fingerprint or ""
        self.policy.authorize(
            KaggleAction(
                action="dataset_create_or_version",
                fingerprint=fingerprint,
                visibility=self.config.dataset_visibility,
                locked_test_materialized=False,
                locked_test_scored=False,
                redistribution_allowed=self.config.redistribution_allowed,
            )
        )
        if state.dataset_uploaded_fingerprint == fingerprint:
            return {}
        status = "missing"
        try:
            result = self._run(
                "dataset_create_or_version",
                self._kaggle("datasets", "status", self.config.dataset_slug),
            )
            status = self._status(result.stdout)
        except AutomationCommandError as exc:
            details = "\n".join([str(exc), exc.stdout, exc.stderr])
            if self._status(details) != "missing":
                raise
        if status == "missing":
            command = self._kaggle(
                "datasets",
                "create",
                "-p",
                str(self.config.package_root / "dataset"),
                "-r",
                "zip",
            )
            if self.config.dataset_visibility == "public":
                command.append("--public")
        else:
            command = self._kaggle(
                "datasets",
                "version",
                "-p",
                str(self.config.package_root / "dataset"),
                "-m",
                f"Gate 6 package {fingerprint[:12]}",
                "-r",
                "zip",
            )
        self._run("dataset_create_or_version", command)
        return {
            "dataset_uploaded_fingerprint": fingerprint,
            "dataset_uploaded_inventory_sha256": fingerprint,
        }

    def dataset_ready(self, _state: AutomationState) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.poll_timeout_seconds
        while time.monotonic() < deadline:
            result = self._run(
                "dataset_ready",
                self._kaggle("datasets", "status", self.config.dataset_slug),
            )
            if self._status(result.stdout) == "ready":
                return {}
            time.sleep(self.config.poll_interval_seconds)
        raise AutomationBlockedError("Gate 6 dataset readiness polling timed out.")

    def kernel_package_generate(self, state: AutomationState) -> dict[str, Any]:
        validation = self._package_validation()
        payload = {
            "dataset_fingerprint": state.dataset_fingerprint,
            "kernel_inventory_sha256": validation["kernel_inventory_sha256"],
            "kernel_code_sha256": validation["kernel_code_sha256"],
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        _write_json(
            self.config.run_root / "kernel_fingerprint.json",
            {**payload, "combined_sha256": fingerprint},
        )
        return {"kernel_fingerprint": fingerprint}

    def refresh_kernel_fingerprint(self, state: AutomationState) -> dict[str, Any]:
        kernel_root = self.config.package_root / "kernel"
        if not state.kernel_fingerprint or not kernel_root.is_dir():
            return {}
        payload = {
            "dataset_fingerprint": state.dataset_fingerprint,
            "kernel_inventory_sha256": self.fingerprints.inventory_sha256(kernel_root),
            "kernel_code_sha256": self.fingerprints.sha256_file(
                kernel_root / "lewm_gate6_kernel.py"
            ),
        }
        return {
            "kernel_fingerprint": hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        }

    def kernel_validate_package(self, _state: AutomationState) -> dict[str, Any]:
        self._package_validation()
        metadata = json.loads(
            (self.config.package_root / "kernel" / "kernel-metadata.json").read_text(
                encoding="utf-8-sig"
            )
        )
        if metadata.get("is_private") is (self.config.kernel_visibility == "public"):
            raise ValueError("Gate 6 kernel visibility does not match automation config.")
        return {}

    def kernel_push_once(self, state: AutomationState) -> dict[str, Any]:
        self.policy.authorize(
            KaggleAction(
                action="kernel_push",
                fingerprint=state.kernel_fingerprint or "",
                visibility=self.config.kernel_visibility,
                locked_test_materialized=False,
                locked_test_scored=False,
                redistribution_allowed=True,
            )
        )
        command = self._kaggle(
            "kernels",
            "push",
            "-p",
            str(self.config.package_root / "kernel"),
            "--accelerator",
            self.config.accelerator,
        )
        try:
            self._run("kernel_push_once", command)
        except AutomationCommandError:
            try:
                result = self._run(
                    "kernel_push_reconcile",
                    self._kaggle("kernels", "status", self.config.kernel_slug),
                )
            except AutomationCommandError:
                raise
            status = self._status(result.stdout)
            if status in {"running", "success", "error"}:
                return {"kernel_status": status}
            raise
        return {"kernel_status": "running"}

    def kernel_poll(self, _state: AutomationState) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.poll_timeout_seconds
        while time.monotonic() < deadline:
            result = self._run(
                "kernel_poll",
                self._kaggle("kernels", "status", self.config.kernel_slug),
            )
            status = self._status(result.stdout)
            if status == "success":
                return {"kernel_status": "success"}
            if status == "error":
                self._download_output("kernel_error_download")
                raise AutomationBlockedError(
                    "Gate 6 runtime failed; downloaded evidence requires a changed "
                    "package fingerprint."
                )
            time.sleep(self.config.poll_interval_seconds)
        raise AutomationBlockedError("Gate 6 kernel polling exceeded its timeout.")

    def artifact_download(self, _state: AutomationState) -> dict[str, Any]:
        self._download_output("artifact_download")
        return {"artifact_paths": {"downloaded_root": str(self.config.downloaded_root)}}

    def _artifact_root(self) -> Path:
        if (self.config.downloaded_root / "run_config.json").is_file():
            return self.config.downloaded_root
        candidates = [path.parent for path in self.config.downloaded_root.rglob("run_config.json")]
        if len(candidates) != 1:
            raise ValueError(
                "Expected one Gate 6 artifact root under downloaded output, "
                f"found {len(candidates)}."
            )
        return candidates[0]

    def artifact_validate(self, _state: AutomationState) -> dict[str, Any]:
        artifact_root = self._artifact_root()
        summary = validate_gate6_artifacts(artifact_root)
        _write_json(self.config.run_root / "audit" / "artifact_validation.json", summary)
        return {
            "artifact_paths": {
                "downloaded_root": str(self.config.downloaded_root),
                "artifact_root": str(artifact_root),
                "validation_report": str(
                    self.config.run_root / "audit" / "artifact_validation.json"
                ),
            }
        }

    def complete(self, _state: AutomationState) -> dict[str, Any]:
        return {}

    def as_mapping(self) -> dict[str, Callable[[AutomationState], dict[str, Any]]]:
        names = [
            *GATE6_AUTOMATION_STEPS,
            "refresh_dataset_fingerprint",
            "refresh_kernel_fingerprint",
        ]
        return {name: getattr(self, name) for name in names}
