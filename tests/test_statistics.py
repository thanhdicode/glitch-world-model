import pytest

from glitch_detection.statistics import (
    _metric,
    bootstrap_metric_ci,
    delong_auroc_test,
    paired_bootstrap_delta,
)
from scripts.evaluate_tempglitch_locked_test import write_locked_metrics_markdown

ROWS = [
    {"source": "n1", "pair_id_heuristic": "p1", "label": 0, "score": 0.1},
    {"source": "p1", "pair_id_heuristic": "p1", "label": 1, "score": 0.9},
    {"source": "n2", "pair_id_heuristic": "p2", "label": 0, "score": 0.2},
    {"source": "p2", "pair_id_heuristic": "p2", "label": 1, "score": 0.8},
]


def test_bootstrap_auroc_ci_is_deterministic_and_reports_metadata():
    first = bootstrap_metric_ci(ROWS, "auroc", n_bootstrap=100, seed=42, group_key="source")
    second = bootstrap_metric_ci(ROWS, "auroc", n_bootstrap=100, seed=42, group_key="source")

    assert first == second
    assert first["point"] == 1.0
    assert first["lower"] <= first["mean"] <= first["upper"]
    assert first["valid_bootstrap_count"] < 100
    assert first["n_bootstrap"] == 100
    assert first["seed"] == 42
    assert first["group_key"] == "source"
    assert first["confidence_level"] == 0.95


def test_bootstrap_f1_ci_supports_pair_level_resampling():
    result = bootstrap_metric_ci(
        ROWS,
        "f1",
        n_bootstrap=50,
        seed=7,
        group_key="pair_id_heuristic",
        threshold=0.5,
    )

    assert result["point"] == 1.0
    assert result["valid_bootstrap_count"] == 50
    assert result["group_key"] == "pair_id_heuristic"


def test_delong_auroc_test_reports_known_auroc_gap():
    labels = [1, 1, 1, 0, 0, 0]
    perfect = [0.9, 0.8, 0.7, 0.6, 0.2, 0.1]
    weaker = [0.95, 0.4, 0.3, 0.85, 0.2, 0.1]

    result = delong_auroc_test(labels, perfect, weaker)

    assert result["auroc_a"] == pytest.approx(1.0)
    assert result["auroc_b"] == pytest.approx(7 / 9)
    assert result["z"] > 0
    assert 0.0 <= result["p_value"] <= 1.0


def test_paired_bootstrap_delta_is_deterministic_for_same_group_resamples():
    rows_a = [
        {"source": "ep1", "label": 0, "score": 0.1},
        {"source": "ep2", "label": 0, "score": 0.2},
        {"source": "ep3", "label": 1, "score": 0.8},
        {"source": "ep4", "label": 1, "score": 0.9},
    ]
    rows_b = [
        {"source": "ep1", "label": 0, "score": 0.3},
        {"source": "ep2", "label": 0, "score": 0.4},
        {"source": "ep3", "label": 1, "score": 0.7},
        {"source": "ep4", "label": 1, "score": 0.6},
    ]

    first = paired_bootstrap_delta(rows_a, rows_b, "auroc", seed=11, n_bootstrap=40)
    second = paired_bootstrap_delta(rows_a, rows_b, "auroc", seed=11, n_bootstrap=40)

    assert first == second
    assert first["point_delta"] == pytest.approx(0.0)
    assert 0 < first["valid_bootstrap_count"] <= 40
    assert first["group_key"] == "source"


@pytest.mark.parametrize(
    ("metric_name", "expected"),
    [
        ("auprc", 1.0),
        ("balanced_accuracy", 1.0),
        ("mcc", 1.0),
    ],
)
def test_metric_supports_new_branches(metric_name, expected):
    threshold = 0.5 if metric_name in {"balanced_accuracy", "mcc"} else None
    assert _metric(ROWS, metric_name, threshold) == pytest.approx(expected)


def test_locked_metrics_markdown_handles_undefined_auroc_ci(tmp_path):
    payload = {
        "selection_split": "validation",
        "scorer": "demo",
        "aggregation": "mean",
        "threshold": 0.5,
        "evaluated_config_count": 1,
        "test_metrics": {"auroc": None, "f1": 0.0},
        "confidence_intervals": {
            "auroc": {
                "point": None,
                "lower": None,
                "upper": None,
                "valid_bootstrap_count": 0,
                "n_bootstrap": 10,
                "group_key": "source",
            }
        },
    }

    path = write_locked_metrics_markdown(payload, tmp_path / "metrics.md")

    assert "n/a" in path.read_text(encoding="utf-8")
