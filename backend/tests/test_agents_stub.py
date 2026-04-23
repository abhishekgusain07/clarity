import pytest

from apply.agents.intake import intake_stub


@pytest.mark.asyncio
async def test_intake_stub_returns_valid_job_listing():
    listing = await intake_stub(url="https://workatastartup.com/jobs/123")

    assert listing.company_name
    assert listing.role_title
    assert str(listing.url) == "https://workatastartup.com/jobs/123"
    assert listing.requirements  # non-empty


from apply.agents.company_researcher import company_researcher_stub


@pytest.mark.asyncio
async def test_company_researcher_stub_returns_valid_research():
    research = await company_researcher_stub(company_name="Acme AI")

    assert research.company_name == "Acme AI"
    assert research.founders  # non-empty
    assert research.recent_news  # non-empty
    assert 0.0 <= research.signal_score <= 1.0
    assert research.sources
