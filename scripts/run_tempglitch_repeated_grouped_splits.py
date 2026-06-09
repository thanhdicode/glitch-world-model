from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from glitch_detection.manifest import read_manifest
from glitch_detection.model_selection import evaluate_locked_test, select_validation_config
from glitch_detection.pairs import pair_leakage_report
from glitch_detection.repeated_eval import (
    build_video_rows,
    clip_score_rows,
    fit_scorer_for_split,
    score_fitted_scorer,
    write_clip_scores_csv,
)
from glitch_detection.splits import (
    assign_grouped_video_splits,
    filter_labels_by_sources,
    filter_manifest_by_sources,
    validate_no_group_leakage,
    write_grouped_split_csv,
)
from glitch_detection.statistics import bootstrap_metric_ci
from glitch_detection.tempglitch import read_tempglitch_metadata
from glitch_detection.video_eval import AGGREGATIONS, calibrate_video_threshold, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORERS = ["frame_diff", "feature_distance", "mini_latent"]


def _require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")
    return path


def _clear_score_files(directory: Path) -> None:
    if not directory.is_dir():
        return
    for path in directory.glob("*_scores.csv"):
        path.unlink()


def _write_split_artifacts(
    seed_dir: Path,
    records: list[Any],
    seed: int,
) -> dict[str, Any]:
    split_path, generated_metadata_path = write_grouped_split_csv(
        seed_dir / "split.csv", records, seed=seed
    )
    split_metadata = json.loads(generated_metadata_path.read_text(encoding="utf-8"))
    split_metadata_path = seed_dir / "split_metadata.json"
    write_json(split_metadata, split_metadata_path)
    leakage = pair_leakage_report(records)
    leakage_path = write_json(leakage, seed_dir / "leakage_report.json")
    return {
        "split_path": split_path,
        "split_metadata_path": split_metadata_path,
        "leakage_report_path": leakage_path,
        "validation": validate_no_group_leakage(records),
    }


def _write_partitions(
    manifest_path: Path,
    labels_path: Path,
    seed_dir: Path,
    records: list[Any],
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    partition_dir = seed_dir / "partitions"
    for split in ["train", "validation", "test"]:
        sources = {row.source for row in records if row.split == split}
        paths[f"{split}_manifest"] = filter_manifest_by_sources(
            manifest_path, sources, partition_dir / f"{split}_manifest.csv"
        )
        paths[f"{split}_labels"] = filter_labels_by_sources(
            labels_path, sources, partition_dir / f"{split}_labels.csv"
        )
    return paths


def _format_metric(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.6g}"


def _write_locked_summary(payload: dict[str, Any], output_path: Path) -> Path:
    metrics = payload["test_metrics"]
    lines = [
        "# Phase 6D Locked Test Summary",
        "",
        f"- Seed: `{payload['seed']}`",
        f"- Selected config: `{payload['scorer']}/{payload['aggregation']}`",
        f"- Selection split: `{payload['selection_split']}`",
        f"- Evaluated test configurations: `{payload['evaluated_config_count']}`",
        f"- Test AUROC: `{_format_metric(metrics['auroc'])}`",
        f"- Test F1: `{_format_metric(metrics['f1'])}`",
        "",
        "| Metric | Point | 95% lower | 95% upper | Valid bootstrap / requested |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, ci in payload["confidence_intervals"].items():
        lines.append(
            f"| {name} | {_format_metric(ci['point'])} | {_format_metric(ci['lower'])} | "
            f"{_format_metric(ci['upper'])} | {ci['valid_bootstrap_count']} / "
            f"{ci['n_bootstrap']} |"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _metric_summary(runs: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    values = [
        float(run["locked_test"]["test_metrics"][metric])
        for run in runs
        if run["locked_test"]["test_metrics"].get(metric) is not None
    ]
    return {
        "metric": metric,
        "mean": mean(values) if values else None,
        "population_std": pstdev(values) if len(values) > 1 else 0.0 if values else None,
        "valid_seed_count": len(values),
    }


def _write_repeated_summary(payload: dict[str, Any], output_path: Path) -> Path:
    lines = [
        "# Phase 6D Repeated Grouped Summary",
        "",
        f"- Status: `{payload['status']}`",
        f"- Seeds completed: `{', '.join(str(seed) for seed in payload['seeds_completed'])}`",
        f"- Grouping mode: `{payload['grouping_mode']}`",
        f"- Dataset sample mode(s): `{', '.join(payload['dataset']['sample_modes'])}`",
        "",
        "| Seed | Cross-split groups | Selected config | Test AUROC | AUROC 95% CI | Test F1 | F1 95% CI |",
        "| ---: | ---: | --- | ---: | --- | ---: | --- |",
    ]
    for run in payload["runs"]:
        selected = run.get("selected_config")
        locked = run.get("locked_test")
        config = f"{selected['scorer']}/{selected['aggregation']}" if selected else "n/a"
        auroc = _format_metric(locked["test_metrics"]["auroc"]) if locked else "n/a"
        f1 = _format_metric(locked["test_metrics"]["f1"]) if locked else "n/a"
        auroc_ci = "n/a"
        f1_ci = "n/a"
        if locked:
            confidence_intervals = locked["confidence_intervals"]
            auroc_ci = (
                f"[{_format_metric(confidence_intervals['auroc']['lower'])}, "
                f"{_format_metric(confidence_intervals['auroc']['upper'])}]"
            )
            f1_ci = (
                f"[{_format_metric(confidence_intervals['f1']['lower'])}, "
                f"{_format_metric(confidence_intervals['f1']['upper'])}]"
            )
        lines.append(
            f"| {run['seed']} | {run['cross_split_group_count']} | {config} | {auroc} | "
            f"{auroc_ci} | {f1} | {f1_ci} |"
        )
    if payload.get("metric_summary"):
        lines.extend(
            [
                "",
                "These are selected-pipeline performance estimates, not per-scorer superiority "
                "comparisons.",
                "",
                "| Metric | Mean | Population std | Valid seeds |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for metric in ["auroc", "f1"]:
            row = payload["metric_summary"][metric]
            lines.append(
                f"| {metric} | {_format_metric(row['mean'])} | "
                f"{_format_metric(row['population_std'])} | {row['valid_seed_count']} |"
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def run_repeated_grouped_experiments(
    metadata_path: Path,
    manifest_path: Path,
    labels_path: Path,
    output_root: Path,
    seeds: list[int],
    scorers: list[str],
    aggregations: list[str],
    n_bootstrap: int,
    dry_run: bool,
    top_k: int = 3,
    declared_sample_mode: str | None = None,
) -> dict[str, Any]:
    _require_file(metadata_path, "TempGlitch metadata")
    _require_file(manifest_path, "combined manifest")
    _require_file(labels_path, "labels CSV")
    metadata_rows = read_tempglitch_metadata(metadata_path)
    manifest_records = read_manifest(manifest_path)
    runs: list[dict[str, Any]] = []

    for seed in seeds:
        seed_dir = output_root / f"seed_{seed}"
        split_records = assign_grouped_video_splits(metadata_rows, seed=seed)
        split_artifacts = _write_split_artifacts(seed_dir, split_records, seed)
        validation = split_artifacts["validation"]
        run: dict[str, Any] = {
            "seed": seed,
            "video_count": len(split_records),
            "group_count": validation["group_count"],
            "suspected_pair_count": validation["suspected_pair_count"],
            "cross_split_group_count": validation["cross_split_group_count"],
            "split_counts": {
                split: sum(row.split == split for row in split_records)
                for split in ["train", "validation", "test"]
            },
        }
        if dry_run:
            runs.append(run)
            continue

        partition_paths = _write_partitions(manifest_path, labels_path, seed_dir, split_records)
        validation_records = read_manifest(partition_paths["validation_manifest"])
        test_records = read_manifest(partition_paths["test_manifest"])
        _clear_score_files(seed_dir / "validation_scores")
        _clear_score_files(seed_dir / "test_scores")
        fitted_by_scorer = {
            scorer: fit_scorer_for_split(scorer, manifest_records, split_records)
            for scorer in scorers
        }
        write_json(
            [fitted_by_scorer[scorer].fit_metadata for scorer in scorers],
            seed_dir / "fit_metadata.json",
        )

        candidates: list[dict[str, Any]] = []
        for scorer in scorers:
            fitted = fitted_by_scorer[scorer]
            validation_clip_rows = clip_score_rows(
                validation_records, score_fitted_scorer(fitted, validation_records)
            )
            write_clip_scores_csv(
                validation_clip_rows, seed_dir / "validation_scores" / f"{scorer}_scores.csv"
            )
            for aggregation in aggregations:
                validation_video_rows = build_video_rows(
                    validation_clip_rows,
                    split_records,
                    "validation",
                    aggregation,
                    top_k,
                )
                candidates.append(
                    calibrate_video_threshold(validation_video_rows, aggregation, scorer)
                )

        selected = select_validation_config(candidates, seed=seed)
        selected["validation_candidate_count"] = len(candidates)
        write_json(selected, seed_dir / "selected_protocol_config.json")

        selected_fitted = fitted_by_scorer[str(selected["scorer"])]
        test_clip_rows = clip_score_rows(
            test_records, score_fitted_scorer(selected_fitted, test_records)
        )
        write_clip_scores_csv(
            test_clip_rows,
            seed_dir / "test_scores" / f"{selected['scorer']}_scores.csv",
        )
        test_video_rows = build_video_rows(
            test_clip_rows,
            split_records,
            "test",
            str(selected["aggregation"]),
            top_k,
        )
        locked = evaluate_locked_test(
            selected,
            {(str(selected["scorer"]), str(selected["aggregation"])): test_video_rows},
        )
        locked["seed"] = seed
        write_json(locked, seed_dir / "locked_test_metrics.json")
        locked["confidence_intervals"] = {
            "auroc": bootstrap_metric_ci(
                test_video_rows,
                "auroc",
                n_bootstrap=n_bootstrap,
                seed=seed,
                group_key="pair_id_heuristic",
            ),
            "f1": bootstrap_metric_ci(
                test_video_rows,
                "f1",
                n_bootstrap=n_bootstrap,
                seed=seed,
                group_key="pair_id_heuristic",
                threshold=float(selected["threshold"]),
            ),
        }
        write_json(locked, seed_dir / "locked_test_metrics_with_ci.json")
        _write_locked_summary(locked, seed_dir / "locked_test_summary.md")
        run["selected_config"] = selected
        run["locked_test"] = locked
        run["fit_metadata"] = [fitted_by_scorer[scorer].fit_metadata for scorer in scorers]
        runs.append(run)

    status = "dry-run only" if dry_run else "full run complete"
    metadata_sample_modes = sorted(
        {str(row["sample_mode"]) for row in metadata_rows if row.get("sample_mode")}
    )
    sample_modes = [declared_sample_mode] if declared_sample_mode else metadata_sample_modes
    payload: dict[str, Any] = {
        "status": status,
        "dataset": {
            "metadata_path": str(metadata_path),
            "video_count": len(metadata_rows),
            "sample_modes": sample_modes or ["unknown"],
            "sample_mode_source": (
                "declared-protocol"
                if declared_sample_mode
                else "metadata"
                if metadata_sample_modes
                else "unavailable"
            ),
            "dataset_revisions": sorted(
                {str(row.get("dataset_revision", "unknown")) for row in metadata_rows}
            ),
        },
        "grouping_mode": "pair_id_heuristic",
        "selection_policy": "validation AUROC; fallback validation F1",
        "locked_test_policy": "evaluate exactly one validation-selected config per seed",
        "bootstrap_policy": {
            "n_bootstrap": n_bootstrap,
            "group_key": "pair_id_heuristic",
            "confidence_level": 0.95,
        },
        "seeds_completed": [run["seed"] for run in runs],
        "runs": runs,
    }
    if not dry_run:
        payload["metric_summary"] = {
            "auroc": _metric_summary(runs, "auroc"),
            "f1": _metric_summary(runs, "f1"),
        }
    write_json(payload, output_root / "phase6d_repeated_summary.json")
    _write_repeated_summary(payload, output_root / "phase6d_repeated_summary.md")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repeated grouped TempGlitch evaluation.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=ROOT / "data" / "raw" / "tempglitch_phase3b" / "metadata.csv",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_phase3b" / "manifest.csv",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_phase3b" / "labels.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6d",
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--scorer", action="append", dest="scorers", default=None)
    parser.add_argument("--aggregation", nargs="+", default=list(AGGREGATIONS))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument(
        "--sample-mode",
        choices=["sequential", "random-stratified"],
        default=None,
        help="Declare the fixed subset sample mode when legacy metadata does not record it.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = run_repeated_grouped_experiments(
        metadata_path=args.metadata,
        manifest_path=args.manifest,
        labels_path=args.labels,
        output_root=args.output_root,
        seeds=args.seeds,
        scorers=args.scorers or list(DEFAULT_SCORERS),
        aggregations=args.aggregation,
        n_bootstrap=args.n_bootstrap,
        dry_run=args.dry_run,
        top_k=args.top_k,
        declared_sample_mode=args.sample_mode,
    )
    print(f"Phase 6D status: {summary['status']}")
    print(f"Seeds completed: {summary['seeds_completed']}")
    for run in summary["runs"]:
        line = f"seed {run['seed']}: leakage={run['cross_split_group_count']}"
        if run.get("selected_config"):
            selected = run["selected_config"]
            metrics = run["locked_test"]["test_metrics"]
            line += (
                f", selected={selected['scorer']}/{selected['aggregation']}, "
                f"AUROC={_format_metric(metrics['auroc'])}, F1={_format_metric(metrics['f1'])}"
            )
        print(line)
    if summary.get("metric_summary"):
        auroc = summary["metric_summary"]["auroc"]
        f1 = summary["metric_summary"]["f1"]
        print(
            f"Locked-test AUROC mean +/- std: {_format_metric(auroc['mean'])} +/- "
            f"{_format_metric(auroc['population_std'])}"
        )
        print(
            f"Locked-test F1 mean +/- std: {_format_metric(f1['mean'])} +/- "
            f"{_format_metric(f1['population_std'])}"
        )
    print(f"Output summary: {args.output_root / 'phase6d_repeated_summary.json'}")


if __name__ == "__main__":
    main()
