from __future__ import annotations

import pytest

from glitch_detection.r5_xgame_metrics import evaluate_r5_xgame_binary_scores


def test_r5_xgame_binary_metrics_require_both_classes():
    with pytest.raises(ValueError, match="both normal and buggy"):
        evaluate_r5_xgame_binary_scores([1, 1], [0.7, 0.8], threshold=0.5)


def test_r5_xgame_binary_metrics_return_required_fields():
    metrics = evaluate_r5_xgame_binary_scores([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], threshold=0.5)
    assert metrics["auroc"] == 1.0
    assert metrics["balanced_accuracy"] == 1.0
    assert metrics["fpr_at_95_tpr"] == 0.0
