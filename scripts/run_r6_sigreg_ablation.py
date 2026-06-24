from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from glitch_detection.lewm_adapter import ActionMode
from glitch_detection.lewm_training import LeWMTrainConfig, train_lewm

ROOT = Path(__file__).resolve().parents[1]


def _variant_name(seed: int, *, sigreg_enabled: bool, action_mode: str) -> str:
    sigreg_name = "sigreg_on" if sigreg_enabled else "sigreg_off"
    action_name = "real_action" if action_mode == ActionMode.REAL.value else "zero_action"
    return f"seed{seed}_{sigreg_name}_{action_name}"


def build_r6_ablation_variants(
    *, seeds: list[int], base_config: LeWMTrainConfig
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for seed in seeds:
        for sigreg_enabled in (True, False):
            for action_mode in (ActionMode.REAL.value, ActionMode.ZERO_ACTION.value):
                config = replace(
                    base_config,
                    seed=seed,
                    sigreg_enabled=sigreg_enabled,
                    action_mode=action_mode,
                )
                variants.append(
                    {
                        "variant_name": _variant_name(
                            seed, sigreg_enabled=sigreg_enabled, action_mode=action_mode
                        ),
                        "seed": seed,
                        "sigreg_enabled": sigreg_enabled,
                        "action_mode": action_mode,
                        "config": config,
                    }
                )
    return variants


def build_controlled_pairs(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (variant["seed"], variant["sigreg_enabled"], variant["action_mode"]): variant
        for variant in variants
    }
    pairs: list[dict[str, Any]] = []
    for seed in sorted({variant["seed"] for variant in variants}):
        for action_mode in (ActionMode.REAL.value, ActionMode.ZERO_ACTION.value):
            on_variant = by_key[(seed, True, action_mode)]
            off_variant = by_key[(seed, False, action_mode)]
            pairs.append(
                {
                    "pair_type": "sigreg",
                    "seed": seed,
                    "control_variant": off_variant["variant_name"],
                    "treatment_variant": on_variant["variant_name"],
                    "changed_field": "sigreg_enabled",
                    "action_mode": action_mode,
                }
            )
        for sigreg_enabled in (True, False):
            real_variant = by_key[(seed, sigreg_enabled, ActionMode.REAL.value)]
            zero_variant = by_key[(seed, sigreg_enabled, ActionMode.ZERO_ACTION.value)]
            pairs.append(
                {
                    "pair_type": "action_conditioning",
                    "seed": seed,
                    "control_variant": zero_variant["variant_name"],
                    "treatment_variant": real_variant["variant_name"],
                    "changed_field": "action_mode",
                    "sigreg_enabled": sigreg_enabled,
                }
            )
    return pairs


def run_r6_sigreg_ablation(
    *,
    train_path: Path,
    validation_path: Path,
    output_root: Path,
    seeds: list[int],
    base_config: LeWMTrainConfig,
    device: str,
    dry_run: bool,
    resume: bool,
) -> dict[str, Any]:
    variants = build_r6_ablation_variants(seeds=seeds, base_config=base_config)
    pairs = build_controlled_pairs(variants)
    output_root.mkdir(parents=True, exist_ok=True)
    plan = {
        "status": "dry_run_ready" if dry_run else "planned",
        "train_path": str(train_path),
        "validation_path": str(validation_path),
        "variant_count": len(variants),
        "pair_count": len(pairs),
        "seeds": seeds,
        "device": device,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "variants": [
            {
                **{key: value for key, value in variant.items() if key != "config"},
                "config": variant["config"].__dict__,
            }
            for variant in variants
        ],
        "controlled_pairs": pairs,
    }
    (output_root / "r6_ablation_plan.json").write_text(
        json.dumps(plan, indent=2) + "\n",
        encoding="utf-8",
    )
    if dry_run:
        return plan

    executed_variants: list[dict[str, Any]] = []
    for variant in variants:
        variant_root = output_root / variant["variant_name"]
        metadata = train_lewm(
            train_path=train_path,
            validation_path=validation_path,
            output_root=variant_root,
            config=variant["config"],
            device=device,
            resume=resume,
        )
        executed_variants.append(
            {
                "variant_name": variant["variant_name"],
                "seed": variant["seed"],
                "sigreg_enabled": variant["sigreg_enabled"],
                "action_mode": variant["action_mode"],
                "artifact_root": str(variant_root),
                "training_metadata": metadata,
            }
        )
    receipt = {
        **plan,
        "status": "training_complete_unvalidated",
        "executed_variants": executed_variants,
    }
    (output_root / "r6_controlled_pairs.json").write_text(
        json.dumps(
            {
                "status": "controlled_pairs_declared",
                "pairs": pairs,
                "variant_count": len(executed_variants),
                "locked_test_materialized": False,
                "locked_test_scored": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_root / "r6_ablation_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run controlled SIGReg and action-conditioning R6 ablations."
    )
    parser.add_argument("--train-path", type=Path, required=True)
    parser.add_argument("--validation-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--device", default="auto")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--image-size", type=int, default=112)
    parser.add_argument("--history-size", type=int, default=3)
    parser.add_argument("--embed-dim", type=int, default=192)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--sigreg-weight", type=float, default=0.09)
    parser.add_argument("--sigreg-projections", type=int, default=128)
    parser.add_argument("--target-optimizer-updates", type=int, default=500)
    parser.add_argument("--evaluation-interval-updates", type=int, default=100)
    parser.add_argument("--checkpoint-interval-updates", type=int, default=100)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    base_config = LeWMTrainConfig(
        image_size=args.image_size,
        history_size=args.history_size,
        embed_dim=args.embed_dim,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        sigreg_weight=args.sigreg_weight,
        sigreg_projections=args.sigreg_projections,
        run_kind="research",
        target_optimizer_updates=args.target_optimizer_updates,
        evaluation_interval_updates=args.evaluation_interval_updates,
        checkpoint_interval_updates=args.checkpoint_interval_updates,
    )
    receipt = run_r6_sigreg_ablation(
        train_path=args.train_path,
        validation_path=args.validation_path,
        output_root=args.output_root,
        seeds=args.seeds,
        base_config=base_config,
        device=args.device,
        dry_run=args.dry_run,
        resume=args.resume,
    )
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
