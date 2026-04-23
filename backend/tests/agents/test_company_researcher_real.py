from unittest.mock import patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from apply.agents import company_researcher_real as mod
from apply.schemas.company import CompanyResearch


@pytest.mark.asyncio
async def test_company_researcher_real_returns_valid_research():
    """Unit test: patch `_build_agent` to return a TestModel-backed agent
    without MCP toolsets — avoids spinning up real MCP subprocesses.
    """
    test_model = TestModel(
        custom_output_args={
            "company_name": "Acme AI",
            "funding_stage": "Series A",
            "last_round": None,
            "team_size": "20-50",
            "founders": [
                {
                    "name": "Jordan Smith",
                    "background": "ex-Anthropic",
                    "linkedin_url": None,
                }
            ],
            "recent_news": [
                {
                    "title": "Acme raises $12M Series A",
                    "url": "https://techcrunch.com/acme",
                    "date_iso": "2025-11-15",
                    "summary": None,
                }
            ],
            "recent_blog_posts": [],
            "tech_stack_hints": ["Python", "LangGraph"],
            "signal_score": 0.72,
            "sources": [
                {
                    "url": "https://acme.ai",
                    "title": "Acme homepage",
                    "trust_score": 0.9,
                }
            ],
        }
    )

    agent_stub = Agent(
        model=test_model,
        output_type=CompanyResearch,
        system_prompt="",
    )

    with patch.object(mod, "_build_agent", return_value=agent_stub):
        result = await mod.company_researcher_real(company_name="Acme AI")

    assert isinstance(result, CompanyResearch)
    assert result.company_name == "Acme AI"
    assert 0.0 <= result.signal_score <= 1.0
    assert result.founders
    assert result.sources
