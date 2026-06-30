# TempGlitch Selection Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a no-GPU audit/reporting helper that ranks validated TempGlitch comparison rows and prevents confusion between window scorers and episode aggregations.

**Architecture:** Add one focused script under `scripts/` that parses comparison CSV plus optional metrics/provenance JSON, validates safety flags, ranks top rows, and emits JSON or Markdown summaries. Add focused tests with tiny synthetic fixtures, then use the helper to write one evidence audit report under `docs/research/`.

**Tech Stack:** Python standard library (`argparse`, `csv`, `json`, `math`, `dataclasses`, `pathlib`), pytest, existing paper/claim registry Markdown/LaTeX files.

---

## File Structure

- Create `scripts/summarize_tempglitch_selection.py`
  - Responsibility: validate and summarize comparison-row rankings from existing artifacts.
  - Public functions: `load_comparison_rows`, `load_safety_metadata`, `summarize_selection`, `render_markdown`.
- Create `tests/test_summarize_tempglitch_selection.py`
  - Responsibility: synthetic fixture tests for ranking, validation, guardrails, and safety metadata.
- Create `docs/research/130_tempglitch_selection_reporting_audit_2026_07_01.md`
  - Responsibility: record the no-GPU audit outcome and exact best rows from validated artifacts.
- Modify `docs/context/LAST_HANDOFF.md`
  - Responsibility: update handoff with completed A+B audit/reporting work and checks.
- Modify paper or claim files only if the audit reveals stale wording:
  - `paper/main.tex`
  - `paper/sections/*.tex`
  - `paper/tables/*.tex`
  - `docs/research/16_claim_registry.md`

## Task 1: Write Failing Tests For Selection Summary

**Files:**
- Create: `tests/test_summarize_tempglitch_selection.py`
- Create in Task 2: `scripts/summarize_tempglitch_selection.py`

- [ ] **Step 1: Add synthetic comparison and metadata fixtures**

Create `tests/test_summarize_tempglitch_selection.py` with this initial content:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.summarize_tempglitch_selection import (
    SelectionSummaryError,
    load_comparison_rows,
    load_safety_metadata,
    render_markdown,
    summarize_selection,
)


HEADER = (
    "method_family,method,window_scorer,seed,episode_aggregation,threshold_source,"
    "auroc,auprc,f1,precision,recall,balanced_accuracy,fpr_at_95_tpr,"
    "evaluation_episode_count,positive_episode_count,negative_episode_count,"
    "auroc_ci_lower,auroc_ci_upper,f1_ci_lower,f1_ci_upper\n"
)


def write_comparison(path: Path, rows: list[str]) -> None:
    path.write_text(HEADER + "".join(rows), encoding="utf-8")


def test_summarize_selection_ranks_by_metrics_and_preserves_axes(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.csv"
    write_comparison(
        comparison,
        [
            "lewm,lewm,lewm_l2_max,44,mean,calibration_normal_p95,"
            "0.7159,0.8026,0.7143,0.75,0.6818,0.6326,0.75,34,22,12,0.5349,0.8770,0.5854,0.8293\n",
            "baseline,feature_distance,feature_distance,,top2_mean,calibration_normal_p95,"
            "0.6136,0.7310,0.1600,0.6667,0.0909,0.5038,0.8333,34,22,12,0.4636,0.7545,0,0.3575\n",
            "lewm,lewm,lewm_l2_max,44,max,calibration_normal_p95,"
            "0.6174,0.7299,0.6500,0.65,0.65,0.55,0.9167,34,22,12,0.4014,0.8179,0.4516,0.8\n",
        ],
    )

    rows = load_comparison_rows(comparison)
    summary = summarize_selection(rows, top_k=2)

    assert summary["row_count"] == 3
    assert summary["best_by_metric"]["auroc"]["window_scorer"] == "lewm_l2_max"
    assert summary["best_by_metric"]["auroc"]["episode_aggregation"] == "mean"
    assert summary["best_by_metric"]["auroc"]["auroc"] == pytest.approx(0.7159)
    assert summary["top_by_metric"]["auroc"][1]["method"] == "feature_distance"
    assert summary["axis_guardrail"] == (
        "window_scorer and episode_aggregation are separate axes; "
        "lewm_l2_max is a window scorer, not episode-level max aggregation."
    )


def test_render_markdown_names_window_and_episode_axes(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.csv"
    write_comparison(
        comparison,
        [
            "lewm,lewm,lewm_l2_max,44,mean,calibration_normal_p95,"
            "0.7159,0.8026,0.7143,0.75,0.6818,0.6326,0.75,34,22,12,0.5349,0.8770,0.5854,0.8293\n",
        ],
    )

    markdown = render_markdown(
        summarize_selection(load_comparison_rows(comparison), top_k=1),
        title="Synthetic TempGlitch Audit",
    )

    assert "# Synthetic TempGlitch Audit" in markdown
    assert "`lewm_l2_max`" in markdown
    assert "episode `mean`" in markdown
    assert "window scorer" in markdown


def test_missing_required_column_fails_closed(tmp_path: Path) -> None:
    comparison = tmp_path / "bad.csv"
    comparison.write_text("method,auroc\nlewm,0.5\n", encoding="utf-8")

    with pytest.raises(SelectionSummaryError, match="missing required column"):
        load_comparison_rows(comparison)


def test_non_finite_metric_fails_closed(tmp_path: Path) -> None:
    comparison = tmp_path / "bad.csv"
    write_comparison(
        comparison,
        [
            "lewm,lewm,lewm_l2_max,44,mean,calibration_normal_p95,"
            "nan,0.8026,0.7143,0.75,0.6818,0.6326,0.75,34,22,12,0.5349,0.8770,0.5854,0.8293\n",
        ],
    )

    with pytest.raises(SelectionSummaryError, match="non-finite metric"):
        load_comparison_rows(comparison)


def test_locked_test_metadata_fails_closed(tmp_path: Path) -> None:
    metadata = tmp_path / "metrics.json"
    metadata.write_text(json.dumps({"locked_test_scored": True}), encoding="utf-8")

    with pytest.raises(SelectionSummaryError, match="locked_test_scored"):
        load_safety_metadata(metadata)
```

- [ ] **Step 2: Run the new tests and verify they fail because the script is missing**

Run:

```powershell
python -m pytest tests/test_summarize_tempglitch_selection.py -q
```

Expected: collection fails with `ModuleNotFoundError` or import failure for `scripts.summarize_tempglitch_selection`.

## Task 2: Implement The Selection Summary Helper

**Files:**
- Create: `scripts/summarize_tempglitch_selection.py`
- Test: `tests/test_summarize_tempglitch_selection.py`

- [ ] **Step 1: Add the script implementation**

Create `scripts/summarize_tempglitch_selection.py` with this content:

```python
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = (
    "method_family",
    "method",
    "window_scorer",
    "seed",
    "episode_aggregation",
    "threshold_source",
    "auroc",
    "auprc",
    "f1",
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
)
NUMERIC_COLUMNS = (
    "auroc",
    "auprc",
    "f1",
    "precision",
    "recall",
    "balanced_accuracy",
    "fpr_at_95_tpr",
    "auroc_ci_lower",
    "auroc_ci_upper",
    "f1_ci_lower",
    "f1_ci_upper",
)
INTEGER_COLUMNS = (
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
)
SAFETY_FLAGS = (
    "validation_buggy_used_for_fit_select",
    "locked_test_materialized",
    "locked_test_scored",
)
AXIS_GUARDRAIL = (
    "window_scorer and episode_aggregation are separate axes; "
    "lewm_l2_max is a window scorer, not episode-level max aggregation."
)


class SelectionSummaryError(ValueError):
    """Raised when a comparison artifact is unsafe or malformed."""


def _parse_float(row: dict[str, str], column: str, row_number: int) -> float | None:
    value = row.get(column, "")
    if value == "":
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise SelectionSummaryError(
            f"row {row_number}: non-numeric metric {column}={value!r}"
        ) from exc
    if not math.isfinite(parsed):
        raise SelectionSummaryError(f"row {row_number}: non-finite metric {column}={value!r}")
    return parsed


def _parse_int(row: dict[str, str], column: str, row_number: int) -> int | None:
    value = row.get(column, "")
    if value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise SelectionSummaryError(
            f"row {row_number}: non-integer count {column}={value!r}"
        ) from exc


def load_comparison_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise SelectionSummaryError(f"missing required column(s): {', '.join(missing)}")
        rows: list[dict[str, Any]] = []
        for row_number, raw in enumerate(reader, start=2):
            parsed: dict[str, Any] = {key: raw.get(key, "") for key in fieldnames}
            for column in NUMERIC_COLUMNS:
                if column in fieldnames:
                    parsed[column] = _parse_float(raw, column, row_number)
            for column in INTEGER_COLUMNS:
                if column in fieldnames:
                    parsed[column] = _parse_int(raw, column, row_number)
            rows.append(parsed)
    if not rows:
        raise SelectionSummaryError(f"comparison CSV has no rows: {path}")
    return rows


def _flag_is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_safety_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    metadata = json.loads(path.read_text(encoding="utf-8-sig"))
    for flag in SAFETY_FLAGS:
        if _flag_is_true(metadata.get(flag, False)):
            raise SelectionSummaryError(f"{flag} must be false for reporting-safe summaries.")
    return {flag: bool(metadata.get(flag, False)) for flag in SAFETY_FLAGS if flag in metadata}


def _display_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "method_family",
        "method",
        "window_scorer",
        "seed",
        "episode_aggregation",
        "threshold_source",
        "auroc",
        "auprc",
        "f1",
        "precision",
        "recall",
        "balanced_accuracy",
        "fpr_at_95_tpr",
        "evaluation_episode_count",
        "positive_episode_count",
        "negative_episode_count",
        "auroc_ci_lower",
        "auroc_ci_upper",
        "f1_ci_lower",
        "f1_ci_upper",
    )
    return {key: row.get(key) for key in keys if key in row}


def summarize_selection(
    rows: list[dict[str, Any]],
    *,
    top_k: int = 5,
    safety_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if top_k < 1:
        raise SelectionSummaryError("top_k must be positive.")
    metrics = ("auroc", "auprc", "f1")
    top_by_metric: dict[str, list[dict[str, Any]]] = {}
    for metric in metrics:
        top_rows = sorted(rows, key=lambda row: float(row[metric]), reverse=True)[:top_k]
        top_by_metric[metric] = [_display_row(row) for row in top_rows]
    return {
        "status": "selection_summary_complete",
        "row_count": len(rows),
        "axis_guardrail": AXIS_GUARDRAIL,
        "safety_metadata": safety_metadata or {},
        "best_by_metric": {metric: values[0] for metric, values in top_by_metric.items()},
        "top_by_metric": top_by_metric,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return ""
    return str(value)


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    best = summary["best_by_metric"]["auroc"]
    lines = [
        f"# {title}",
        "",
        "## Guardrail",
        "",
        summary["axis_guardrail"],
        "",
        "## Best AUROC Row",
        "",
        (
            f"- Method: `{best['method']}`"
            f" seed `{best.get('seed') or 'n/a'}`"
            f" window scorer `{best['window_scorer']}`"
            f" episode `{best['episode_aggregation']}`"
        ),
        f"- AUROC: `{_fmt(best['auroc'])}`",
        f"- AUPRC: `{_fmt(best.get('auprc'))}`",
        f"- F1: `{_fmt(best.get('f1'))}`",
        f"- FPR@95TPR: `{_fmt(best.get('fpr_at_95_tpr'))}`",
        f"- Evaluation support: `{best.get('negative_episode_count')}` normal-negative / "
        f"`{best.get('positive_episode_count')}` buggy-positive episodes",
        "",
        "## Top Rows By Metric",
        "",
    ]
    for metric, rows in summary["top_by_metric"].items():
        lines.extend(
            [
                f"### {metric.upper()}",
                "",
                "| Rank | Method | Seed | Window scorer | Episode aggregation | Value |",
                "| ---: | --- | --- | --- | --- | ---: |",
            ]
        )
        for index, row in enumerate(rows, start=1):
            lines.append(
                f"| {index} | `{row['method']}` | `{row.get('seed') or 'n/a'}` | "
                f"`{row['window_scorer']}` | `{row['episode_aggregation']}` | "
                f"{_fmt(row[metric])} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize validated TempGlitch comparison row selection."
    )
    parser.add_argument("--comparison-csv", required=True, type=Path)
    parser.add_argument("--metadata-json", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--title", default="TempGlitch Selection Reporting Audit")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    safety_metadata = load_safety_metadata(args.metadata_json)
    summary = summarize_selection(
        load_comparison_rows(args.comparison_csv),
        top_k=args.top_k,
        safety_metadata=safety_metadata,
    )
    if args.format == "markdown":
        rendered = render_markdown(summary, title=args.title)
    else:
        rendered = json.dumps(summary, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m pytest tests/test_summarize_tempglitch_selection.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Commit the helper and tests**

Run:

```powershell
git add scripts/summarize_tempglitch_selection.py tests/test_summarize_tempglitch_selection.py
git commit -m "test: add TempGlitch selection summary helper"
```

Expected: commit succeeds with only the helper and test files staged.

## Task 3: Run The Helper On Validated Artifacts

**Files:**
- Read: `outputs/r5_tempglitch_identical_episode/r5_comparison.csv`
- Read: `outputs/r5_tempglitch_identical_episode/r5_metrics.json`
- Read: `outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv`
- Read: `outputs/tempglitch_followup_pair_disjoint/followup_metrics.json`
- Read if present: `C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_comparison.csv`
- Read if present: `C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_metrics.json`
- Create: `.test-tmp/tempglitch_selection_audit/`

- [ ] **Step 1: Summarize R5 identical-episode rows**

Run:

```powershell
python scripts/summarize_tempglitch_selection.py `
  --comparison-csv outputs/r5_tempglitch_identical_episode/r5_comparison.csv `
  --metadata-json outputs/r5_tempglitch_identical_episode/r5_metrics.json `
  --format markdown `
  --title "R5 TempGlitch Selection Audit" `
  --output .test-tmp/tempglitch_selection_audit/r5_selection.md
```

Expected: command exits 0 and writes `.test-tmp/tempglitch_selection_audit/r5_selection.md`.

- [ ] **Step 2: Summarize pair-disjoint follow-up rows**

Run:

```powershell
python scripts/summarize_tempglitch_selection.py `
  --comparison-csv outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv `
  --metadata-json outputs/tempglitch_followup_pair_disjoint/followup_metrics.json `
  --format markdown `
  --title "TempGlitch Pair-Disjoint Selection Audit" `
  --output .test-tmp/tempglitch_selection_audit/followup_selection.md
```

Expected: command exits 0 and writes `.test-tmp/tempglitch_selection_audit/followup_selection.md`.

- [ ] **Step 3: Summarize K-A expanded rows when local download is present**

Run:

```powershell
if (Test-Path "C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_comparison.csv") {
  python scripts/summarize_tempglitch_selection.py `
    --comparison-csv "C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_comparison.csv" `
    --metadata-json "C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_metrics.json" `
    --format markdown `
    --title "K-A Expanded TempGlitch Selection Audit" `
    --output .test-tmp/tempglitch_selection_audit/ka_expanded_selection.md
}
```

Expected when the local download exists: command exits 0 and writes `.test-tmp/tempglitch_selection_audit/ka_expanded_selection.md`.

## Task 4: Write The No-GPU Audit Report

**Files:**
- Create: `docs/research/130_tempglitch_selection_reporting_audit_2026_07_01.md`
- Read: `.test-tmp/tempglitch_selection_audit/*.md`
- Read: `docs/research/101_tempglitch_followup_results.md`
- Read: `docs/research/129_ka_tempglitch_expanded_intake_2026_06_30.md`
- Read: `docs/research/16_claim_registry.md`
- Read: `paper/main.tex`
- Read: `paper/sections/07_experiments.tex`
- Read: `paper/sections/08_results.tex`

- [ ] **Step 1: Inspect generated summaries and paper text**

Run:

```powershell
Get-Content .test-tmp/tempglitch_selection_audit/r5_selection.md
Get-Content .test-tmp/tempglitch_selection_audit/followup_selection.md
if (Test-Path .test-tmp/tempglitch_selection_audit/ka_expanded_selection.md) {
  Get-Content .test-tmp/tempglitch_selection_audit/ka_expanded_selection.md
}
rg -n "lewm_l2_max|episode.*max|0\\.7159|0\\.700544|0\\.6969|window scorer|episode aggregation" paper docs/research/16_claim_registry.md
```

Expected: generated summaries identify `lewm_l2_max` as the best TempGlitch window scorer and episode `mean` as the best-row episode aggregation for the inspected TempGlitch artifacts.

- [ ] **Step 2: Create the audit report**

Create `docs/research/130_tempglitch_selection_reporting_audit_2026_07_01.md` with this structure and the values observed from the generated summaries:

```markdown
# 130 - TempGlitch Selection Reporting Audit 2026-07-01

## Status

No-GPU audit complete. The current TempGlitch evidence already contains the relevant max-style
LeWM window scorers, so the immediate fix is reporting hardening rather than rescoring or
retraining.

## Key Finding

`lewm_l2_max` is a window scorer. It is distinct from episode-level `max` aggregation. In the
validated TempGlitch artifacts inspected for this audit, the best AUROC rows use `lewm_l2_max`
with episode aggregation `mean`.

## Inspected Artifacts

| Artifact family | Comparison artifact | Safety metadata | Best AUROC row |
| --- | --- | --- | --- |
| R5 identical episode | `outputs/r5_tempglitch_identical_episode/r5_comparison.csv` | `outputs/r5_tempglitch_identical_episode/r5_metrics.json` | seed44 `lewm_l2_max`, episode `mean`, AUROC `0.69696969697` |
| Pair-disjoint follow-up | `outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv` | `outputs/tempglitch_followup_pair_disjoint/followup_metrics.json` | seed44 `lewm_l2_max`, episode `mean`, AUROC `0.715909090909` |
| K-A expanded follow-up | `C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_comparison.csv` | `C:\Users\ADMIN\Downloads\results (3)\tempglitch_followup_expanded\followup_metrics.json` | seed43 `lewm_l2_max`, episode `mean`, AUROC `0.700544` |

## Paper And Claim Registry Audit

- Claim C-091 already records the pair-disjoint TempGlitch best row as seed44 `lewm_l2_max`
  with mean episode aggregation.
- Claim C-118 already records the K-A expanded best row as seed43 `lewm_l2_max` with mean
  episode aggregation.
- Paper-facing text should continue to describe these as bounded, non-locked, validation-only
  observations with wide uncertainty and no broad superiority claim.

## Safety Boundary

- No GPU training was run.
- No window rescoring was run.
- No Kaggle action was taken.
- No locked-test materialization or scoring occurred.
- No output bundle, checkpoint, Lance dataset, raw data, cache, or credential was committed.

## Next Decision

Do not spend GPU on history-size or encoder changes until the K-C WOB binary intake status and
paper narrative gap are known. If a GPU lane opens later, combine history-size and encoder choices
into one controlled experiment family.
```

- [ ] **Step 3: Adjust paper or claim wording only if the audit finds stale text**

If the `rg` output from Step 1 shows a paper or claim sentence that says episode `max` is the best TempGlitch row, edit that exact sentence to say `lewm_l2_max` is the window scorer and episode `mean` is the best-row episode aggregation.

Run after edits:

```powershell
python scripts/check_claim_registry.py
```

Expected: command exits 0.

- [ ] **Step 4: Commit the audit report and any synchronized docs**

Run:

```powershell
git add docs/research/130_tempglitch_selection_reporting_audit_2026_07_01.md docs/research/16_claim_registry.md paper
git diff --cached --name-only
git commit -m "docs: audit TempGlitch selection reporting"
```

Expected: commit includes the audit report and only necessary paper/claim synchronization edits.

## Task 5: Update Context And Run Verification

**Files:**
- Modify: `docs/context/LAST_HANDOFF.md`
- May modify via generator: `docs/context/BOOT.md`, `docs/context/PROJECT_STATE.md`, `docs/context/NEXT_ACTION.md`, `docs/context/TASK_ROUTER.md`

- [ ] **Step 1: Update LAST_HANDOFF**

Edit `docs/context/LAST_HANDOFF.md` to include:

```markdown
Last completed task: TempGlitch selection reporting audit and helper
Commit: paste the SHA printed by `git rev-parse HEAD` after Task 4
Date: 2026-07-01T00:00:00+07:00

## What Changed

- Added a no-GPU TempGlitch selection summary helper that ranks comparison rows and distinguishes
  window scorers from episode aggregations.
- Added focused tests for ranking, malformed comparisons, non-finite metrics, and locked-test
  safety metadata.
- Wrote the TempGlitch selection reporting audit report.
- Confirmed the immediate issue is reporting hardening, not adding a missing TempGlitch scorer.

## Safety Status

- No GPU training, Kaggle launch, window rescoring, locked-test materialization, or locked-test
  scoring was performed.
- Output artifacts, checkpoints, Lance datasets, caches, credentials, and Kaggle files remain
  uncommitted.

## Next Recommended Task

- Continue with K-C WOB binary intake if the success tarball and SHA sidecar are available.
- Consider GPU retraining only after K-C status and paper narrative gaps are known.
```

Get the Task 4 commit SHA with:

```powershell
git rev-parse HEAD
```

- [ ] **Step 2: Refresh and validate context cache**

Run:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
```

Expected: both commands exit 0. If the cache generator changes context files, inspect and stage only relevant context files.

- [ ] **Step 3: Run focused verification**

Run:

```powershell
python -m pytest tests/test_summarize_tempglitch_selection.py tests/test_research_release_tools.py tests/test_context_cache.py -q
python -m ruff check scripts/summarize_tempglitch_selection.py tests/test_summarize_tempglitch_selection.py
python -m ruff format --check scripts/summarize_tempglitch_selection.py tests/test_summarize_tempglitch_selection.py
python scripts/check_claim_registry.py
python scripts/validate_research_release.py --ci
python scripts/doctor.py
```

Expected: all commands exit 0.

- [ ] **Step 4: Run full required checks if time allows**

Run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
```

Expected: all commands exit 0. If a command is skipped because runtime is too long or an external dependency is unavailable, record the skipped check in the final report.

- [ ] **Step 5: Commit context updates**

Run:

```powershell
git add docs/context
git diff --cached --name-only
git commit -m "docs: update context after TempGlitch reporting audit"
```

Expected: commit includes only context-cache and handoff changes.

## Self-Review

- Spec coverage: Tasks 1-2 implement the reporting helper and tests; Task 3 runs it on validated artifacts; Task 4 writes the audit report and synchronizes paper/claims if needed; Task 5 updates context and verifies.
- Placeholder scan: no unfinished-marker strings or undefined later-fill steps remain.
- Type consistency: the plan consistently uses `SelectionSummaryError`, `load_comparison_rows`, `load_safety_metadata`, `summarize_selection`, and `render_markdown`.
