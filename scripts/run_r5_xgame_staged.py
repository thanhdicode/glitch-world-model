"""Fail-closed staged entrypoint for the four-role R5-XGame protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from glitch_detection.r5_xgame_protocol import validate_r5_xgame_manifest

STAGES = (
    "preflight",
    "materialize",
    "baseline_score",
    "train_lewm",
    "lewm_score",
    "aggregate_episode",
    "calibrate_thresholds",
    "evaluate_binary",
    "bootstrap_ci",
    "package",
    "validate_package",
)
PLANNED_OUTPUTS = (
    "r5_xgame_manifest.csv",
    "r5_xgame_window_manifest.csv",
    "r5_xgame_baseline_scores.csv",
    "r5_xgame_lewm_scores_seed42.csv",
    "r5_xgame_lewm_scores_seed43.csv",
    "r5_xgame_lewm_scores_seed44.csv",
    "r5_xgame_episode_scores.csv",
    "r5_xgame_comparison.csv",
    "r5_xgame_metrics.json",
    "R5_XGAME_REPORT.md",
    "r5_xgame_provenance.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _role_hash(rows: list[dict[str, str]], role: str) -> str:
    values = sorted(row["source"] for row in rows if row["evaluation_role"] == role)
    return hashlib.sha256("\n".join(values).encode()).hexdigest()


def _find_source(input_root: Path, source: str) -> Path | None:
    if not input_root.is_dir():
        return None
    for candidate in input_root.rglob(Path(source).name):
        if candidate.is_file() and candidate.as_posix().endswith(source):
            return candidate
    return None


def preflight(
    manifest: Path, input_root: Path, output_dir: Path, seeds: list[int]
) -> dict[str, object]:
    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts = validate_r5_xgame_manifest(rows)
    resolved = {row["source"]: _find_source(input_root, row["source"]) for row in rows}
    missing_by_role: dict[str, list[str]] = {}
    for role in counts:
        missing_by_role[role] = [
            row["source"]
            for row in rows
            if row["evaluation_role"] == role and resolved[row["source"]] is None
        ]
    if any("r5_wob" in str(path).lower() for path in resolved.values() if path is not None):
        raise ValueError("R5-XGame refuses source/checkpoint paths containing r5_wob.")
    payload = {
        "stage": "preflight",
        "status": "preflight_complete"
        if not any(missing_by_role.values())
        else "preflight_missing_inputs",
        "manifest": str(manifest),
        "manifest_sha256": _sha256(manifest),
        "role_counts": counts,
        "role_hashes": {role: _role_hash(rows, role) for role in counts},
        "seeds": seeds,
        "input_root": str(input_root),
        "missing_by_role": missing_by_role,
        "old_r5_wob_checkpoint_reused": False,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage_preflight.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe R5-XGame stage.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/r5_xgame"))
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--stage", choices=(*STAGES, "all"), default="preflight")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--package", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if sorted(args.seeds) != [42, 43, 44]:
        raise ValueError("R5-XGame requires fresh seeds 42, 43, and 44.")
    receipt = preflight(args.manifest, args.input_root, args.output_dir, args.seeds)
    ready = receipt["status"] == "preflight_complete"
    if args.dry_run or args.smoke:
        print(
            json.dumps(
                {
                    **receipt,
                    "SAFE_TO_RUN_KAGGLE": ready and False,
                    "planned_outputs": PLANNED_OUTPUTS,
                },
                indent=2,
            )
        )
        return 0
    if not ready:
        raise ValueError("R5-XGame preflight failed: frozen source archives are missing.")
    if args.stage not in {"preflight", "all"}:
        raise NotImplementedError(
            "R5-XGame compute stages require the four-role materialize/train/score module; "
            "preflight completed without using old R5-WOB checkpoints."
        )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
