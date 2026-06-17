"""R5 identical-episode evaluation for LeWM-Glitch.

This module implements episode-level (not window-level) evaluation of all
methods on an identical non-locked TempGlitch validation episode manifest.

Primary metrics  : AUROC, AUPRC
Secondary metrics: F1@normal-calibration-P95, FPR@95TPR
CI               : 95% grouped episode-bootstrap (resample episodes with
                   replacement, 1000 iterations by default)

All evaluation gates:
- No locked-test path may appear as any input.
- Episode labels must be homogeneous (all windows in one episode share one label).
- Calibration episodes must all be normal; buggy episodes must not be in the
  calibration set.
- Evaluation set must contain both normal and buggy episodes.
"""

from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from .evaluate import auroc, average_precision, binary_metrics
from .lewm_adapter import sha256_file
from .lewm_lance_eval import (
    read_csv_rows,
    runtime_provenance,
    write_csv_rows,
)

R5_WINDOW_AGGREGATIONS = ("mse_max", "mse_mean", "l2_max", "l2_mean")
R5_EPISODE_AGGREGATIONS = ("max", "mean")

R5_EPISODE_MANIFEST_FIELDS = (
    "episode_id",
    "dataset_name",
    "label",
    "evaluation_role",
    "window_count",
    "category",
)

R5_COMPARISON_FIELDS = (
    "scorer",
    "window_aggregation",
    "episode_aggregation",
    "auroc",
    "auprc",
    "auroc_ci_lower",
    "auroc_ci_upper",
    "auprc_ci_lower",
    "auprc_ci_upper",
    "threshold",
    "threshold_source",
    "f1",
    "precision",
    "recall",
    "fpr_at_95tpr",
    "episode_count",
    "positive_episode_count",
    "negative_episode_count",
)

_LOCKED_RE = re.compile(r"(?:^|[_\-])locked(?:[_\-]|$)", re.IGNORECASE)


def _locked_guard(path: Path) -> None:
    if _LOCKED_RE.search(path.name):
        raise ValueError(f"R5 refuses locked-test path: {path}")


@dataclass(frozen=True)
class EpisodeRecord:
    episode_id: str
    dataset_name: str
    label: str
    evaluation_role: str
    window_count: int
    category: str

    def to_csv_dict(self) -> dict[str, str]:
        d = asdict(self)
        d["window_count"] = str(d["window_count"])
        return d


def build_episode_manifest(
    window_manifest_rows: Sequence[dict[str, str]],
) -> list[EpisodeRecord]:
    """Group window rows into episode-level records.

    An episode's evaluation_role is ``calibration_normal`` if at least one of
    its windows carries that role; otherwise it is ``evaluation``.
    """
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in window_manifest_rows:
        groups[row["source_episode_id"]].append(row)

    records: list[EpisodeRecord] = []
    for episode_id, rows in sorted(groups.items()):
        labels = {r["label"].lower() for r in rows}
        if len(labels) != 1:
            raise ValueError(f"Episode {episode_id!r} has mixed labels: {sorted(labels)}")
        label = labels.pop()

        roles = [r["evaluation_role"] for r in rows]
        role = "calibration_normal" if "calibration_normal" in roles else "evaluation"
        if label == "buggy" and role == "calibration_normal":
            raise ValueError(
                f"Buggy episode {episode_id!r} must not be a calibration_normal episode."
            )

        categories = sorted({r.get("category", "") for r in rows})
        dataset_names = sorted({r.get("dataset_name", "") for r in rows})
        records.append(
            EpisodeRecord(
                episode_id=episode_id,
                dataset_name=dataset_names[0] if dataset_names else "",
                label=label,
                evaluation_role=role,
                window_count=len(rows),
                category=categories[0] if categories else "",
            )
        )
    return records


def validate_episode_manifest(records: list[EpisodeRecord]) -> None:
    if not records:
        raise ValueError("R5 episode manifest is empty.")
    episode_ids = [r.episode_id for r in records]
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("R5 episode manifest contains duplicate episode_id values.")
    calibration = [r for r in records if r.evaluation_role == "calibration_normal"]
    evaluation = [r for r in records if r.evaluation_role == "evaluation"]
    if not calibration:
        raise ValueError("R5 episode manifest has no calibration_normal episodes.")
    if not evaluation:
        raise ValueError("R5 episode manifest has no evaluation episodes.")
    eval_labels = {r.label for r in evaluation}
    if "normal" not in eval_labels or "buggy" not in eval_labels:
        raise ValueError(
            "R5 evaluation set must contain both normal and buggy episodes. "
            f"Found labels: {sorted(eval_labels)}"
        )
    for record in records:
        if "locked" in record.episode_id.lower():
            raise ValueError(
                f"R5 episode manifest must not contain locked-test episodes: {record.episode_id!r}"
            )


def _window_score_lewm(row: dict[str, str], window_aggregation: str) -> float:
    """Aggregate three LeWM transition scores to one per-window scalar."""
    if window_aggregation == "mse_max":
        values = [float(row[f"mse_t{i}"]) for i in range(1, 4)]
        return max(values)
    if window_aggregation == "mse_mean":
        values = [float(row[f"mse_t{i}"]) for i in range(1, 4)]
        return sum(values) / len(values)
    if window_aggregation == "l2_max":
        values = [float(row[f"l2_t{i}"]) for i in range(1, 4)]
        return max(values)
    if window_aggregation == "l2_mean":
        values = [float(row[f"l2_t{i}"]) for i in range(1, 4)]
        return sum(values) / len(values)
    raise ValueError(
        f"Unsupported LeWM window aggregation: {window_aggregation!r}. "
        f"Expected one of {R5_WINDOW_AGGREGATIONS}."
    )


def extract_lewm_window_scores(
    score_rows: Sequence[dict[str, str]],
    window_aggregation: str,
) -> dict[str, float]:
    """Return window_id → scalar score for a LeWM score CSV."""
    result: dict[str, float] = {}
    for row in score_rows:
        wid = row["window_id"]
        score = _window_score_lewm(row, window_aggregation)
        if not math.isfinite(score):
            raise ValueError(f"Non-finite LeWM score for window {wid!r}.")
        result[wid] = score
    return result


def extract_baseline_window_scores(
    score_rows: Sequence[dict[str, str]],
    field: str,
) -> dict[str, float]:
    """Return window_id → scalar score from a baseline (frame_diff / feature_distance) CSV."""
    result: dict[str, float] = {}
    for row in score_rows:
        wid = row["window_id"]
        score = float(row[field])
        if not math.isfinite(score):
            raise ValueError(f"Non-finite baseline score for window {wid!r}.")
        result[wid] = score
    return result


def aggregate_window_to_episode(
    episode_records: list[EpisodeRecord],
    window_manifest_rows: Sequence[dict[str, str]],
    window_scores: dict[str, float],
    episode_aggregation: str,
) -> dict[str, float]:
    """Aggregate per-window scores to per-episode scores.

    Args:
        episode_records: The R5 episode manifest.
        window_manifest_rows: The full window manifest (provides episode mapping).
        window_scores: window_id → scalar score.
        episode_aggregation: ``"max"`` or ``"mean"``.

    Returns:
        episode_id → scalar episode score.
    """
    if episode_aggregation not in R5_EPISODE_AGGREGATIONS:
        raise ValueError(
            f"Unsupported episode aggregation: {episode_aggregation!r}. "
            f"Expected one of {R5_EPISODE_AGGREGATIONS}."
        )
    episode_windows: dict[str, list[float]] = defaultdict(list)
    for row in window_manifest_rows:
        wid = row["window_id"]
        if wid not in window_scores:
            raise ValueError(f"Missing score for window {wid!r}.")
        episode_windows[row["source_episode_id"]].append(window_scores[wid])

    result: dict[str, float] = {}
    for record in episode_records:
        values = episode_windows.get(record.episode_id, [])
        if not values:
            raise ValueError(f"No window scores for episode {record.episode_id!r}.")
        if episode_aggregation == "max":
            result[record.episode_id] = max(values)
        else:
            result[record.episode_id] = sum(values) / len(values)
    return result


def _percentile_linear(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    n = len(ordered)
    position = (n - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, n - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def fpr_at_tpr(
    labels: list[int],
    scores: list[float],
    target_tpr: float = 0.95,
) -> float | None:
    """FPR at the lowest score threshold where TPR >= target_tpr."""
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    for threshold in sorted(set(scores), reverse=True):
        predictions = [int(s >= threshold) for s in scores]
        tp = sum(1 for lb, p in zip(labels, predictions) if lb == 1 and p == 1)
        fp = sum(1 for lb, p in zip(labels, predictions) if lb == 0 and p == 1)
        tpr = tp / positives
        fpr = fp / negatives
        if tpr >= target_tpr:
            return fpr
    return 1.0


def _bootstrap_primary_cis(
    eval_rows: list[dict[str, Any]],
    *,
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    """Bootstrap 95% CI for AUROC and AUPRC simultaneously (episode-grouped)."""
    episode_ids = sorted({row["episode_id"] for row in eval_rows})
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        groups[row["episode_id"]].append(row)

    rng = random.Random(seed)
    auroc_samples: list[float] = []
    auprc_samples: list[float] = []
    n_groups = len(episode_ids)

    for _ in range(n_bootstrap):
        sampled_ids = rng.choices(episode_ids, k=n_groups)
        sample_labels: list[int] = []
        sample_scores: list[float] = []
        for eid in sampled_ids:
            for row in groups[eid]:
                sample_labels.append(int(row["label"]))
                sample_scores.append(float(row["score"]))
        a = auroc(sample_labels, sample_scores)
        ap = average_precision(sample_labels, sample_scores)
        if a is not None:
            auroc_samples.append(a)
        if ap is not None:
            auprc_samples.append(ap)

    def _ci(samples: list[float]) -> dict[str, float | None]:
        if not samples:
            return {"lower": None, "upper": None}
        return {
            "lower": _percentile_linear(samples, 0.025),
            "upper": _percentile_linear(samples, 0.975),
        }

    return {
        "auroc": _ci(auroc_samples),
        "auprc": _ci(auprc_samples),
        "n_bootstrap": n_bootstrap,
        "valid_auroc_count": len(auroc_samples),
        "valid_auprc_count": len(auprc_samples),
        "seed": seed,
    }


def evaluate_r5_scorer(
    name: str,
    window_aggregation: str,
    episode_aggregation: str,
    episode_records: list[EpisodeRecord],
    episode_scores: dict[str, float],
    *,
    n_bootstrap: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    """Compute R5 metrics for one scorer on the identical episode manifest.

    Args:
        name: Scorer name (e.g. ``"seed43_lewm"``, ``"baseline_frame_diff"``).
        window_aggregation: How transition scores were combined within a window.
        episode_aggregation: How window scores were combined within an episode.
        episode_records: Full R5 episode manifest.
        episode_scores: episode_id → scalar score.
        n_bootstrap: Number of bootstrap iterations.
        bootstrap_seed: RNG seed for bootstrap.

    Returns:
        Dict with primary metrics, secondary metrics, and CI bounds.
    """
    calibration_records = [r for r in episode_records if r.evaluation_role == "calibration_normal"]
    evaluation_records = [r for r in episode_records if r.evaluation_role == "evaluation"]

    calibration_scores = [episode_scores[r.episode_id] for r in calibration_records]
    if not calibration_scores:
        raise ValueError(f"{name}: no calibration_normal episodes.")
    threshold = _percentile_linear(calibration_scores, 0.95)

    eval_labels = [int(r.label.lower() == "buggy") for r in evaluation_records]
    eval_scores = [episode_scores[r.episode_id] for r in evaluation_records]

    if not eval_labels or not any(eval_labels) or all(eval_labels):
        raise ValueError(f"{name}: evaluation requires both normal and buggy episodes.")

    predictions = [int(s >= threshold) for s in eval_scores]
    f1_metrics = binary_metrics(eval_labels, predictions)
    metric_auprc = average_precision(eval_labels, eval_scores)
    metric_auroc = auroc(eval_labels, eval_scores)
    if metric_auroc is None or metric_auprc is None:
        raise ValueError(f"{name}: produced undefined primary metrics.")

    fpr_95 = fpr_at_tpr(eval_labels, eval_scores, target_tpr=0.95)

    eval_rows = [
        {
            "episode_id": r.episode_id,
            "label": int(r.label.lower() == "buggy"),
            "score": episode_scores[r.episode_id],
        }
        for r in evaluation_records
    ]
    ci = _bootstrap_primary_cis(
        eval_rows,
        n_bootstrap=n_bootstrap,
        seed=bootstrap_seed,
    )

    return {
        "scorer": name,
        "window_aggregation": window_aggregation,
        "episode_aggregation": episode_aggregation,
        "auroc": metric_auroc,
        "auprc": metric_auprc,
        "auroc_ci_lower": ci["auroc"]["lower"],
        "auroc_ci_upper": ci["auroc"]["upper"],
        "auprc_ci_lower": ci["auprc"]["lower"],
        "auprc_ci_upper": ci["auprc"]["upper"],
        "bootstrap": ci,
        "threshold": threshold,
        "threshold_percentile": 95,
        "threshold_source": "calibration_normal_p95",
        "f1": f1_metrics["f1"],
        "precision": f1_metrics["precision"],
        "recall": f1_metrics["recall"],
        "fpr_at_95tpr": fpr_95,
        "calibration_episode_ids": sorted(r.episode_id for r in calibration_records),
        "calibration_episode_count": len(calibration_records),
        "episode_count": len(evaluation_records),
        "positive_episode_count": sum(eval_labels),
        "negative_episode_count": len(eval_labels) - sum(eval_labels),
        **{k: v for k, v in f1_metrics.items() if k not in {"f1", "precision", "recall"}},
    }


def run_r5_episode_eval(
    *,
    manifest_path: Path,
    lewm_scores_by_name: dict[str, Path],
    baseline_scores_path: Path,
    output_dir: Path,
    lewm_window_aggregations: tuple[str, ...] = ("mse_max", "l2_max"),
    episode_aggregations: tuple[str, ...] = ("max",),
    n_bootstrap: int = 1000,
    bootstrap_seed: int = 42,
) -> dict[str, Any]:
    """Full R5 episode-level evaluation orchestration.

    This function:
    1. Reads the window manifest and groups into episode records.
    2. For each (LeWM scorer, window aggregation, episode aggregation), computes
       episode-level scores and metrics.
    3. For each baseline (frame_diff, feature_distance) and episode aggregation,
       does the same.
    4. Writes provenance-bound output artifacts.
    5. Returns the full result dict.

    No locked-test path is accepted at any point.
    """
    _locked_guard(manifest_path)
    _locked_guard(baseline_scores_path)
    for name, path in lewm_scores_by_name.items():
        _locked_guard(path)

    window_manifest_rows = read_csv_rows(manifest_path)
    if not window_manifest_rows:
        raise ValueError("Window manifest is empty.")
    baseline_rows = read_csv_rows(baseline_scores_path)

    episode_records = build_episode_manifest(window_manifest_rows)
    validate_episode_manifest(episode_records)

    output_dir.mkdir(parents=True, exist_ok=True)
    episode_manifest_path = write_csv_rows(
        output_dir / "r5_episode_manifest.csv",
        [r.to_csv_dict() for r in episode_records],
        R5_EPISODE_MANIFEST_FIELDS,
    )

    scorer_results: list[dict[str, Any]] = []

    for scorer_name, lewm_path in sorted(lewm_scores_by_name.items()):
        lewm_rows = read_csv_rows(lewm_path)
        for win_agg in lewm_window_aggregations:
            window_scores = extract_lewm_window_scores(lewm_rows, win_agg)
            for ep_agg in episode_aggregations:
                episode_scores = aggregate_window_to_episode(
                    episode_records,
                    window_manifest_rows,
                    window_scores,
                    ep_agg,
                )
                result = evaluate_r5_scorer(
                    scorer_name,
                    window_aggregation=win_agg,
                    episode_aggregation=ep_agg,
                    episode_records=episode_records,
                    episode_scores=episode_scores,
                    n_bootstrap=n_bootstrap,
                    bootstrap_seed=bootstrap_seed,
                )
                scorer_results.append(result)

    for baseline_field in ("frame_diff", "feature_distance"):
        baseline_name = f"baseline_{baseline_field}"
        window_scores = extract_baseline_window_scores(baseline_rows, baseline_field)
        for ep_agg in episode_aggregations:
            episode_scores = aggregate_window_to_episode(
                episode_records,
                window_manifest_rows,
                window_scores,
                ep_agg,
            )
            result = evaluate_r5_scorer(
                baseline_name,
                window_aggregation="n/a",
                episode_aggregation=ep_agg,
                episode_records=episode_records,
                episode_scores=episode_scores,
                n_bootstrap=n_bootstrap,
                bootstrap_seed=bootstrap_seed,
            )
            scorer_results.append(result)

    comparison_path = write_csv_rows(
        output_dir / "r5_comparison.csv",
        scorer_results,
        R5_COMPARISON_FIELDS,
    )

    calibration_episode_ids = sorted(
        r.episode_id for r in episode_records if r.evaluation_role == "calibration_normal"
    )
    evaluation_episode_ids = sorted(
        r.episode_id for r in episode_records if r.evaluation_role == "evaluation"
    )
    buggy_episode_ids = sorted(r.episode_id for r in episode_records if r.label.lower() == "buggy")

    payload: dict[str, Any] = {
        "status": "r5_episode_evaluated",
        "protocol": "identical_nonlocked_episode_level_evaluation",
        "primary_metrics": ["auroc", "auprc"],
        "secondary_metrics": ["f1_at_calibration_normal_p95", "fpr_at_95tpr"],
        "ci": "95_grouped_episode_bootstrap",
        "episode_counts": {
            "total": len(episode_records),
            "calibration_normal": len(calibration_episode_ids),
            "evaluation_total": len(evaluation_episode_ids),
            "evaluation_buggy": len(buggy_episode_ids),
            "evaluation_normal": len(evaluation_episode_ids) - len(buggy_episode_ids),
        },
        "calibration_episode_ids": calibration_episode_ids,
        "buggy_episode_ids": buggy_episode_ids,
        "evaluation_protocol": {
            "lewm_window_aggregations": list(lewm_window_aggregations),
            "episode_aggregations": list(episode_aggregations),
            "threshold_source": "calibration_normal_p95",
            "n_bootstrap": n_bootstrap,
            "bootstrap_seed": bootstrap_seed,
        },
        "scorer_names": sorted(lewm_scores_by_name.keys()),
        "metrics": {
            f"{r['scorer']}/{r['window_aggregation']}/{r['episode_aggregation']}": r
            for r in scorer_results
        },
        "manifest_sha256": sha256_file(manifest_path),
        "baseline_scores_sha256": sha256_file(baseline_scores_path),
        "lewm_scores_sha256": {
            name: sha256_file(path) for name, path in sorted(lewm_scores_by_name.items())
        },
        "episode_manifest_sha256": sha256_file(episode_manifest_path),
        "comparison_sha256": sha256_file(comparison_path),
        "environment": runtime_provenance(include_lewm=False),
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "pilot_limitations": [
            "Window rows within an episode are correlated; episode-level evaluation "
            "reduces but does not eliminate this.",
            "Multi-seed evidence represents Kaggle GPU profiles, not fully reproduced "
            "independent training runs until R4 artifacts are artifact-backed.",
            "These metrics do not support claims of broad generalization or temporal localization.",
        ],
    }

    results_path = output_dir / "r5_episode_eval.json"
    import json

    results_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["results_path"] = str(results_path)
    payload["episode_manifest_path"] = str(episode_manifest_path)
    payload["comparison_path"] = str(comparison_path)
    return payload
