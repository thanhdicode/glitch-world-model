"""Freeze the seed42 non-locked World of Bugs evaluation-readiness bundle.

This is a metadata-only, local CPU gate. It derives a frozen WOB evaluation manifest from the
tracked protocol split (`configs/wob_protocol/split.csv`) and writes a readiness record that pins
the evaluation manifest, calibration/evaluation role split, recorded artifact hashes, the seed42
selected-checkpoint expectations, the frozen reporting paths, and the claim boundary. It does not
run any evaluation, does not touch the locked test, and does not require the GPU artifact tarball
or a Kaggle run.

Locked rows are identified by ``split == "test"`` only. The buggy validation rows legitimately
carry ``source`` paths under ``TEST/`` in the upstream dataset layout; they remain non-locked
because their ``split`` is ``validation``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SPLIT_CSV = Path("configs/wob_protocol/split.csv")
DEFAULT_EVAL_MANIFEST = Path("configs/wob_protocol/wob_expansion_eval_manifest.csv")
DEFAULT_READINESS_JSON = Path("configs/wob_protocol/wob_expansion_readiness.json")

# Recorded, verified upstream artifact hashes (see C-070, C-071 in the claim registry).
WOB_P0_KAGGLE_AUDIT_SHA256 = "e08e683ecdf59662092116495fbb4f10ab74225c5414ae7acf1d456bd5d492b9"
WOB_P1_SEED42_ARTIFACT_SHA256 = "54bb2b606233e35ca2f23607d0bf07d8101c040080c15154dacb7c9cd4c62f03"

# Frozen non-locked protocol counts derived from configs/wob_protocol/split.csv.
EXPECTED_CALIBRATION_NORMAL = 6
EXPECTED_EVALUATION_NORMAL = 6
EXPECTED_EVALUATION_BUGGY = 60
EXPECTED_VALIDATION_TOTAL = (
    EXPECTED_CALIBRATION_NORMAL + EXPECTED_EVALUATION_NORMAL + EXPECTED_EVALUATION_BUGGY
)
EXPECTED_LOCKED_EXCLUDED = 59
EXPECTED_TRAIN_EXCLUDED = 48

CALIBRATION_ROLE = "calibration_normal"
EVALUATION_NORMAL_ROLE = "evaluation_normal"
EVALUATION_BUGGY_ROLE = "evaluation_buggy"

# seed42 WOB-P1 selected-checkpoint expectations (mirror validate_wob_seed42_artifacts.py).
SEED42_CHECKPOINT = {
    "seed": 42,
    "selection_split": "validation_normal",
    "action_dim": 4,
    "target_optimizer_updates": 15000,
    "best_update": 1500,
    "best_validation_loss": 0.6093359693480057,
}

# Frozen reporting / output paths for the future R5-WOB non-locked evaluation.
REPORTING = {
    "results_doc": "docs/research/78_r5_wob_identical_episode_results.md",
    "output_dir": "outputs/r5_wob_identical_episode",
    "manifest_output": "outputs/r5_wob_identical_episode/r5_wob_manifest.csv",
    "episode_scores_output": "outputs/r5_wob_identical_episode/r5_wob_episode_scores.csv",
    "metrics_output": "outputs/r5_wob_identical_episode/r5_wob_metrics.json",
    "provenance_output": "outputs/r5_wob_identical_episode/r5_wob_provenance.json",
}

METHODS_PLANNED = [
    "lewm seed42",
    "lewm seed43",
    "lewm seed44",
    "frame_diff",
    "feature_distance (train-normal-fitted)",
]

CLAIM_BOUNDARY = (
    "The WOB evaluation-readiness gate freezes the seed42 non-locked WOB evaluation manifest, "
    "role split, recorded artifact hashes, reporting paths, and claim boundary as metadata only. "
    "It runs no WOB evaluation and supports no WOB detection-performance, cross-game "
    "generalization, action-conditioning-benefit, SIGReg-benefit, superiority, or locked-test "
    "claim. WOB result claims may only be made after the R5-WOB evaluation artifacts exist."
)

FORBIDDEN_CLAIMS = [
    "WOB detection performance or AUROC/AUPRC/F1 before R5-WOB evaluation artifacts exist",
    "cross-game generalization before R5-XGAME exists",
    "action-conditioning benefit before the WOB real-action vs zero-action ablation exists",
    "SIGReg benefit before the R6 SIGReg ablation exists",
    "any locked-test result or locked-test materialization/scoring",
]

EVAL_MANIFEST_FIELDS = (
    "dataset_id",
    "source",
    "episode_id",
    "pair_id",
    "category",
    "label",
    "split",
    "action_mode",
    "use_for_training",
    "materialize",
    "evaluation_role",
)


def _read_split_rows(split_csv: Path) -> list[dict[str, str]]:
    with split_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_eval_manifest_rows(split_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Select the 72 non-locked validation rows and tag each with its evaluation role.

    Locked rows (``split == "test"``) and train rows (``split == "train"``) are excluded. The
    upstream ``source`` directory naming (``TEST/...``) is never used to decide locked status.
    """

    normal_rows = [
        row
        for row in split_rows
        if row.get("split") == "validation" and row.get("label") == "Normal"
    ]
    calibration_episode_ids = {
        row["episode_id"] for row in normal_rows[:EXPECTED_CALIBRATION_NORMAL]
    }
    rows: list[dict[str, str]] = []
    for row in split_rows:
        if row.get("split") != "validation":
            continue
        label = row.get("label", "")
        if label == "Normal":
            role = (
                CALIBRATION_ROLE
                if row.get("episode_id", "") in calibration_episode_ids
                else EVALUATION_NORMAL_ROLE
            )
        else:
            role = EVALUATION_BUGGY_ROLE
        rows.append(
            {
                **{key: row.get(key, "") for key in EVAL_MANIFEST_FIELDS[:-1]},
                "evaluation_role": role,
            }
        )
    return rows


def render_eval_manifest_csv(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(EVAL_MANIFEST_FIELDS), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in EVAL_MANIFEST_FIELDS})
    return buffer.getvalue()


def build_readiness(
    split_rows: list[dict[str, str]],
    eval_manifest_csv: str,
    *,
    split_csv_rel: str,
    eval_manifest_rel: str,
) -> dict[str, Any]:
    manifest_rows = build_eval_manifest_rows(split_rows)
    calibration = [r for r in manifest_rows if r["evaluation_role"] == CALIBRATION_ROLE]
    evaluation_normal = [r for r in manifest_rows if r["evaluation_role"] == EVALUATION_NORMAL_ROLE]
    evaluation_buggy = [r for r in manifest_rows if r["evaluation_role"] == EVALUATION_BUGGY_ROLE]
    locked_excluded = [r for r in split_rows if r.get("split") == "test"]
    train_excluded = [r for r in split_rows if r.get("split") == "train"]

    split_csv_text = render_split_source(split_rows)

    return {
        "phase": "wob_expansion_readiness",
        "seed": SEED42_CHECKPOINT["seed"],
        "status": "frozen",
        "source_split_csv": split_csv_rel,
        "source_split_sha256": _sha256_bytes(split_csv_text.encode("utf-8")),
        "eval_manifest_path": eval_manifest_rel,
        "eval_manifest_sha256": _sha256_bytes(eval_manifest_csv.encode("utf-8")),
        "eval_manifest_row_count": len(manifest_rows),
        "calibration": {
            "evaluation_role": CALIBRATION_ROLE,
            "label": "Normal",
            "count": len(calibration),
        },
        "evaluation_normal": {
            "evaluation_role": EVALUATION_NORMAL_ROLE,
            "label": "Normal",
            "count": len(evaluation_normal),
        },
        "evaluation_buggy": {
            "evaluation_role": EVALUATION_BUGGY_ROLE,
            "label": "Buggy",
            "count": len(evaluation_buggy),
        },
        "locked_rows_excluded": len(locked_excluded),
        "train_rows_excluded": len(train_excluded),
        "recorded_artifact_hashes": {
            "wob_p0_kaggle_audit_sha256": WOB_P0_KAGGLE_AUDIT_SHA256,
            "wob_p1_seed42_artifact_sha256": WOB_P1_SEED42_ARTIFACT_SHA256,
        },
        "seed42_selected_checkpoint": dict(SEED42_CHECKPOINT),
        "reporting": dict(REPORTING),
        "methods_planned": list(METHODS_PLANNED),
        "claim_boundary": CLAIM_BOUNDARY,
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
        "action_synchronization_verified": False,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "evaluation_run": False,
    }


def render_split_source(split_rows: list[dict[str, str]]) -> str:
    """Re-render the split rows deterministically for a stable provenance hash."""

    if not split_rows:
        return ""
    fieldnames = list(split_rows[0].keys())
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in split_rows:
        writer.writerow(row)
    return buffer.getvalue()


def prepare(
    *,
    repo_root: Path,
    split_csv: Path,
    eval_manifest: Path,
    readiness_json: Path,
    dry_run: bool,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    split_rows = _read_split_rows(split_csv)
    manifest_rows = build_eval_manifest_rows(split_rows)
    eval_manifest_csv = render_eval_manifest_csv(manifest_rows)

    split_csv_rel = split_csv.resolve().relative_to(repo_root).as_posix()
    eval_manifest_rel = eval_manifest.resolve().relative_to(repo_root).as_posix()
    readiness = build_readiness(
        split_rows,
        eval_manifest_csv,
        split_csv_rel=split_csv_rel,
        eval_manifest_rel=eval_manifest_rel,
    )

    if not dry_run:
        eval_manifest.parent.mkdir(parents=True, exist_ok=True)
        eval_manifest.write_text(eval_manifest_csv, encoding="utf-8", newline="")
        readiness_json.parent.mkdir(parents=True, exist_ok=True)
        readiness_json.write_text(
            json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    return {
        "status": "wob_expansion_readiness_prepared" if not dry_run else "dry_run",
        "eval_manifest_path": eval_manifest_rel,
        "eval_manifest_sha256": readiness["eval_manifest_sha256"],
        "eval_manifest_row_count": readiness["eval_manifest_row_count"],
        "calibration_count": readiness["calibration"]["count"],
        "evaluation_normal_count": readiness["evaluation_normal"]["count"],
        "evaluation_buggy_count": readiness["evaluation_buggy"]["count"],
        "locked_rows_excluded": readiness["locked_rows_excluded"],
        "train_rows_excluded": readiness["train_rows_excluded"],
        "readiness_json_path": readiness_json.resolve().relative_to(repo_root).as_posix(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze the seed42 non-locked WOB evaluation-readiness bundle."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--split-csv", type=Path, default=ROOT / DEFAULT_SPLIT_CSV)
    parser.add_argument("--eval-manifest", type=Path, default=ROOT / DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--readiness-json", type=Path, default=ROOT / DEFAULT_READINESS_JSON)
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = prepare(
        repo_root=args.repo_root.resolve(),
        split_csv=args.split_csv,
        eval_manifest=args.eval_manifest,
        readiness_json=args.readiness_json,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
