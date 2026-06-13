from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

EXPECTED_TRAIN_HASH = "e6c48a35eef32edf43a6c78db37c52adcbbe656f47b2e453e1917365355f3aa1"
EXPECTED_VALIDATION_NORMAL_HASH = "bb89e66c6afa5d3af7728be8efd0bacbf49cfedca6704fd27cc6178f27e556e6"
EXPECTED_VALIDATION_BUGGY_HASH = "02c2417579bb25cd683738106d0603c5ed7a70fb6f3271716f9c23b95bae10f1"
EXPECTED_PROFILE_FINGERPRINT = "694390b59b874dfc11e16c6ed7774d847c944485f09b655fd3c019b200a2596d"
EXPECTED_PROFILE_SHA = "ff372c9ec50edbd517024e92ef058cafadfd4abc"


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_research_mvp_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors: list[str] = []

    dataset = payload.get("dataset", {})
    local_scope = dataset.get("local_scope", {})
    training = payload.get("training", {})
    main_run = training.get("main_run", {})
    profile = training.get("profile_run", {})
    evaluation = payload.get("evaluation", {})
    optional_video = evaluation.get("optional_frozen_video_representation", {})

    _require(
        payload.get("status") == "r2_frozen_main_run_schedule", "status is not R2 frozen", errors
    )
    _require(payload.get("validation_only") is True, "validation_only must be true", errors)
    _require(
        payload.get("locked_test_enabled") is False, "locked_test_enabled must be false", errors
    )
    _require(
        dataset.get("locked_test_materialized") is False,
        "dataset locked_test_materialized must be false",
        errors,
    )

    _require(
        local_scope.get("train_lance_sha256") == EXPECTED_TRAIN_HASH,
        "train-normal Lance hash mismatch",
        errors,
    )
    _require(
        local_scope.get("validation_normal_lance_sha256") == EXPECTED_VALIDATION_NORMAL_HASH,
        "validation-normal Lance hash mismatch",
        errors,
    )
    _require(
        local_scope.get("validation_buggy_lance_sha256") == EXPECTED_VALIDATION_BUGGY_HASH,
        "validation-buggy Lance hash mismatch",
        errors,
    )

    _require(training.get("batch_size") == 8, "batch_size must be 8 from R1 profile", errors)
    _require(training.get("amp") is True, "AMP must remain enabled", errors)
    _require(
        training.get("num_workers") == 0, "num_workers must remain 0 for Kaggle safety", errors
    )
    _require(training.get("seeds") == [42, 43, 44], "seeds must be [42, 43, 44]", errors)
    _require(
        profile.get("fingerprint") == EXPECTED_PROFILE_FINGERPRINT,
        "profile fingerprint mismatch",
        errors,
    )
    _require(profile.get("git_sha") == EXPECTED_PROFILE_SHA, "profile git SHA mismatch", errors)
    _require(
        main_run.get("target_optimizer_updates") == 15000,
        "target_optimizer_updates must be 15000",
        errors,
    )
    _require(
        main_run.get("evaluation_interval_updates") == 500,
        "evaluation interval must be 500 updates",
        errors,
    )
    _require(
        main_run.get("checkpoint_interval_updates") == 500,
        "checkpoint interval must be 500 updates",
        errors,
    )
    _require(
        main_run.get("early_stopping_patience_evaluations") == 5,
        "early stopping patience must be 5 evaluations",
        errors,
    )
    _require(
        main_run.get("seed_order") == [42, 43, 44],
        "seed order must run 42 before 43/44",
        errors,
    )

    _require(
        optional_video.get("enabled") is True,
        "optional frozen video representation baseline must be declared",
        errors,
    )
    _require(
        optional_video.get("fail_closed_if_dependency_missing") is True,
        "optional baseline must fail closed when dependencies are missing",
        errors,
    )
    _require(
        optional_video.get("blocks_lewm_critical_path") is False,
        "optional baseline must not block LeWM critical path",
        errors,
    )

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "lewm_research_mvp_config_validated",
        "config": str(path),
        "target_optimizer_updates": main_run["target_optimizer_updates"],
        "seeds": training["seeds"],
        "profile_fingerprint": profile["fingerprint"],
        "locked_test_enabled": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the frozen LeWM research MVP config.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/lewm_research_mvp.yaml"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(validate_research_mvp_config(args.config), indent=2))


if __name__ == "__main__":
    main()
