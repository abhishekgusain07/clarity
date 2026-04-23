from eval.reports.markdown import render_bench_report
from eval.runners.company_research_bench import CompanyResearchBenchResult
from eval.runners.fit_bench import FitBenchResult, FitCorrelationStats
from eval.runners.intake_bench import IntakeBenchResult


def test_render_bench_report_includes_all_sections():
    intake_results = [
        IntakeBenchResult(
            jd_id="yc-001",
            passed=True,
            field_recall=1.0,
            field_hits=7,
            field_checked=7,
        )
    ]
    company_results = [
        CompanyResearchBenchResult(
            company_name="Anthropic",
            passed=True,
            fact_recall=1.0,
            facts_found=["Anthropic", "AI safety"],
            signal_score=0.85,
        )
    ]
    fit_results = [
        FitBenchResult(
            resume_id="resume-python-ai",
            jd_id="yc-001",
            expert_score=80,
            predicted_score=78,
            score_delta=-2,
            within_tolerance=True,
            verdict_match=True,
            action_match=True,
            expected_verdict="STRONG",
            predicted_verdict="STRONG",
            expected_action="PROCEED",
            predicted_action="PROCEED",
        )
    ]
    fit_stats = FitCorrelationStats(
        n=5,
        pearson_r=0.83,
        pearson_p=0.04,
        mean_abs_delta=5.2,
        pct_within_tolerance=0.8,
    )

    md = render_bench_report(
        intake=intake_results,
        company=company_results,
        fit=fit_results,
        fit_stats=fit_stats,
        run_timestamp="2026-04-23T12:00:00Z",
    )

    assert "# Bench report" in md
    assert "2026-04-23" in md
    assert "Intake" in md
    assert "Company Research" in md
    assert "Fit Analyst" in md
    assert "yc-001" in md
    assert "Anthropic" in md
    assert "0.83" in md  # pearson_r formatting


def test_render_bench_report_handles_insufficient_correlation():
    fit_stats = FitCorrelationStats(
        n=2, pearson_r=None, pearson_p=None, mean_abs_delta=None, pct_within_tolerance=None,
    )
    md = render_bench_report(
        intake=[], company=[], fit=[],
        fit_stats=fit_stats,
        run_timestamp="2026-04-23T12:00:00Z",
    )
    assert "insufficient" in md.lower() or "n/a" in md.lower()
