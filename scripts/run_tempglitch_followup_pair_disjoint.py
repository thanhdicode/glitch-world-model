from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the bounded TempGlitch pair-disjoint follow-up from validated R5 artifacts."
    )
    parser.add_argument(
        "--r5-output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "r5_tempglitch_identical_episode",
        help="Validated R5 TempGlitch output directory.",
    )
    parser.add_argument(
        "--train-lance",
        type=Path,
        default=REPO_ROOT
        / "outputs"
        / "research_mvp"
        / "datasets"
        / "tempglitch_train_normal_all_local.lance",
        help="Train-normal Lance inventory used by the validated R5 bundle.",
    )
    parser.add_argument(
        "--validation-normal-lance",
        type=Path,
        default=REPO_ROOT
        / "outputs"
        / "research_mvp"
        / "datasets"
        / "tempglitch_validation_normal_all_local.lance",
        help="Validation-normal Lance inventory used by the validated R5 bundle.",
    )
    parser.add_argument(
        "--validation-buggy-lance",
        type=Path,
        default=REPO_ROOT
        / "outputs"
        / "research_mvp"
        / "datasets"
        / "tempglitch_validation_buggy_all_local.lance",
        help="Validation-buggy Lance inventory used by the validated R5 bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint",
        help="Output directory for the bounded follow-up bundle.",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=42,
        help="Bootstrap seed for pair-grouped confidence intervals.",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap resamples for supported confidence intervals.",
    )
    return parser


def _command_text(argv: list[str]) -> str:
    return subprocess.list2cmdline([sys.executable, *argv])


def main(argv: list[str] | None = None) -> int:
    from glitch_detection.tempglitch_followup import run_tempglitch_followup_pair_disjoint

    argv = argv if argv is not None else sys.argv
    args = build_parser().parse_args(argv[1:])
    result = run_tempglitch_followup_pair_disjoint(
        r5_output_dir=args.r5_output_dir,
        train_lance=args.train_lance,
        validation_normal_lance=args.validation_normal_lance,
        validation_buggy_lance=args.validation_buggy_lance,
        output_dir=args.output_dir,
        bootstrap_seed=args.bootstrap_seed,
        n_bootstrap=args.n_bootstrap,
        command_text=_command_text(argv),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
