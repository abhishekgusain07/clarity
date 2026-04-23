import pytest

from apply.schemas.company import (
    BlogPost,
    CompanyResearch,
    Founder,
    NewsItem,
    Source,
)
from eval.runners.company_research_bench import (
    CompanyResearchBenchResult,
    score_company_research,
)


def _fake_research(company_name="Anthropic", signal_score=0.8):
    return CompanyResearch(
        company_name=company_name,
        funding_stage="Series E",
        last_round=None,
        team_size="500+",
        founders=[
            Founder(name="Dario Amodei", background="ex-OpenAI VP of Research")
        ],
        recent_news=[
            NewsItem(
                title="Anthropic releases Claude 4.6",
                url="https://techcrunch.com/anthropic-claude-46",
                date_iso="2025-10-15",
                summary="New frontier model focused on agentic workflows.",
            )
        ],
        recent_blog_posts=[
            BlogPost(
                title="How we think about AI safety",
                url="https://www.anthropic.com/blog/ai-safety",
                summary="Core principles for responsible AI development.",
            )
        ],
        tech_stack_hints=["Python", "PyTorch"],
        signal_score=signal_score,
        sources=[
            Source(url="https://www.anthropic.com", title="homepage", trust_score=0.95),
        ],
    )


def test_all_expected_facts_found():
    expected_facts = ["Anthropic", "founded", "AI safety"]
    research = _fake_research()

    result = score_company_research(expected_facts=expected_facts, research=research)

    assert result.fact_recall >= 0.6  # "Anthropic" in name, "AI safety" in blog title; "founded" may miss
    assert result.passed is (result.fact_recall >= 0.6)


def test_no_expected_facts_vacuous_pass():
    research = _fake_research()

    result = score_company_research(expected_facts=[], research=research)

    assert result.fact_recall == 1.0
    assert result.passed is True


def test_low_signal_score_flagged():
    research = _fake_research(signal_score=0.2)

    result = score_company_research(
        expected_facts=["Anthropic"],
        research=research,
    )

    assert "low_signal_score" in result.notes


def test_missing_critical_facts_fails():
    expected_facts = ["Nonexistent Corp", "crypto", "metaverse"]
    research = _fake_research()  # about Anthropic, not any of those

    result = score_company_research(expected_facts=expected_facts, research=research)

    assert result.fact_recall < 0.5
    assert not result.passed
