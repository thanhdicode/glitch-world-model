from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from glitch_detection.kaggle_automation import FingerprintBuilder  # noqa: E402
from glitch_detection.lewm_adapter import sha256_file  # noqa: E402
from glitch_detection.r5_xgame_protocol import (  # noqa: E402
    BUGGY_EVAL_ROLE,
    CALIBRATION_ROLE,
    NORMAL_EVAL_ROLE,
    TRAIN_ROLE,
    validate_r5_xgame_manifest,
)

R5_XGAME_MANIFEST = REPO_ROOT / "configs" / "wob_protocol" / "r5_xgame_split.csv"
R5_XGAME_OUTPUT_DIR = REPO_ROOT / "outputs" / "r5_xgame"
K3_OUTPUT_DIR = REPO_ROOT / "outputs" / "k3_ablation_inputs"
K3_MANIFEST_PATH = K3_OUTPUT_DIR / "k3_input_manifest.json"
K3_REPORT_PATH = K3_OUTPUT_DIR / "K3_INPUTS_REPORT.md"
EXPECTED_ROLE_COUNTS = {
    TRAIN_ROLE: 36,
    CALIBRATION_ROLE: 12,
    NORMAL_EVAL_ROLE: 12,
    BUGGY_EVAL_ROLE: 60,
}
REQUIRED_K3_FILES = {
    "train": "_r5_xgame_train_normal.lance",
    "validation": "_r5_xgame_calibration_eval_normal.lance",
    "buggy_eval": "_r5_xgame_eval_buggy.lance",
    "frozen_manifest": "r5_xgame_manifest.csv",
    "window_manifest": "r5_xgame_window_manifest.csv",
}
SAFE_FALSE_FIELDS = (
    "validation_buggy_used_for_fit_select",
    "locked_test_materialized",
    "locked_test_scored",
)


def _load_script_module(stem: str) -> Any:
    module_path = REPO_ROOT / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(f"_k3_{stem}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load helper module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_sha256(path: Path) -> Path:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(sha256_file(path) + "\n", encoding="utf-8")
    return sidecar


def _read_manifest_rows() -> list[dict[str, str]]:
    runner = _load_script_module("run_r5_xgame_staged")
    rows = runner._normalize_rows(runner._read_manifest(R5_XGAME_MANIFEST))
    counts = validate_r5_xgame_manifest(rows)
    if counts != EXPECTED_ROLE_COUNTS:
        raise ValueError(
            f"R5-XGame role counts changed: expected {EXPECTED_ROLE_COUNTS}, found {counts}."
        )
    return rows


def _require_safe_false(payload: dict[str, Any], *, context: str) -> None:
    for field in SAFE_FALSE_FIELDS:
        if payload.get(field) is not False:
            raise ValueError(f"Unsafe {context} flag: {field}")


def _resolve_stage_file(files: dict[str, Any], name: str) -> Path:
    recorded_path = Path(files[name]["path"])
    if recorded_path.exists():
        return recorded_path
    relocated_path = R5_XGAME_OUTPUT_DIR / name
    if relocated_path.exists():
        return relocated_path
    raise FileNotFoundError(
        f"R5-XGame stage marker points to a missing path: {recorded_path}; "
        f"relocated path also missing: {relocated_path}"
    )


def _candidate_roots() -> list[Path]:
    values = [
        os.environ.get("K3_INPUT_ROOT"),
        os.environ.get("R5_XGAME_INPUT_ROOT"),
        os.environ.get("WOB_INPUT_ROOT"),
        os.environ.get("NORMAL_INPUT_ROOT"),
        os.environ.get("TEST_INPUT_ROOT"),
        str(REPO_ROOT),
        str(REPO_ROOT / "data"),
        str(REPO_ROOT / "artifacts"),
        str(Path.home() / "Downloads"),
    ]
    roots: list[Path] = []
    seen: set[Path] = set()
    for value in values:
        if not value:
            continue
        candidate = Path(value).resolve()
        if candidate in seen or not candidate.exists() or not candidate.is_dir():
            continue
        roots.append(candidate)
        seen.add(candidate)
    return roots


def _existing_materialized_state() -> dict[str, Any] | None:
    stage_path = R5_XGAME_OUTPUT_DIR / "stage_materialize.json"
    if stage_path.is_file():
        stage = _read_json(stage_path)
        _require_safe_false(stage, context="stage_materialize")
        files = stage.get("files", {})
        try:
            train_path = _resolve_stage_file(files, REQUIRED_K3_FILES["train"])
            validation_path = _resolve_stage_file(files, REQUIRED_K3_FILES["validation"])
            buggy_path = _resolve_stage_file(files, REQUIRED_K3_FILES["buggy_eval"])
        except KeyError as exc:
            raise ValueError(
                f"stage_materialize.json is missing a required file record: {exc}"
            ) from exc
        frozen_manifest = _resolve_stage_file(files, REQUIRED_K3_FILES["frozen_manifest"])
        return {
            "mode": "existing_materialized",
            "train_path": train_path,
            "validation_path": validation_path,
            "buggy_eval_path": buggy_path,
            "frozen_manifest_path": frozen_manifest,
            "window_manifest_path": _resolve_stage_file(
                files, REQUIRED_K3_FILES["window_manifest"]
            ),
            "dataset_hashes": {
                "train": FingerprintBuilder.inventory_sha256(train_path),
                "validation": FingerprintBuilder.inventory_sha256(validation_path),
                "buggy_eval": FingerprintBuilder.inventory_sha256(buggy_path),
            },
        }

    direct_train = R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["train"]
    direct_validation = R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["validation"]
    direct_buggy = R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["buggy_eval"]
    direct_manifest = R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["frozen_manifest"]
    if all(
        path.exists() for path in (direct_train, direct_validation, direct_buggy, direct_manifest)
    ):
        return {
            "mode": "existing_unmarked",
            "train_path": direct_train,
            "validation_path": direct_validation,
            "buggy_eval_path": direct_buggy,
            "frozen_manifest_path": direct_manifest,
            "window_manifest_path": R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["window_manifest"],
            "dataset_hashes": {
                "train": FingerprintBuilder.inventory_sha256(direct_train),
                "validation": FingerprintBuilder.inventory_sha256(direct_validation),
                "buggy_eval": FingerprintBuilder.inventory_sha256(direct_buggy),
            },
        }
    return None


def _materialize_from_raw(
    rows: list[dict[str, str]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    del rows  # validated by _read_manifest_rows; kept for explicit contract continuity
    runner = _load_script_module("run_r5_xgame_staged")
    probes: list[dict[str, Any]] = []
    selected_root: Path | None = None
    selected_preflight: dict[str, Any] | None = None
    for index, candidate in enumerate(_candidate_roots()):
        probe_output = K3_OUTPUT_DIR / "_preflight_probes" / f"probe_{index:02d}"
        try:
            result = runner.preflight(R5_XGAME_MANIFEST, candidate, probe_output, [42, 43, 44])
            probe = {
                "candidate_root": str(candidate),
                "status": str(result["status"]),
                "coverage_by_role": result.get("coverage_by_role", {}),
                "missing_by_role": result.get("missing_by_role", {}),
            }
        except Exception as exc:
            probe = {
                "candidate_root": str(candidate),
                "status": "preflight_error",
                "coverage_by_role": {},
                "missing_by_role": {},
                "error": str(exc),
            }
            probes.append(probe)
            continue
        probes.append(probe)
        if result["status"] == "preflight_complete" and selected_root is None:
            selected_root = candidate
            selected_preflight = result

    if selected_root is None or selected_preflight is None:
        return None, probes

    runner.preflight(R5_XGAME_MANIFEST, selected_root, R5_XGAME_OUTPUT_DIR, [42, 43, 44])
    materialize = runner.run_materialize(manifest=R5_XGAME_MANIFEST, output_dir=R5_XGAME_OUTPUT_DIR)
    _require_safe_false(materialize, context="materialize")
    files = materialize["files"]
    return (
        {
            "mode": "materialized_from_raw",
            "candidate_root": str(selected_root),
            "preflight": selected_preflight,
            "train_path": Path(files[REQUIRED_K3_FILES["train"]]["path"]),
            "validation_path": Path(files[REQUIRED_K3_FILES["validation"]]["path"]),
            "buggy_eval_path": Path(files[REQUIRED_K3_FILES["buggy_eval"]]["path"]),
            "frozen_manifest_path": Path(files[REQUIRED_K3_FILES["frozen_manifest"]]["path"]),
            "window_manifest_path": Path(files[REQUIRED_K3_FILES["window_manifest"]]["path"]),
            "dataset_hashes": {
                "train": str(materialize["files"][REQUIRED_K3_FILES["train"]]["sha256"]),
                "validation": str(materialize["files"][REQUIRED_K3_FILES["validation"]]["sha256"]),
                "buggy_eval": str(materialize["files"][REQUIRED_K3_FILES["buggy_eval"]]["sha256"]),
            },
        },
        probes,
    )


def _manifest_payload_for_missing(
    rows: list[dict[str, str]], probes: list[dict[str, Any]]
) -> dict[str, Any]:
    missing_contract: list[dict[str, Any]] = []
    for probe in probes:
        if probe["status"] == "preflight_complete":
            continue
        per_role_missing = []
        for role in (TRAIN_ROLE, CALIBRATION_ROLE, NORMAL_EVAL_ROLE, BUGGY_EVAL_ROLE):
            values = list(probe["missing_by_role"].get(role, []))
            per_role_missing.append(
                {
                    "role": role,
                    "missing_count": len(values),
                    "missing_paths": values,
                }
            )
        missing_contract.append(
            {
                "candidate_root": probe["candidate_root"],
                "status": probe["status"],
                "error": probe.get("error"),
                "missing_by_role": per_role_missing,
            }
        )
    return {
        "status": "missing_required_inputs",
        "selected_support_source": "R5-XGame train_normal + calibration/eval_normal Lance",
        "source_protocol": "configs/wob_protocol/r5_xgame_split.csv",
        "role_counts": EXPECTED_ROLE_COUNTS,
        "expected_train_path": str(R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["train"]),
        "expected_validation_path": str(R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["validation"]),
        "expected_buggy_eval_path": str(R5_XGAME_OUTPUT_DIR / REQUIRED_K3_FILES["buggy_eval"]),
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "candidate_roots_checked": [probe["candidate_root"] for probe in probes],
        "missing_artifacts": missing_contract,
        "rerun_command": "python scripts/prepare_k3_ablation_inputs.py",
        "notes": [
            "K3 uses the R5-XGame lane selected by outputs/r6_sigreg_ablation_plan/r6_ablation_plan.json.",
            "The required local raw/source archives were not found under any checked candidate root.",
            "No fake Lance datasets were created.",
        ],
    }


def _manifest_payload_for_ready(
    rows: list[dict[str, str]], state: dict[str, Any], probes: list[dict[str, Any]]
) -> dict[str, Any]:
    validation_episode_count = (
        EXPECTED_ROLE_COUNTS[CALIBRATION_ROLE] + EXPECTED_ROLE_COUNTS[NORMAL_EVAL_ROLE]
    )
    return {
        "status": "prepared",
        "selected_support_source": "R5-XGame train_normal + calibration/eval_normal Lance",
        "source_protocol": "configs/wob_protocol/r5_xgame_split.csv",
        "materialization_mode": state["mode"],
        "candidate_root_used": state.get("candidate_root"),
        "candidate_roots_checked": [probe["candidate_root"] for probe in probes],
        "train_path": str(Path(state["train_path"]).resolve()),
        "validation_path": str(Path(state["validation_path"]).resolve()),
        "auxiliary_buggy_eval_path": str(Path(state["buggy_eval_path"]).resolve()),
        "frozen_manifest_path": str(Path(state["frozen_manifest_path"]).resolve()),
        "window_manifest_path": str(Path(state["window_manifest_path"]).resolve()),
        "dataset_hashes": state["dataset_hashes"],
        "role_counts": EXPECTED_ROLE_COUNTS,
        "train_episode_count": EXPECTED_ROLE_COUNTS[TRAIN_ROLE],
        "validation_episode_count": validation_episode_count,
        "validation_role_counts": {
            CALIBRATION_ROLE: EXPECTED_ROLE_COUNTS[CALIBRATION_ROLE],
            NORMAL_EVAL_ROLE: EXPECTED_ROLE_COUNTS[NORMAL_EVAL_ROLE],
        },
        "k3_training_inputs_only": True,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "rerun_command": "python scripts/prepare_k3_ablation_inputs.py",
        "notes": [
            "K3 currently consumes train_normal and calibration/eval_normal Lance inputs only.",
            "The buggy-positive R5-XGame Lance remains recorded for provenance but is not passed to run_r6_sigreg_ablation.py.",
            "No SIGReg or action-conditioning scientific claim is supported until a downloaded K3 bundle validates locally.",
        ],
        "manifest_role_snapshot_sha256": sha256_file(R5_XGAME_MANIFEST),
        "validated_manifest_role_counts": validate_r5_xgame_manifest(rows),
    }


def _render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# K3 Input Preparation Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Selected support source: `{payload['selected_support_source']}`",
        f"- Source protocol: `{payload['source_protocol']}`",
        f"- Locked test materialized: `{str(payload['locked_test_materialized']).lower()}`",
        f"- Locked test scored: `{str(payload['locked_test_scored']).lower()}`",
        "",
        "## Role Counts",
        "",
        f"- train_normal: `{payload['role_counts'][TRAIN_ROLE]}`",
        f"- calibration_normal: `{payload['role_counts'][CALIBRATION_ROLE]}`",
        f"- evaluation_normal_negative: `{payload['role_counts'][NORMAL_EVAL_ROLE]}`",
        f"- evaluation_buggy_positive: `{payload['role_counts'][BUGGY_EVAL_ROLE]}`",
        "",
    ]
    if payload["status"] == "prepared":
        lines.extend(
            [
                "## Selected Inputs",
                "",
                f"- Train path: `{payload['train_path']}`",
                f"- Validation path: `{payload['validation_path']}`",
                f"- Auxiliary buggy-eval path: `{payload['auxiliary_buggy_eval_path']}`",
                f"- Train hash: `{payload['dataset_hashes']['train']}`",
                f"- Validation hash: `{payload['dataset_hashes']['validation']}`",
                f"- Buggy-eval hash: `{payload['dataset_hashes']['buggy_eval']}`",
                f"- Rerun command: `{payload['rerun_command']}`",
            ]
        )
    else:
        lines.extend(
            [
                "## Missing Artifacts",
                "",
                f"- Expected train path: `{payload['expected_train_path']}`",
                f"- Expected validation path: `{payload['expected_validation_path']}`",
                f"- Expected buggy-eval path: `{payload['expected_buggy_eval_path']}`",
                "",
            ]
        )
        for contract in payload["missing_artifacts"]:
            lines.append(f"### Candidate Root `{contract['candidate_root']}`")
            lines.append("")
            lines.append(f"- Probe status: `{contract['status']}`")
            if contract.get("error"):
                lines.append(f"- Error: `{contract['error']}`")
            for row in contract["missing_by_role"]:
                lines.append(f"- {row['role']}: missing `{row['missing_count']}` archive(s)")
            lines.append("")
        lines.append(f"- Rerun command: `{payload['rerun_command']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    rows = _read_manifest_rows()
    K3_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    probes: list[dict[str, Any]] = []
    state = _existing_materialized_state()
    if state is None:
        state, probes = _materialize_from_raw(rows)
    else:
        probes = [
            {
                "candidate_root": str(R5_XGAME_OUTPUT_DIR),
                "status": "existing_materialized",
                "coverage_by_role": {},
                "missing_by_role": {},
            }
        ]

    if state is None:
        payload = _manifest_payload_for_missing(rows, probes)
        _write_json(K3_MANIFEST_PATH, payload)
        _write_sha256(K3_MANIFEST_PATH)
        K3_REPORT_PATH.write_text(_render_report(payload), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 1

    payload = _manifest_payload_for_ready(rows, state, probes)
    _write_json(K3_MANIFEST_PATH, payload)
    _write_sha256(K3_MANIFEST_PATH)
    K3_REPORT_PATH.write_text(_render_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
