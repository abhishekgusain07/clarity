import pytest

from apply.agents.intake import intake_stub


@pytest.mark.asyncio
async def test_intake_stub_returns_valid_job_listing():
    listing = await intake_stub(url="https://workatastartup.com/jobs/123")

    assert listing.company_name
    assert listing.role_title
    assert str(listing.url) == "https://workatastartup.com/jobs/123"
    assert listing.requirements  # non-empty
