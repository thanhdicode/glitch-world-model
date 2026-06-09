from pathlib import Path

import pytest

from glitch_detection.kaggle_automation import (
    APPROVAL_STEPS,
    AutomationBlockedError,
    AutomationState,
    Phase6EKaggleOrchestrator,
    StateStore,
)


def _handlers(calls: list[str]):
    def handler(step: str):
        def run(_state: AutomationState):
            calls.append(step)
            if step == "dataset_fingerprint":
                return {"dataset_fingerprint": "dataset-fp"}
            if step == "kernel_package_generate":
                return {"kernel_fingerprint": "kernel-fp"}
            if step == "kernel_push_once":
                return {"kernel_status": "running"}
            return {}

        return run

    return {
        step: handler(step)
        for step in [
            "preflight",
            "auth_check_or_request_login",
            "repo_and_security_scan",
            "dataset_dry_run",
            "dataset_prepare",
            "dataset_validate_package",
            "dataset_fingerprint",
            "dataset_create_or_version",
            "kernel_package_generate",
            "kernel_validate_package",
            "kernel_push_once",
            "kernel_poll",
            "artifact_download",
            "artifact_validate",
            "artifact_ingest",
            "complete",
        ]
    }


def test_orchestrator_stops_for_fingerprint_bound_dataset_approval(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    )

    state = orchestrator.run()

    assert state.current_step == "dataset_upload_approval"
    assert state.requires_approval == "dataset_upload_approval"
    assert state.dataset_fingerprint == "dataset-fp"
    assert (tmp_path / "approvals" / "dataset_upload_approval.request.json").is_file()
    assert "dataset_create_or_version" not in calls


def test_dry_run_never_consumes_approval_or_runs_live_action(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=True,
    )
    state = AutomationState(
        current_step="dataset_create_or_version",
        completed_steps=[
            "preflight",
            "auth_check_or_request_login",
            "repo_and_security_scan",
            "dataset_dry_run",
            "dataset_prepare",
            "dataset_validate_package",
            "dataset_fingerprint",
            "dataset_upload_approval",
        ],
        dataset_fingerprint="dataset-fp",
    )
    orchestrator.state_store.save(state)
    orchestrator.approval_store.request("dataset_upload_approval", "dataset-fp")
    orchestrator.approval_store.approve("dataset_upload_approval", "dataset-fp")

    result = orchestrator.run()

    assert result.current_step == "dataset_create_or_version"
    assert result.blocked_reason == "dry-run: live action not executed"
    assert "dataset_create_or_version" not in calls
    assert orchestrator.approval_store.is_approved("dataset_upload_approval", "dataset-fp") is True


def test_live_action_consumes_approval_then_resumes_to_kernel_approval(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    )
    state = AutomationState(
        current_step="dataset_upload_approval",
        completed_steps=[
            "preflight",
            "auth_check_or_request_login",
            "repo_and_security_scan",
            "dataset_dry_run",
            "dataset_prepare",
            "dataset_validate_package",
            "dataset_fingerprint",
        ],
        dataset_fingerprint="dataset-fp",
    )
    orchestrator.state_store.save(state)
    orchestrator.approval_store.request("dataset_upload_approval", "dataset-fp")
    orchestrator.approval_store.approve("dataset_upload_approval", "dataset-fp")

    result = orchestrator.run()

    assert "dataset_create_or_version" in calls
    assert result.current_step == "kernel_push_approval"
    assert result.requires_approval == "kernel_push_approval"
    approved = orchestrator.approval_store._read_approved("dataset_upload_approval")
    assert approved["consumed_at"] is not None


def test_same_kernel_fingerprint_can_only_start_one_gpu_push(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    )
    state = AutomationState(
        current_step="kernel_push_once",
        completed_steps=[],
        kernel_fingerprint="kernel-fp",
        gpu_push_fingerprints=["kernel-fp"],
    )
    orchestrator.state_store.save(state)

    with pytest.raises(AutomationBlockedError, match="already used"):
        orchestrator.run()
    assert "kernel_push_once" not in calls


def test_approval_step_names_are_stable():
    assert APPROVAL_STEPS == {
        "dataset_upload_approval": ("dataset_fingerprint", "dataset_create_or_version"),
        "kernel_push_approval": ("kernel_fingerprint", "kernel_push_once"),
    }


def test_changed_fingerprint_invalidates_completed_approval(tmp_path: Path):
    calls: list[str] = []
    handlers = _handlers(calls)
    handlers["refresh_dataset_fingerprint"] = lambda _state: {
        "dataset_fingerprint": "dataset-fp-new"
    }
    orchestrator = Phase6EKaggleOrchestrator(root=tmp_path, handlers=handlers, dry_run=False)
    orchestrator.state_store.save(
        AutomationState(
            current_step="dataset_create_or_version",
            completed_steps=[
                "preflight",
                "auth_check_or_request_login",
                "repo_and_security_scan",
                "dataset_dry_run",
                "dataset_prepare",
                "dataset_validate_package",
                "dataset_fingerprint",
                "dataset_upload_approval",
            ],
            dataset_fingerprint="dataset-fp-old",
        )
    )

    result = orchestrator.run()

    assert result.current_step == "dataset_upload_approval"
    assert result.requires_approval == "dataset_upload_approval"
    assert result.dataset_fingerprint == "dataset-fp-new"
    assert "dataset_create_or_version" not in calls


def test_switching_from_dry_run_to_live_resets_before_real_dataset_prepare(tmp_path: Path):
    calls: list[str] = []
    state = AutomationState(
        current_step="dataset_upload_approval",
        completed_steps=[
            "preflight",
            "auth_check_or_request_login",
            "repo_and_security_scan",
            "dataset_dry_run",
            "dataset_prepare",
            "dataset_validate_package",
            "dataset_fingerprint",
        ],
        dataset_fingerprint="dry-fingerprint",
        execution_mode="dry-run",
    )
    StateStore(tmp_path / "state.json").save(state)
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    )

    result = orchestrator.run()

    assert "dataset_prepare" in calls
    assert result.execution_mode == "live"
    assert result.current_step == "dataset_upload_approval"
