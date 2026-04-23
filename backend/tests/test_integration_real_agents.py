"""Live integration test. Runs against real OpenRouter + Tavily + Firecrawl.

Skipped unless APPLY_OPENROUTER_API_KEY, TAVILY_API_KEY, and FIRECRAWL_API_KEY
are all set. Costs ~$0.10 per run. Not run in CI.
"""
import os

import pytest

from apply.agents import runtime
from apply.schemas.company import CompanyResearch
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing

REQUIRED_KEYS = ("APPLY_OPENROUTER_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY")
_HAS_KEYS = all(os.getenv(k) for k in REQUIRED_KEYS)


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_intake_on_sample_text(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    sample = """
    Founding Engineer at Acme AI (YC W24).
    San Francisco, hybrid. $180k-$240k + equity.
    Requirements: 5+ years Python, LLM experience. Nice to have: LangGraph.
    """
    result = await runtime.intake(
        url="https://workatastartup.com/jobs/test-123",
        jd_text=sample,
        raw_html_path="/tmp/apply/test.html",
    )
    assert isinstance(result, JobListing)
    assert "Acme" in result.company_name
    assert result.requirements


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_fit_analyst(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.fit_analyst(
        resume_markdown="Senior Python engineer, 5 years async + ML infra.",
        jd_markdown="Founding engineer. 5+ years Python. LLM experience required.",
        company_brief="Acme AI — Series A, building agents.",
    )
    assert isinstance(result, FitAnalysis)
    assert 0 <= result.overall_score <= 100


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_company_researcher(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.company_researcher(company_name="Anthropic")
    assert isinstance(result, CompanyResearch)
    assert result.company_name
    assert result.sources


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_cover_letter_writer(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime

    result = await runtime.cover_letter_writer(
        application_id="app-live-test",
        company_name="Anthropic",
        company_brief="AI safety research lab, Claude models",
        jd_markdown=(
            "Applied AI Engineer. 5+ years Python. "
            "Experience with LLMs and agent frameworks. "
            "Comfort with async systems."
        ),
        corpus_resume_markdown=(
            "Senior Python engineer. Shipped multi-agent systems "
            "with Pydantic AI + MCP. Async systems expertise."
        ),
        corpus_voice_samples=[
            "I read your recent blog on agent product thinking with interest.",
            "The thing I'd most like to talk about is how your team thinks about evaluation.",
        ],
    )

    assert result.body_markdown
    assert result.word_count >= 100
    assert 0.0 <= result.voice_similarity_score <= 1.0


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_screening_answerer(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime
    from apply.schemas.enums import ScreeningAnswerOrigin

    result = await runtime.screening_answerer(
        question="What excites you about applied AI work?",
        company_name="Anthropic",
        company_brief="AI safety research lab",
        jd_markdown="Applied AI Engineer",
        corpus_resume_markdown="Ships agents, cares about eval harnesses.",
        corpus_voice_samples=["The discipline that makes good backend code makes good agent code."],
        origin=ScreeningAnswerOrigin.PROACTIVE,
    )

    assert result.answer
    assert result.word_count >= 30
