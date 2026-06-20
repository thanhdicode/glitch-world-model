from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from cloud.wob_kaggle_native.common import write_debug_tarball


def load_split_rows(split_csv: Path) -> list[dict[str, str]]:
    with split_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_p1_selected_rows(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    selected = [
        row for row in rows if row["label"] == "Normal" and row["split"] in {"train", "validation"}
    ]
    summary = {
        "train_normal_count": sum(
            1 for row in selected if row["label"] == "Normal" and row["split"] == "train"
        ),
        "validation_normal_count": sum(
            1 for row in selected if row["label"] == "Normal" and row["split"] == "validation"
        ),
        "validation_buggy_excluded_count": sum(
            1 for row in rows if row["label"] == "Buggy" and row["split"] == "validation"
        ),
        "locked_rows_skipped": sum(1 for row in rows if row["split"] == "test"),
    }
    return sorted(selected, key=lambda row: row["source"]), summary


def write_selected_split_csv(split_csv: Path, output_path: Path) -> dict[str, int]:
    rows = load_split_rows(split_csv)
    selected, summary = build_p1_selected_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    return summary


def load_research_schedule(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    training = config["training"]
    main_run = training["main_run"]
    return {
        "batch_size": training["batch_size"],
        "num_workers": training["num_workers"],
        "mixed_precision": training["amp"],
        "gradient_clip_norm": training["gradient_clip_norm"],
        "target_optimizer_updates": main_run["target_optimizer_updates"],
        "evaluation_interval_updates": main_run["evaluation_interval_updates"],
        "checkpoint_interval_updates": main_run["checkpoint_interval_updates"],
        "early_stopping_patience": main_run["early_stopping_patience_evaluations"],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def package_artifacts(output_path: Path, roots: list[tuple[Path, str]]) -> None:
    write_debug_tarball(output_path, roots, exclude_suffixes=(".tar", ".lance"))
