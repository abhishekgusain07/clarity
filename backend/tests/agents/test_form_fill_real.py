from unittest.mock import patch

import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.form_context import FormFillDeps
from apply.agents.form_fill import FormFillResult
from apply.agents.form_fill_real import form_fill_real


@pytest.fixture
def sample_deps() -> FormFillDeps:
    return FormFillDeps(
        application_url="file:///tmp/test.html",
        profile={"full_name": "Test User", "email": "t@e.co"},
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, …",
        company_name="Acme AI",
        company_brief="Series A agent startup",
        jd_markdown="Engineer role",
        voice_samples=[],
    )


@pytest.mark.asyncio
async def test_form_fill_real_returns_structured_result(sample_deps):
    test_model = TestModel(
        custom_output_args={
            "fields_filled": [
                {"name": "full_name", "value": "Test User", "field_type": "text"},
                {"name": "email", "value": "t@e.co", "field_type": "text"},
                {"name": "cover_letter", "value": "Dear team, …", "field_type": "textarea"},
            ],
            "unknown_fields": [],
            "screenshot_path": "/tmp/apply/fill.png",
            "submission_url": None,
            "success": True,
        }
    )

    # Build a new agent without the real Playwright MCP toolset for the test
    from pydantic_ai import Agent

    from apply.agents import form_fill_real as mod

    agent_without_mcp = Agent(
        model=test_model,
        output_type=FormFillResult,
        deps_type=FormFillDeps,
        system_prompt="test",
    )

    with patch.object(mod, "_build_agent", return_value=agent_without_mcp):
        result = await form_fill_real(deps=sample_deps)

    assert isinstance(result, FormFillResult)
    assert result.success
    assert len(result.fields_filled) == 3
    assert any(f.name == "full_name" for f in result.fields_filled)
    assert result.screenshot_path == "/tmp/apply/fill.png"


@pytest.mark.asyncio
async def test_form_fill_real_surfaces_unknown_fields(sample_deps):
    test_model = TestModel(
        custom_output_args={
            "fields_filled": [
                {"name": "full_name", "value": "Test User", "field_type": "text"}
            ],
            "unknown_fields": [
                {
                    "name": "why_us",
                    "field_type": "textarea",
                    "best_guess": None,
                    "reason_flagged": "open-ended question not in profile",
                }
            ],
            "screenshot_path": "/tmp/s.png",
            "submission_url": None,
            "success": True,
        }
    )

    from pydantic_ai import Agent

    from apply.agents import form_fill_real as mod

    agent_without_mcp = Agent(
        model=test_model,
        output_type=FormFillResult,
        deps_type=FormFillDeps,
        system_prompt="test",
    )

    with patch.object(mod, "_build_agent", return_value=agent_without_mcp):
        result = await form_fill_real(deps=sample_deps)

    assert len(result.unknown_fields) == 1
    assert result.unknown_fields[0].name == "why_us"
