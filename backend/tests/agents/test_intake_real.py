import pytest

from apply.agents import intake_real as intake_real_mod
from apply.agents.intake_real import intake_real
from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing


@pytest.fixture
def sample_jd_text():
    return """
    Founding Engineer — Acme AI (YC W24)
    Location: San Francisco, CA (Hybrid)
    Salary: $180k-$240k + equity

    We're building long-running agents for enterprise workflows.

    Requirements:
    - 5+ years Python
    - Experience with LLMs and agent frameworks
    - Strong async systems background

    Nice to haves:
    - LangGraph / Claude Agent SDK experience
    - Published open-source agent work
    """


@pytest.mark.asyncio
async def test_intake_real_returns_valid_job_listing_unit(sample_jd_text):
    """Unit test using Pydantic AI's TestModel — no network."""
    from pydantic_ai.models.test import TestModel

    test_model = TestModel(
        custom_output_args={
            "id": "job-test",
            "source": "YC_WAAS",
            "url": "https://workatastartup.com/jobs/123",
            "application_url": "https://workatastartup.com/jobs/123/apply",
            "company_name": "Acme AI",
            "role_title": "Founding Engineer",
            "location": "San Francisco, CA",
            "remote_type": "HYBRID",
            "description_markdown": sample_jd_text.strip(),
            "requirements": ["5+ years Python", "LLM experience"],
            "nice_to_haves": ["LangGraph experience"],
            "compensation_range": "$180k-$240k + equity",
            "raw_html_path": "/tmp/apply/stub-jd.html",
        }
    )

    with intake_real_mod._agent.override(model=test_model):
        result = await intake_real(
            url="https://workatastartup.com/jobs/123",
            jd_text=sample_jd_text,
            raw_html_path="/tmp/apply/stub-jd.html",
        )

    assert isinstance(result, JobListing)
    assert result.company_name == "Acme AI"
    assert result.source == JobSource.YC_WAAS
    assert result.remote_type == RemoteType.HYBRID
    assert len(result.requirements) >= 1
