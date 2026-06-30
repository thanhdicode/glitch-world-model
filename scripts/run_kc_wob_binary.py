from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from glitch_detection.r5_wob_eval import (
    DEFAULT_EVAL_MANIFEST,
    DEFAULT_READINESS_JSON,
    DEFAULT_SPLIT_CSV,
)
from glitch_detection.r5_wob_staged import DEFAULT_INPUT_ROOT, STAGE_ORDER, run_stage

DEFAULT_OUTPUT_DIR = Path("/kaggle/working/kc_wob_binary")
DEFAULT_SUCCESS_TAR = Path("/kaggle/working/kc_wob_binary_outputs.tar.gz")


def run_kc_wob_binary(
    *,
    input_root: Path,
    readiness_json: Path,
    eval_manifest: Path,
    split_csv: Path,
    output_dir: Path,
    success_tarball: Path,
    baseline_batch_size: int,
    lewm_batch_size: int,
    device: str,
    bootstrap_seed: int,
    n_bootstrap: int,
    smoke: bool,
    force: bool,
) -> dict[str, Any]:
    """Run the full non-locked K-C/WOB binary evaluation stage sequence."""
    stages = list(STAGE_ORDER)
    if smoke:
        stages.remove("validate_package")

    stage_results: dict[str, Any] = {}
    for stage in stages:
        stage_results[stage] = run_stage(
            stage=stage,
            input_root=input_root,
            readiness_json=readiness_json,
            eval_manifest=eval_manifest,
            split_csv=split_csv,
            output_dir=output_dir,
            baseline_batch_size=baseline_batch_size,
            lewm_batch_size=lewm_batch_size,
            device=device,
            bootstrap_seed=bootstrap_seed,
            n_bootstrap=n_bootstrap,
            success_tarball=success_tarball,
            smoke=smoke,
            force=force,
        )

    return {
        "status": "kc_wob_binary_smoke_complete" if smoke else "kc_wob_binary_complete",
        "protocol": "wob_identical_episode_nonlocked",
        "paper_valid": not smoke,
        "output_dir": str(output_dir),
        "success_tarball": "" if smoke else str(success_tarball),
        "success_sha256": "" if smoke else f"{success_tarball}.sha256",
        "stages": list(stage_results),
        "stage_results": stage_results,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run K-C WOB binary evaluation using the validated staged R5-WOB pipeline."
    )
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS_JSON)
    parser.add_argument("--eval-manifest", type=Path, default=DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--split-csv", type=Path, default=DEFAULT_SPLIT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--success-tarball", type=Path, default=DEFAULT_SUCCESS_TAR)
    parser.add_argument("--baseline-batch-size", type=int, default=4)
    parser.add_argument("--lewm-batch-size", type=int, default=2)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_kc_wob_binary(
        input_root=args.input_root,
        readiness_json=args.readiness_json,
        eval_manifest=args.eval_manifest,
        split_csv=args.split_csv,
        output_dir=args.output_dir,
        success_tarball=args.success_tarball,
        baseline_batch_size=args.baseline_batch_size,
        lewm_batch_size=args.lewm_batch_size,
        device=args.device,
        bootstrap_seed=args.bootstrap_seed,
        n_bootstrap=args.n_bootstrap,
        smoke=args.smoke,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
