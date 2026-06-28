"""P6 demo lane for reproducible qualitative LeWM surprise timelines.

This script is a thin wrapper around
``scripts/generate_qualitative_surprise_timelines.py``. It is intentionally
claim-limited: it never opens locked test data, never contacts Kaggle, and
never computes temporal-localization metrics. All full-run plots are qualitative
only and all runs emit a receipt with explicit safety flags.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import traceback
from pathlib import Path
from types import ModuleType
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

RECEIPT_STATIC: dict[str, object] = {
    "temporal_metrics_claimed": False,
    "locked_test_used": False,
    "ground_truth_spans_available": False,
    "kaggle_required": False,
    "claim_boundary": (
        "qualitative timeline only — no temporal-localization metric, "
        "no locked test, no broad LeWM superiority claim"
    ),
    "demo_phase": "P6",
}

# Backward-compatible private alias for focused tests and external dry-run checks.
_RECEIPT_STATIC = RECEIPT_STATIC


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P6 qualitative glitch demo lane. Runs without Kaggle or locked test.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    default_base = REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint"
    parser.add_argument(
        "--comparison-csv",
        type=Path,
        default=default_base / "followup_comparison.csv",
        help="Non-locked followup_comparison.csv artifact.",
    )
    parser.add_argument(
        "--episode-scores-csv",
        type=Path,
        default=default_base / "followup_episode_scores.csv",
        help="Non-locked followup_episode_scores.csv artifact.",
    )
    parser.add_argument(
        "--manifest-csv",
        type=Path,
        default=default_base / "followup_manifest.csv",
        help="Non-locked followup_manifest.csv artifact.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "demo_timelines",
        help="Directory for demo plots and demo_receipt.json.",
    )
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=4,
        help="Maximum qualitative episodes to request across buggy and normal examples.",
    )
    parser.add_argument(
        "--method-family",
        default="lewm",
        help="Method family to visualize from the comparison artifact.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write a safety receipt and report whether expected inputs are present; no plots.",
    )
    return parser


def check_inputs_exist(
    comparison_csv: Path,
    episode_scores_csv: Path,
    manifest_csv: Path,
) -> list[str]:
    missing: list[str] = []
    expected_paths = (
        ("comparison_csv", comparison_csv),
        ("episode_scores_csv", episode_scores_csv),
        ("manifest_csv", manifest_csv),
    )
    for label, path in expected_paths:
        if not path.is_file():
            missing.append(f"{label}: {path}")
    return missing


def write_receipt(output_dir: Path, extra: dict[str, object]) -> Path:
    receipt = {**RECEIPT_STATIC, **extra}
    receipt_path = output_dir / "demo_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return receipt_path


def _load_module_from_path(module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "generate_qualitative_surprise_timelines", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_timeline_generator() -> Callable[[list[str] | None], int]:
    try:
        from scripts.generate_qualitative_surprise_timelines import (  # noqa: PLC0415
            main as generator_main,
        )

        return generator_main
    except ImportError:
        generator_path = REPO_ROOT / "scripts" / "generate_qualitative_surprise_timelines.py"
        if not generator_path.is_file():
            raise FileNotFoundError(generator_path) from None
        module = _load_module_from_path(generator_path)
        generator_main = getattr(module, "main", None)
        if not callable(generator_main):
            raise AttributeError(f"{generator_path} does not expose callable main().")
        return generator_main


def _split_episode_budget(max_episodes: int) -> tuple[int, int]:
    if max_episodes < 1:
        raise ValueError("--max-episodes must be at least 1.")
    max_buggy = (max_episodes + 1) // 2
    max_normal = max_episodes // 2
    return max_buggy, max_normal


def build_generator_argv(args: argparse.Namespace) -> list[str]:
    max_buggy, max_normal = _split_episode_budget(args.max_episodes)
    return [
        "--comparison-csv",
        str(args.comparison_csv),
        "--episode-scores-csv",
        str(args.episode_scores_csv),
        "--manifest-csv",
        str(args.manifest_csv),
        "--output-dir",
        str(args.output_dir),
        "--receipt-path",
        str(args.output_dir / "qualitative_timeline_receipt.json"),
        "--max-buggy",
        str(max_buggy),
        "--max-normal",
        str(max_normal),
        "--method-family",
        args.method_family,
    ]


def _print_safety_banner() -> None:
    print("=" * 70)
    print("P6 Qualitative Glitch Demo Lane")
    print("  temporal_metrics_claimed : False")
    print("  locked_test_used         : False")
    print("  kaggle_required          : False")
    print("=" * 70)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _print_safety_banner()

    missing = check_inputs_exist(args.comparison_csv, args.episode_scores_csv, args.manifest_csv)
    if args.dry_run:
        receipt_path = write_receipt(
            args.output_dir,
            {
                "mode": "dry_run",
                "inputs_found": not missing,
                "missing_inputs": missing,
                "plots_generated": [],
            },
        )
        print(f"[dry-run] Receipt written: {receipt_path}")
        if missing:
            print("[dry-run] Missing inputs; this is expected when ignored artifacts are absent:")
            for item in missing:
                print(f"  {item}")
        print("[dry-run] Done.")
        return 0

    if missing:
        print("ERROR: required non-locked demo inputs are missing:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        print("Run with --dry-run to verify safety flags without artifacts.", file=sys.stderr)
        return 1

    try:
        generator_main = load_timeline_generator()
        generator_rc = generator_main(build_generator_argv(args))
        if generator_rc not in (None, 0):
            raise RuntimeError(f"timeline generator returned non-zero status {generator_rc!r}")
        plots_generated = sorted(str(path) for path in args.output_dir.glob("*.png"))
        receipt_path = write_receipt(
            args.output_dir,
            {
                "mode": "full",
                "inputs_found": True,
                "plots_generated": plots_generated,
                "comparison_csv": str(args.comparison_csv),
                "episode_scores_csv": str(args.episode_scores_csv),
                "manifest_csv": str(args.manifest_csv),
                "method_family": args.method_family,
            },
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR during demo generation: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    print(f"Receipt: {receipt_path}")
    print(f"Plots: {args.output_dir}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
