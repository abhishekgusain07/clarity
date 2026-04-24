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


def render_cover_letter_comparison(summary) -> str:
    """Render a 2-way comparison table for S (full pipeline) vs B1 (Claude one-shot)."""
    if not summary.rows:
        return "### Cover Letter Comparison (S vs B1)\n\nNo results.\n"
    lines = [
        "### Cover Letter Comparison (S = full pipeline, B1 = Claude one-shot)",
        "",
        f"- **Pairs judged:** {len(summary.rows)}",
        f"- **Specificity lift (S - B1):** {summary.mean_delta('specificity'):+.2f}",
        f"- **Voice match lift:**      {summary.mean_delta('voice_match'):+.2f}",
        f"- **Hook strength lift:**    {summary.mean_delta('hook_strength'):+.2f}",
        f"- **Professionalism lift:**  {summary.mean_delta('professionalism'):+.2f}",
        "",
        "| Company | Spec (S/B1) | Voice (S/B1) | Hook (S/B1) | Prof (S/B1) |",
        "|---|---|---|---|---|",
    ]
    for r in summary.rows:
        lines.append(
            f"| {r.company_name} | "
            f"{r.s_scores.specificity}/{r.b1_scores.specificity} | "
            f"{r.s_scores.voice_match}/{r.b1_scores.voice_match} | "
            f"{r.s_scores.hook_strength}/{r.b1_scores.hook_strength} | "
            f"{r.s_scores.professionalism}/{r.b1_scores.professionalism} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_bench_report(
    intake: list[IntakeBenchResult],
    company: list[CompanyResearchBenchResult],
    fit: list[FitBenchResult],
    fit_stats: FitCorrelationStats,
    run_timestamp: str,
    cover_letter_summary=None,
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
    if cover_letter_summary is not None:
        parts.extend([
            "---",
            "",
            render_cover_letter_comparison(cover_letter_summary),
        ])
    return "\n".join(parts)
