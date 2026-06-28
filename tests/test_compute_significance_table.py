from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.compute_significance_table import (
    compute_significance,
    main,
    render_latex_row,
)


def _write_scores(path: Path, rows: list[tuple[str, float, int]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source", "score", "label"])
        for source, score, label in rows:
            writer.writerow([source, score, label])


def _separable_pair(tmp_path: Path) -> tuple[Path, Path]:
    # LeWM perfectly separates positives (high) from negatives (low).
    lewm = [(f"ep{i}", 0.9 + 0.01 * i, 1) for i in range(6)]
    lewm += [(f"ep{i}", 0.1 + 0.01 * i, 0) for i in range(6, 12)]
    # Baseline barely separates (overlapping scores).
    baseline = [(f"ep{i}", 0.55 + 0.01 * i, 1) for i in range(6)]
    baseline += [(f"ep{i}", 0.50 + 0.01 * i, 0) for i in range(6, 12)]
    lewm_path = tmp_path / "lewm.csv"
    baseline_path = tmp_path / "baseline.csv"
    _write_scores(lewm_path, lewm)
    _write_scores(baseline_path, baseline)
    return lewm_path, baseline_path


def test_compute_significance_basic(tmp_path: Path):
    lewm_path, baseline_path = _separable_pair(tmp_path)
    summary = compute_significance(lewm_path, baseline_path, n_bootstrap=200, seed=1)
    assert summary["auroc_lewm"] == pytest.approx(1.0)
    assert summary["auroc_lewm"] >= summary["auroc_baseline"]
    assert summary["delta_auroc_point"] is not None
    assert summary["n_evaluation_episodes"] == 12
    # safe_wording must always be a non-empty defensible phrase
    assert "separation" in summary["safe_wording"] or "outperforms" in summary["safe_wording"]


def test_label_mismatch_is_rejected(tmp_path: Path):
    lewm_path = tmp_path / "lewm.csv"
    baseline_path = tmp_path / "baseline.csv"
    _write_scores(lewm_path, [("ep0", 0.9, 1), ("ep1", 0.1, 0)])
    _write_scores(baseline_path, [("ep0", 0.5, 0), ("ep1", 0.4, 0)])
    with pytest.raises(ValueError, match="Label mismatch"):
        compute_significance(lewm_path, baseline_path, n_bootstrap=10)


def test_missing_group_is_rejected(tmp_path: Path):
    lewm_path = tmp_path / "lewm.csv"
    baseline_path = tmp_path / "baseline.csv"
    _write_scores(lewm_path, [("ep0", 0.9, 1), ("ep1", 0.1, 0)])
    _write_scores(baseline_path, [("ep0", 0.5, 1)])
    with pytest.raises(ValueError, match="missing in baseline"):
        compute_significance(lewm_path, baseline_path, n_bootstrap=10)


def test_render_latex_row(tmp_path: Path):
    lewm_path, baseline_path = _separable_pair(tmp_path)
    summary = compute_significance(lewm_path, baseline_path, n_bootstrap=100, seed=2)
    row = render_latex_row(summary, "LeWM", "feature\\_distance")
    assert row.endswith(r"\\")
    assert "LeWM vs feature" in row


def test_main_writes_json(tmp_path: Path, capsys):
    lewm_path, baseline_path = _separable_pair(tmp_path)
    output = tmp_path / "sig.json"
    code = main(
        [
            "--lewm-scores",
            str(lewm_path),
            "--baseline-scores",
            str(baseline_path),
            "--n-bootstrap",
            "100",
            "--output",
            str(output),
        ]
    )
    assert code == 0
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "significant" in payload
    assert "LaTeX significance row" in capsys.readouterr().out
