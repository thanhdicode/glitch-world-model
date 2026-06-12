from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_training import LeWMTrainConfig, train_lewm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run validation-only real-LeWM training.")
    parser.add_argument("--train-dataset", required=True, type=Path)
    parser.add_argument("--validation-dataset", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--image-size", type=int, default=112)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--predictor-depth", type=int, default=6)
    parser.add_argument("--sigreg-projections", type=int, default=128)
    parser.add_argument("--max-train-steps", type=int, default=None)
    parser.add_argument("--max-validation-steps", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-identical-datasets-for-smoke", action="store_true")
    parser.add_argument(
        "--run-kind",
        choices=("engineering_smoke", "research"),
        default="engineering_smoke",
    )
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--pin-memory", action="store_true")
    parser.add_argument("--mixed-precision", action="store_true")
    parser.add_argument("--early-stopping-patience", type=int, default=None)
    parser.add_argument("--early-stopping-min-delta", type=float, default=0.0)
    parser.add_argument("--gradient-clip-norm", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = LeWMTrainConfig(
        image_size=args.image_size,
        batch_size=args.batch_size,
        epochs=args.epochs,
        predictor_depth=args.predictor_depth,
        sigreg_projections=args.sigreg_projections,
        max_train_steps=args.max_train_steps,
        max_validation_steps=args.max_validation_steps,
        allow_identical_datasets_for_smoke=args.allow_identical_datasets_for_smoke,
        run_kind=args.run_kind,
        num_workers=args.num_workers,
        pin_memory=args.pin_memory,
        mixed_precision=args.mixed_precision,
        early_stopping_patience=args.early_stopping_patience,
        early_stopping_min_delta=args.early_stopping_min_delta,
        gradient_clip_norm=args.gradient_clip_norm,
    )
    result = train_lewm(
        args.train_dataset,
        args.validation_dataset,
        args.output_root,
        config,
        device=args.device,
        resume=args.resume,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
