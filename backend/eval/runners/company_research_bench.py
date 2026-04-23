"""Company Research bench runner.

Scores a CompanyResearch against a list of expected_facts. A fact is
counted as "found" if its lowercased text appears anywhere in the
searchable surface of the research object (company_name, funding_stage,
team_size, any founder background, any news title/summary, any blog
title/summary, any tech stack hint). This is deliberately lenient — the
goldenset's expected_facts should be "must find" signals, not exact
phrase matches.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from apply.schemas.company import CompanyResearch


@dataclass
class CompanyResearchBenchResult:
    company_name: str
    passed: bool
    fact_recall: float
    facts_found: list[str] = field(default_factory=list)
    facts_missing: list[str] = field(default_factory=list)
    signal_score: float = 0.0
    notes: list[str] = field(default_factory=list)


def _searchable_text(research: CompanyResearch) -> str:
    parts = [
        research.company_name or "",
        research.funding_stage or "",
        research.team_size or "",
    ]
    for f in research.founders:
        parts.extend([f.name, f.background or ""])
    for n in research.recent_news:
        parts.extend([n.title, n.summary or ""])
    for b in research.recent_blog_posts:
        parts.extend([b.title, b.summary or ""])
    parts.extend(research.tech_stack_hints)
    return " \n ".join(parts).lower()


def score_company_research(
    expected_facts: list[str],
    research: CompanyResearch,
) -> CompanyResearchBenchResult:
    blob = _searchable_text(research)
    result = CompanyResearchBenchResult(
        company_name=research.company_name,
        passed=False,
        fact_recall=0.0,
        signal_score=research.signal_score,
    )

    if not expected_facts:
        result.fact_recall = 1.0
        result.passed = True
    else:
        for fact in expected_facts:
            if fact.lower() in blob:
                result.facts_found.append(fact)
            else:
                result.facts_missing.append(fact)
        result.fact_recall = len(result.facts_found) / len(expected_facts)
        result.passed = result.fact_recall >= 0.6

    if research.signal_score < 0.5:
        result.notes.append("low_signal_score")
    return result


async def run_company_research_bench(
    goldenset_path: Path,
    researcher_fn,
) -> list[CompanyResearchBenchResult]:
    """researcher_fn: async callable(company_name) -> CompanyResearch."""
    data = json.loads(goldenset_path.read_text())
    results: list[CompanyResearchBenchResult] = []

    for item in data["items"]:
        expected_facts = item.get("expected_company_facts", [])
        if not expected_facts:
            continue  # skip entries with no company-fact expectations

        expected_company_name = item.get("expected_fields", {}).get("company_name")
        if not expected_company_name or expected_company_name == "FILL_AT_RUN_TIME":
            continue  # can't research a placeholder

        research = await researcher_fn(company_name=expected_company_name)
        r = score_company_research(expected_facts=expected_facts, research=research)
        results.append(r)

    return results
