import pytest

from apply.agents import runtime


@pytest.mark.asyncio
async def test_runtime_routes_to_stub_when_flag_false(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")

    # Reset cached settings so monkeypatch is picked up
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    listing = await runtime.intake(
        url="https://workatastartup.com/jobs/test",
        jd_text="(ignored in stub)",
        raw_html_path="/tmp/stub.html",
    )
    assert listing.company_name == "Acme AI"  # matches intake_stub fixture


@pytest.mark.asyncio
async def test_runtime_routes_to_real_when_flag_true(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")

    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    # Patch the real function to avoid a real LLM call
    from apply.agents import runtime as rt

    async def fake_intake_real(url, jd_text, raw_html_path):
        from apply.schemas.enums import JobSource, RemoteType
        from apply.schemas.job import JobListing
        return JobListing(
            id="job-real",
            source=JobSource.OTHER,
            url=url,
            application_url=url,
            company_name="Real Corp",
            role_title="Engineer",
            location="Remote",
            remote_type=RemoteType.REMOTE,
            description_markdown="",
            requirements=[],
            nice_to_haves=[],
            raw_html_path=raw_html_path,
        )

    monkeypatch.setattr(rt, "_intake_real", fake_intake_real)

    listing = await runtime.intake(
        url="https://example.com/jobs/1",
        jd_text="text",
        raw_html_path="/tmp/real.html",
    )
    assert listing.company_name == "Real Corp"
