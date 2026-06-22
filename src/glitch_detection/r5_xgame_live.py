"""Four-role R5-XGame materialization contracts used by the staged runner."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .lewm_training import LeWMTrainConfig, train_lewm

ROLE_DATASETS = {
    "train_normal": "train_normal",
    "calibration_normal": "calibration_normal",
    "evaluation_normal_negative": "evaluation_normal_negative",
    "evaluation_buggy_positive": "evaluation_buggy_positive",
}


def partition_manifest_rows(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Partition only the four frozen roles without silently widening evaluation."""
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        role = row["evaluation_role"]
        if role not in ROLE_DATASETS:
            raise ValueError(f"Unsupported R5-XGame role: {role}")
        if row["split"] == "test":
            raise ValueError("R5-XGame refuses test rows during materialization.")
        result[role].append(row)
    missing = [role for role in ROLE_DATASETS if not result[role]]
    if missing:
        raise ValueError(f"R5-XGame materialization missing roles: {missing}")
    return dict(result)


def training_roles(
    rows: Iterable[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return the only rows permitted to reach fresh LeWM training."""
    partitioned = partition_manifest_rows(rows)
    train = partitioned["train_normal"]
    calibration = partitioned["calibration_normal"]
    if any(row["label"] != "Normal" for row in [*train, *calibration]):
        raise ValueError("R5-XGame training and calibration must remain normal-only.")
    return train, calibration


def train_fresh_seed(
    train_lance: Path,
    calibration_lance: Path,
    output_dir: Path,
    *,
    seed: int,
    device: str,
    resume: bool,
) -> dict[str, object]:
    """Train one new R5-XGame seed from frozen role-specific Lance datasets."""
    if seed not in {42, 43, 44}:
        raise ValueError("R5-XGame supports only fresh seeds 42, 43, and 44.")
    if "r5_wob" in str(output_dir).lower():
        raise ValueError("R5-XGame refuses to write into an R5-WOB artifact path.")
    config = LeWMTrainConfig(
        seed=seed,
        run_kind="research",
        target_optimizer_updates=500,
        evaluation_interval_updates=50,
        checkpoint_interval_updates=50,
        mixed_precision=device == "cuda",
    )
    return train_lewm(
        train_lance, calibration_lance, output_dir, config, device=device, resume=resume
    )
