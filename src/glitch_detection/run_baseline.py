from __future__ import annotations

import argparse
from pathlib import Path

from .evaluate import evaluate_scores
from .plot_scores import plot_scores
from .preprocess import preprocess_input
from .score_clips import available_scorers, run_scorer


def run_baseline(
    input_path: Path,
    labels_path: Path | None,
    experiment_name: str,
    clip_length: int,
    stride: int,
    size: int,
    fps: float | None,
    data_dir: Path,
    outputs_dir: Path,
    scorer_name: str = "frame_diff",
    demo_allow_evaluation_label_fitting: bool = False,
) -> dict[str, Path]:
    if (
        scorer_name in {"feature_distance", "mini_latent"}
        and not demo_allow_evaluation_label_fitting
    ):
        raise ValueError(
            "Train-dependent scorers in run_baseline are demo-only and fit on evaluation labels. "
            "Use a split-aware runner, or set demo_allow_evaluation_label_fitting=True explicitly."
        )
    processed_dir = data_dir / experiment_name
    scores_path = outputs_dir / f"{experiment_name}_scores.csv"
    metrics_path = outputs_dir / f"{experiment_name}_metrics.json"
    plot_path = outputs_dir / f"{experiment_name}_scores.png"

    manifest_path = preprocess_input(
        input_path=input_path,
        output_dir=processed_dir,
        clip_length=clip_length,
        stride=stride,
        size=size,
        fps=fps,
    )
    run_scorer(
        scorer_name,
        manifest_path,
        labels_path,
        scores_path,
        allow_evaluation_label_fitting=demo_allow_evaluation_label_fitting,
    )
    evaluate_scores(scores_path, labels_path, metrics_path, allow_fit_threshold=True)
    plot_scores(scores_path, plot_path)

    return {
        "manifest": manifest_path,
        "scores": scores_path,
        "metrics": metrics_path,
        "plot": plot_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full frame-difference baseline pipeline on a video or frame folder."
    )
    parser.add_argument("--input", required=True, type=Path, help="Video file or folder of frames.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional labels CSV.")
    parser.add_argument("--name", required=True, help="Experiment name used for output files.")
    parser.add_argument("--clip-length", type=int, default=16, help="Number of frames per clip.")
    parser.add_argument("--stride", type=int, default=8, help="Frame stride between clips.")
    parser.add_argument("--size", type=int, default=128, help="Output frame size in pixels.")
    parser.add_argument(
        "--fps", type=float, default=None, help="Override FPS for frame-folder inputs."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--scorer", choices=available_scorers(), default="frame_diff")
    parser.add_argument(
        "--demo-allow-evaluation-label-fitting",
        action="store_true",
        help="Unsafe for benchmark claims; permits train-dependent scorers in this demo runner.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    outputs = run_baseline(
        input_path=args.input,
        labels_path=args.labels,
        experiment_name=args.name,
        clip_length=args.clip_length,
        stride=args.stride,
        size=args.size,
        fps=args.fps,
        data_dir=args.data_dir,
        outputs_dir=args.outputs_dir,
        scorer_name=args.scorer,
        demo_allow_evaluation_label_fitting=args.demo_allow_evaluation_label_fitting,
    )
    for label, path in outputs.items():
        print(f"{label.capitalize()}: {path}")


if __name__ == "__main__":
    main()
