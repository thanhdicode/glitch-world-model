import pytest

from glitch_detection.seed_aggregation import aggregate_seed_metrics


def test_aggregate_seed_metrics_reports_population_summary():
    result = aggregate_seed_metrics(
        [
            {"seed": 42, "auroc": 0.6, "f1": 0.5},
            {"seed": 43, "auroc": 0.8, "f1": 0.7},
            {"seed": 44, "auroc": 0.7, "f1": 0.6},
        ]
    )

    assert result["auroc"]["mean"] == pytest.approx(0.7)
    assert result["auroc"]["std"] == pytest.approx(0.08164965809277262)
    assert result["auroc"]["min"] == pytest.approx(0.6)
    assert result["auroc"]["max"] == pytest.approx(0.8)
    assert result["auroc"]["n_seeds"] == 3


def test_aggregate_seed_metrics_handles_single_seed_edge_case():
    result = aggregate_seed_metrics([{"seed": 42, "auroc": 0.75}])

    assert result["auroc"]["mean"] == pytest.approx(0.75)
    assert result["auroc"]["std"] == pytest.approx(0.0)
    assert result["auroc"]["min"] == pytest.approx(0.75)
    assert result["auroc"]["max"] == pytest.approx(0.75)
    assert result["auroc"]["n_seeds"] == 1
