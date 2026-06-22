"""Fail-closed protocol checks for the non-locked R5-XGame evaluation."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

REQUIRED_FIELDS = {
    "dataset_id",
    "source",
    "episode_id",
    "pair_id",
    "label",
    "split",
    "evaluation_role",
}
TRAIN_ROLE = "train_normal"
CALIBRATION_ROLE = "calibration_normal"
NORMAL_EVAL_ROLE = "evaluation_normal_negative"
BUGGY_EVAL_ROLE = "evaluation_buggy_positive"
LOCKED_ROLE = "locked_test"
NONLOCKED_ROLES = {TRAIN_ROLE, CALIBRATION_ROLE, NORMAL_EVAL_ROLE, BUGGY_EVAL_ROLE}


def validate_r5_xgame_manifest(rows: Iterable[Mapping[str, str]]) -> dict[str, int]:
    """Validate the split contract before materialization or scoring.

    The function intentionally validates metadata only. It never opens source media,
    materializes Lance data, or permits locked-test rows into the non-locked protocol.
    """
    materialized_rows = [dict(row) for row in rows]
    if not materialized_rows:
        raise ValueError("R5-XGame manifest is empty.")

    missing_fields = REQUIRED_FIELDS - set(materialized_rows[0])
    if missing_fields:
        raise ValueError(f"R5-XGame manifest missing fields: {sorted(missing_fields)}")

    counts: dict[str, int] = defaultdict(int)
    seen_episodes: dict[str, str] = {}
    seen_groups: dict[str, str] = {}
    seen_sources: dict[str, str] = {}
    for row in materialized_rows:
        role = row["evaluation_role"].strip()
        label = row["label"].strip()
        split = row["split"].strip()
        episode_id = row["episode_id"].strip()
        group_id = row["pair_id"].strip() or episode_id
        source = row["source"].strip()
        if role not in NONLOCKED_ROLES:
            raise ValueError(f"R5-XGame forbids role {role!r} in its non-locked manifest.")
        if split == "test" or role == LOCKED_ROLE:
            raise ValueError("Locked/test rows are forbidden in R5-XGame.")
        if not episode_id or not group_id:
            raise ValueError("R5-XGame rows require non-empty episode_id and pair_id.")
        if role in {TRAIN_ROLE, CALIBRATION_ROLE, NORMAL_EVAL_ROLE} and label != "Normal":
            raise ValueError(f"Role {role} must contain only Normal rows.")
        if role == BUGGY_EVAL_ROLE and label != "Buggy":
            raise ValueError("evaluation_buggy_positive must contain only Buggy rows.")
        if not source:
            raise ValueError("R5-XGame rows require a non-empty source.")
        for key, seen in (
            (episode_id, seen_episodes),
            (group_id, seen_groups),
            (source, seen_sources),
        ):
            previous_role = seen.get(key)
            if previous_role is not None and previous_role != role:
                raise ValueError(
                    f"R5-XGame leakage: identifier {key!r} appears in both "
                    f"{previous_role!r} and {role!r}."
                )
            seen[key] = role
        counts[role] += 1

    for role in (TRAIN_ROLE, CALIBRATION_ROLE, NORMAL_EVAL_ROLE, BUGGY_EVAL_ROLE):
        if counts[role] == 0:
            raise ValueError(f"R5-XGame requires at least one {role} row.")
    return dict(counts)
