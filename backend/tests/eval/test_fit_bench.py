import pytest

from apply.schemas.enums import FitVerdict, RecommendedAction
from apply.schemas.fit import FitAnalysis
from eval.runners.fit_bench import (
    FitBenchResult,
    compute_fit_correlation,
    score_fit_pair,
)


def _fake_analysis(score=75, verdict="MODERATE", action="PROCEED"):
    return FitAnalysis(
        overall_score=score,
        verdict=FitVerdict(verdict),
        matches=[],
        stretches=[],
        gaps=[],
        reasoning="…",
        recommended_action=RecommendedAction(action),
    )


def test_score_fit_pair_close_match():
    expected = {"expert_score": 78, "expected_verdict": "MODERATE", "expected_action": "PROCEED"}
    analysis = _fake_analysis(score=75, verdict="MODERATE", action="PROCEED")

    result = score_fit_pair(expected=expected, analysis=analysis)

    assert result.score_delta == -3
    assert result.verdict_match is True
    assert result.action_match is True
    assert result.within_tolerance is True  # |delta| <= 15


def test_score_fit_pair_large_gap():
    expected = {"expert_score": 85, "expected_verdict": "STRONG", "expected_action": "PROCEED"}
    analysis = _fake_analysis(score=40, verdict="STRETCH", action="PROCEED_WITH_CAUTION")

    result = score_fit_pair(expected=expected, analysis=analysis)

    assert result.score_delta == -45
    assert not result.within_tolerance
    assert not result.verdict_match
    assert not result.action_match


def test_compute_correlation_ideal():
    expert = [20, 40, 60, 80, 100]
    predicted = [22, 38, 62, 78, 99]

    stats = compute_fit_correlation(expert_scores=expert, predicted_scores=predicted)

    assert stats.pearson_r > 0.99
    assert stats.n == 5


def test_compute_correlation_too_few_points():
    stats = compute_fit_correlation(expert_scores=[50], predicted_scores=[60])
    assert stats.n == 1
    assert stats.pearson_r is None
