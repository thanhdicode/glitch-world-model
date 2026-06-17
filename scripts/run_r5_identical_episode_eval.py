"""CLI orchestrator for R5 identical-episode evaluation.

This script takes:
  - A Gate 7-style window manifest CSV (--manifest)
  - One or more LeWM window score CSVs, each specified as ``name:path``
    (--lewm-scores); typically one per training seed
  - A Gate 8-style baseline scores CSV (--baseline-scores)

And produces episode-level AUROC / AUPRC (primary) plus F1@normal-P95 and
FPR@95TPR (secondary) with 95% grouped episode-bootstrap CIs, for all methods
on the identical non-locked episode manifest.

The script refuses any path containing "locked" in its filename and never
touches the locked test split.

Usage example (dry-run):
    python scripts/run_r5_identical_episode_eval.py \\
        --manifest outputs/gate7/window_manifest.csv \\
        --lewm-scores seed43:outputs/gate7_seed43/lewm_transition_scores.csv \\
        --lewm-scores seed44:outputs/gate7_seed44/lewm_transition_scores.csv \\
        --baseline-scores outputs/gate8/baseline_scores.csv \\
        --output-dir outputs/r5_eval \\
        --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from glitch_detection.lewm_adapter import sha256_file
from glitch_detection.lewm_r5_eval import (
    R5_EPISODE_AGGREGATIONS,
    R5_WINDOW_AGGREGATIONS,
    run_r5_episode_eval,
)

_LOCKED_RE = re.compile(r"(?:^|[_\-])locked(?:[_\-]|$)", re.IGNORECASE)

_DEFAULT_LEWM_WIN_AGGS = ("mse_max", "l2_max")
_DEFAULT_EPISODE_AGGS = ("max",)


def _parse_named_path(value: str) -> tuple[str, Path]:
    """Parse a ``name:path`` argument into ``(name, Path)``."""
    if ":" not in value:
        raise argparse.ArgumentTypeError(f"Expected format name:path, got {value!r}")
    name, _, raw_path = value.partition(":")
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"Empty scorer name in {value!r}")
    return name, Path(raw_path.strip())


def _validate_inputs(
    manifest: Path,
    lewm_scores_by_name: dict[str, Path],
    baseline_scores: Path,
) -> None:
    missing: list[str] = []
    for description, path in [
        ("manifest", manifest),
        ("baseline-scores", baseline_scores),
        *((f"lewm-scores:{n}", p) for n, p in lewm_scores_by_name.items()),
    ]:
        if not path.is_file():
            missing.append(f"  {description}: {path}")
    if missing:
        raise FileNotFoundError("Missing R5 input file(s):\n" + "\n".join(missing))
    for path in [manifest, baseline_scores, *lewm_scores_by_name.values()]:
        if _LOCKED_RE.search(path.name):
            raise ValueError(f"R5 refuses locked-test path: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "R5 identical-episode evaluation: episode-level AUROC/AUPRC "
            "with bootstrap CI for all methods on the non-locked validation manifest."
        )
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Gate 7-style window manifest CSV (window_manifest.csv).",
    )
    parser.add_argument(
        "--lewm-scores",
        action="append",
        dest="lewm_scores",
        default=[],
        metavar="NAME:PATH",
        help=("LeWM window score CSV, specified as name:path. May be repeated for multiple seeds."),
    )
    parser.add_argument(
        "--baseline-scores",
        required=True,
        type=Path,
        help="Gate 8-style baseline scores CSV (baseline_scores.csv).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for R5 output artifacts.",
    )
    parser.add_argument(
        "--lewm-window-aggregations",
        nargs="+",
        choices=list(R5_WINDOW_AGGREGATIONS),
        default=list(_DEFAULT_LEWM_WIN_AGGS),
        help=(
            "How to aggregate three LeWM transition scores into one per-window "
            f"scalar. Default: {list(_DEFAULT_LEWM_WIN_AGGS)}."
        ),
    )
    parser.add_argument(
        "--episode-aggregations",
        nargs="+",
        choices=list(R5_EPISODE_AGGREGATIONS),
        default=list(_DEFAULT_EPISODE_AGGS),
        help=(
            f"How to aggregate window scores into an episode score. "
            f"Default: {list(_DEFAULT_EPISODE_AGGS)}."
        ),
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of episode-grouped bootstrap iterations (default: 1000).",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=42,
        help="RNG seed for bootstrap sampling (default: 42).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=("Validate inputs and print provenance hashes without running the full evaluation."),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    lewm_scores_by_name: dict[str, Path] = {}
    for raw in args.lewm_scores:
        name, path = _parse_named_path(raw)
        if name in lewm_scores_by_name:
            raise ValueError(f"Duplicate LeWM scorer name: {name!r}")
        lewm_scores_by_name[name] = path

    _validate_inputs(args.manifest, lewm_scores_by_name, args.baseline_scores)

    if args.dry_run:
        dry_payload = {
            "status": "dry-run",
            "manifest_sha256": sha256_file(args.manifest),
            "baseline_scores_sha256": sha256_file(args.baseline_scores),
            "lewm_scores_sha256": {
                name: sha256_file(path) for name, path in sorted(lewm_scores_by_name.items())
            },
            "output_dir": str(args.output_dir),
            "lewm_window_aggregations": args.lewm_window_aggregations,
            "episode_aggregations": args.episode_aggregations,
            "n_bootstrap": args.n_bootstrap,
            "bootstrap_seed": args.bootstrap_seed,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        }
        print(json.dumps(dry_payload, indent=2))
        return

    result = run_r5_episode_eval(
        manifest_path=args.manifest,
        lewm_scores_by_name=lewm_scores_by_name,
        baseline_scores_path=args.baseline_scores,
        output_dir=args.output_dir,
        lewm_window_aggregations=tuple(args.lewm_window_aggregations),
        episode_aggregations=tuple(args.episode_aggregations),
        n_bootstrap=args.n_bootstrap,
        bootstrap_seed=args.bootstrap_seed,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
