from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from . import feature_distance, frame_diff, lewm_latent, mini_latent, video_autoencoder

ScorerFn = Callable[[Path, Path | None, Path], Path]


def _frame_diff_scorer(manifest_path: Path, labels_path: Path | None, output_path: Path) -> Path:
    _ = labels_path
    return frame_diff.score_manifest(manifest_path, output_path)


SCORERS: dict[str, ScorerFn] = {
    "frame_diff": _frame_diff_scorer,
    "feature_distance": feature_distance.score_manifest,
    "mini_latent": mini_latent.score_manifest,
    "lewm_latent": lewm_latent.score_manifest,
    "video_autoencoder": video_autoencoder.score_manifest,
}


def available_scorers() -> list[str]:
    return sorted(SCORERS)


def run_scorer(
    scorer_name: str,
    manifest_path: Path,
    labels_path: Path | None,
    output_path: Path,
) -> Path:
    if scorer_name not in SCORERS:
        raise ValueError(
            f"Unknown scorer '{scorer_name}'. Available scorers: {', '.join(available_scorers())}"
        )
    return SCORERS[scorer_name](manifest_path, labels_path, output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score clips with a registered baseline scorer.")
    parser.add_argument("--scorer", required=True, choices=available_scorers())
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional labels CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output scores.csv path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_path = run_scorer(args.scorer, args.manifest, args.labels, args.output)
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()
