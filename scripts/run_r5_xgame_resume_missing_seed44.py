"""Resume/finalize an R5-XGame run from a mounted partial output tree."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_SEEDS = (42, 43, 44)
MISSING_SEED = 44
REQUIRED_STAGE_MARKERS = (
    "stage_preflight.json",
    "stage_materialize.json",
    "stage_baseline_score.json",
    "stage_train_lewm.json",
)


def _runner():
    path = ROOT / "scripts" / "run_r5_xgame_staged.py"
    spec = importlib.util.spec_from_file_location("r5_xgame_runner_resume", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _csv_data_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def find_partial_output_dir(input_root: Path) -> Path:
    candidates = sorted(
        path
        for path in input_root.rglob("r5_xgame")
        if path.is_dir() and str(path).startswith(str(input_root))
    )
    if not candidates:
        raise FileNotFoundError(
            f"Missing mounted partial R5-XGame directory under {input_root}: expected */r5_xgame"
        )
    verified = [path for path in candidates if (path / "stage_train_lewm.json").is_file()]
    if len(verified) == 1:
        return verified[0]
    if len(verified) > 1:
        raise ValueError(f"Multiple mounted partial r5_xgame directories found: {verified}")
    if len(candidates) == 1:
        return candidates[0]
    raise ValueError(f"Multiple mounted r5_xgame directories found: {candidates}")


def copy_partial_output_dir(partial_dir: Path, output_dir: Path) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(partial_dir, output_dir)
    return output_dir


def _require_false_flag(payload: dict[str, Any], *, field: str, context: str) -> None:
    if payload.get(field) is not False:
        raise ValueError(f"Unsafe {context} flag: {field}")


def validate_partial_output_for_resume(output_dir: Path) -> dict[str, Any]:
    runner = _runner()
    for marker_name in REQUIRED_STAGE_MARKERS:
        marker_path = output_dir / marker_name
        if not marker_path.is_file():
            raise FileNotFoundError(f"Missing required stage marker for resume: {marker_path}")
        marker = _read_json(marker_path)
        context = marker_name.removeprefix("stage_").removesuffix(".json")
        for field in (
            "validation_buggy_used_for_fit_select",
            "locked_test_materialized",
            "locked_test_scored",
        ):
            _require_false_flag(marker, field=field, context=context)
    train_stage = _read_json(output_dir / "stage_train_lewm.json")
    if train_stage.get("status") != "train_lewm_complete":
        raise ValueError("stage_train_lewm.json must have status train_lewm_complete.")

    required_files = (
        "r5_xgame_window_manifest.csv",
        "r5_xgame_baseline_scores.csv",
        "r5_xgame_lewm_scores_seed42.csv",
        "r5_xgame_lewm_scores_seed43.csv",
    )
    for name in required_files:
        path = output_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing partial R5-XGame file: {path}")

    for seed in SUPPORTED_SEEDS:
        seed_dir = output_dir / f"_lewm_seed{seed}"
        if not seed_dir.is_dir():
            raise FileNotFoundError(f"Missing partial R5-XGame seed artifact root: {seed_dir}")
    for name in ("best_weights.pt", "config.json"):
        path = output_dir / f"_lewm_seed{MISSING_SEED}" / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing seed44 resume artifact: {path}")

    window_manifest = output_dir / "r5_xgame_window_manifest.csv"
    window_rows = _csv_data_row_count(window_manifest)
    for seed in (42, 43):
        score_path = output_dir / f"r5_xgame_lewm_scores_seed{seed}.csv"
        score_rows = _csv_data_row_count(score_path)
        if score_rows != window_rows:
            raise ValueError(
                f"Incomplete seed{seed} score CSV: expected {window_rows} rows, found {score_rows}."
            )

    manifest_rows = runner.read_csv_rows(window_manifest)
    seed42 = runner.validate_existing_lewm_score_file(output_dir, manifest_rows, seed=42)
    seed43 = runner.validate_existing_lewm_score_file(output_dir, manifest_rows, seed=43)

    return {
        "status": "resume_partial_output_validated",
        "output_dir": str(output_dir),
        "window_row_count": window_rows,
        "seed42_row_count": seed42["row_count"],
        "seed43_row_count": seed43["row_count"],
        "missing_seed": MISSING_SEED,
    }


def finalize_from_complete_scores(
    *, output_dir: Path, manifest: Path, bootstrap_seed: int, n_bootstrap: int
) -> dict[str, Any]:
    runner = _runner()
    manifest_rows = runner.read_csv_rows(output_dir / runner.WINDOW_MANIFEST_NAME)
    for seed in SUPPORTED_SEEDS:
        runner.validate_existing_lewm_score_file(output_dir, manifest_rows, seed=seed)
    lewm_score_marker = output_dir / "stage_lewm_score.json"
    if not lewm_score_marker.is_file():
        raise FileNotFoundError(f"Missing stage marker required for finalize: {lewm_score_marker}")
    aggregate = runner.run_aggregate_episode(output_dir=output_dir, seeds=SUPPORTED_SEEDS)
    calibrate = runner.run_calibrate_thresholds(output_dir=output_dir)
    evaluate = runner.run_evaluate_binary(output_dir=output_dir)
    bootstrap = runner.run_bootstrap_ci(
        output_dir=output_dir,
        bootstrap_seed=bootstrap_seed,
        n_bootstrap=n_bootstrap,
    )
    package = runner.run_package(manifest=manifest, output_dir=output_dir)
    validate = runner.run_validate_package(output_dir=output_dir, frozen_manifest=manifest)
    return {
        "status": "resume_finalize_complete",
        "stages": {
            "aggregate_episode": aggregate["status"],
            "calibrate_thresholds": calibrate["status"],
            "evaluate_binary": evaluate["status"],
            "bootstrap_ci": bootstrap["status"],
            "package": package["status"],
            "validate_package": validate["status"],
        },
    }


def resume_missing_seed44_and_finalize(
    *,
    input_root: Path,
    output_dir: Path,
    manifest: Path,
    device: str,
    lewm_batch_size: int,
    bootstrap_seed: int,
    n_bootstrap: int,
) -> dict[str, Any]:
    partial_dir = find_partial_output_dir(input_root)
    copy_partial_output_dir(partial_dir, output_dir)
    partial = validate_partial_output_for_resume(output_dir)
    runner = _runner()
    lewm_score = runner.run_lewm_score(
        output_dir=output_dir,
        seeds=(MISSING_SEED,),
        device=device,
        batch_size=lewm_batch_size,
    )
    finalized = finalize_from_complete_scores(
        output_dir=output_dir,
        manifest=manifest,
        bootstrap_seed=bootstrap_seed,
        n_bootstrap=n_bootstrap,
    )
    return {
        "status": "resume_missing_seed44_complete",
        "partial_source_dir": str(partial_dir),
        "copied_output_dir": str(output_dir),
        "partial_validation": partial,
        "lewm_score": lewm_score["status"],
        "finalize": finalized,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resume a mounted partial R5-XGame output and finalize downstream stages."
    )
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--output-dir", type=Path, default=Path("/kaggle/working/r5_xgame"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("configs/wob_protocol/r5_xgame_split.csv")
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--lewm-batch-size", type=int, default=2)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = resume_missing_seed44_and_finalize(
        input_root=args.input_root,
        output_dir=args.output_dir,
        manifest=args.manifest,
        device=args.device,
        lewm_batch_size=args.lewm_batch_size,
        bootstrap_seed=args.bootstrap_seed,
        n_bootstrap=args.n_bootstrap,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
