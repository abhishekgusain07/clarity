"""Markdown report generator for bench runs."""
from eval.runners.company_research_bench import CompanyResearchBenchResult
from eval.runners.fit_bench import FitBenchResult, FitCorrelationStats
from eval.runners.intake_bench import IntakeBenchResult


def _pct(x: float | None) -> str:
    if x is None:
        return "N/A"
    return f"{x * 100:.1f}%"


def _fmt_float(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "N/A"
    return f"{x:.{digits}f}"


def _render_intake(results: list[IntakeBenchResult]) -> str:
    if not results:
        return "### Intake\n\nNo results.\n"
    passed = sum(1 for r in results if r.passed)
    lines = [
        "### Intake",
        "",
        f"- **Cases run:** {len(results)}",
        f"- **Passed (field recall ≥ 0.95):** {passed}/{len(results)}",
        "",
        "| JD | Recall | Hits | Checked | Failed fields |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        failed = ", ".join(r.failed_fields) if r.failed_fields else "—"
        lines.append(f"| `{r.jd_id}` | {_pct(r.field_recall)} | {r.field_hits} | {r.field_checked} | {failed} |")
    lines.append("")
    return "\n".join(lines)


def _render_company(results: list[CompanyResearchBenchResult]) -> str:
    if not results:
        return "### Company Research\n\nNo results (no JDs with expected_company_facts).\n"
    passed = sum(1 for r in results if r.passed)
    lines = [
        "### Company Research",
        "",
        f"- **Cases run:** {len(results)}",
        f"- **Passed (fact recall ≥ 0.60):** {passed}/{len(results)}",
        "",
        "| Company | Recall | Signal | Found | Missing |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        found = ", ".join(r.facts_found) if r.facts_found else "—"
        missing = ", ".join(r.facts_missing) if r.facts_missing else "—"
        lines.append(f"| {r.company_name} | {_pct(r.fact_recall)} | {_fmt_float(r.signal_score)} | {found} | {missing} |")
    lines.append("")
    return "\n".join(lines)


def _render_fit(results: list[FitBenchResult], stats: FitCorrelationStats) -> str:
    lines = [
        "### Fit Analyst",
        "",
        f"- **Cases run:** {stats.n}",
    ]
    if stats.pearson_r is None:
        lines.append("- **Correlation:** insufficient data (need ≥ 3 pairs)")
    else:
        lines.append(f"- **Pearson r:** {_fmt_float(stats.pearson_r)} (p = {_fmt_float(stats.pearson_p, 3)})")
        lines.append(f"- **Mean |delta|:** {_fmt_float(stats.mean_abs_delta, 1)} points")
        lines.append(f"- **% within ±15 pts:** {_pct(stats.pct_within_tolerance)}")
    lines.extend([
        "",
        "| Resume | JD | Expert | Predicted | Δ | Verdict match | Action match |",
        "|---|---|---|---|---|---|---|",
    ])
    for r in results:
        lines.append(
            f"| {r.resume_id} | {r.jd_id} | {r.expert_score} | {r.predicted_score} | "
            f"{r.score_delta:+d} | {'✓' if r.verdict_match else '✗'} ({r.expected_verdict}→{r.predicted_verdict}) | "
            f"{'✓' if r.action_match else '✗'} ({r.expected_action}→{r.predicted_action}) |"
        )
    lines.append("")
    return "\n".join(lines)


def render_bench_report(
    intake: list[IntakeBenchResult],
    company: list[CompanyResearchBenchResult],
    fit: list[FitBenchResult],
    fit_stats: FitCorrelationStats,
    run_timestamp: str,
) -> str:
    parts = [
        "# Bench report",
        "",
        f"Run: {run_timestamp}",
        "",
        "## Summary",
        "",
        f"- Intake cases: {len(intake)}",
        f"- Company Research cases: {len(company)}",
        f"- Fit Analyst cases: {fit_stats.n}",
        "",
        "---",
        "",
        _render_intake(intake),
        "---",
        "",
        _render_company(company),
        "---",
        "",
        _render_fit(fit, fit_stats),
    ]
    return "\n".join(parts)
