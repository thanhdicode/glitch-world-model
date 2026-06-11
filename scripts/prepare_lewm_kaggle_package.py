from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_kaggle import LeWMKaggleConfig, prepare_lewm_kaggle_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a validation-only LeWM Kaggle package.")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--dataset-slug", required=True)
    parser.add_argument("--kernel-slug", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--action-mode", choices=["real", "zero_action"], required=True)
    parser.add_argument("--train-dataset-name", required=True)
    parser.add_argument("--validation-dataset-name", required=True)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--max-train-steps", type=int, default=2)
    parser.add_argument("--max-validation-steps", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = LeWMKaggleConfig(
        dataset_slug=args.dataset_slug,
        kernel_slug=args.kernel_slug,
        dataset_id=args.dataset_id,
        action_mode=args.action_mode,
        train_dataset_name=args.train_dataset_name,
        validation_dataset_name=args.validation_dataset_name,
        batch_size=args.batch_size,
        max_epochs=args.max_epochs,
        max_train_steps=args.max_train_steps,
        max_validation_steps=args.max_validation_steps,
    )
    summary = prepare_lewm_kaggle_package(
        args.source_root,
        args.output_root,
        config,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
