from __future__ import annotations

import json
from pathlib import Path

from glitch_detection.lewm_training import LeWMTrainConfig
from scripts.run_r6_sigreg_ablation import build_controlled_pairs, build_r6_ablation_variants
from scripts.validate_r6_ablations import validate_r6


def test_r6_sigreg_ablation_builds_full_variant_matrix():
    variants = build_r6_ablation_variants(seeds=[42], base_config=LeWMTrainConfig())
    pairs = build_controlled_pairs(variants)

    assert len(variants) == 4
    assert {pair["pair_type"] for pair in pairs} == {"sigreg", "action_conditioning"}


def test_validate_r6_accepts_controlled_pair_receipts(tmp_path: Path):
    output_dir = tmp_path / "r6"
    output_dir.mkdir(parents=True)
    executed_variants = []
    for variant_name, seed, sigreg_enabled, action_mode in (
        ("seed42_sigreg_off_real_action", 42, False, "real"),
        ("seed42_sigreg_on_real_action", 42, True, "real"),
        ("seed42_sigreg_off_zero_action", 42, False, "zero_action"),
        ("seed42_sigreg_on_zero_action", 42, True, "zero_action"),
    ):
        executed_variants.append(
            {
                "variant_name": variant_name,
                "training_metadata": {
                    "dataset_hashes": {"train": "a", "validation": "b"},
                    "config": {"seed": seed},
                    "sigreg_enabled": sigreg_enabled,
                    "action_mode": action_mode,
                },
            }
        )
    (output_dir / "r6_ablation_receipt.json").write_text(
        json.dumps(
            {
                "executed_variants": executed_variants,
                "locked_test_materialized": False,
                "locked_test_scored": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "r6_controlled_pairs.json").write_text(
        json.dumps(
            {
                "pairs": [
                    {
                        "pair_type": "sigreg",
                        "control_variant": "seed42_sigreg_off_real_action",
                        "treatment_variant": "seed42_sigreg_on_real_action",
                    },
                    {
                        "pair_type": "action_conditioning",
                        "control_variant": "seed42_sigreg_on_zero_action",
                        "treatment_variant": "seed42_sigreg_on_real_action",
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = validate_r6(output_dir)

    assert result["valid"] is True
    assert "controlled_pairs" in result["completed_ablations"]
