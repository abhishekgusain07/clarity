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


from apply.schemas.enums import ScreeningAnswerOrigin


@pytest.mark.asyncio
async def test_runtime_cover_letter_writer_stub_path(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.cover_letter_writer(
        application_id="app-x",
        company_name="Acme AI",
        company_brief="brief",
        jd_markdown="jd",
        corpus_resume_markdown="resume",
        corpus_voice_samples=["sample"],
    )
    # Stub path: should call cover_letter_writer_stub and return a CoverLetter
    assert result.application_id == "app-x"


@pytest.mark.asyncio
async def test_runtime_screening_answerer_stub_path(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.screening_answerer(
        question="Why us?",
        company_name="Acme AI",
        company_brief="brief",
        jd_markdown="jd",
        corpus_resume_markdown="resume",
        corpus_voice_samples=["sample"],
        origin=ScreeningAnswerOrigin.PROACTIVE,
    )
    assert result.question == "Why us?"


@pytest.mark.asyncio
async def test_runtime_cover_letter_writer_real_path(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime as rt

    async def fake_real(**kwargs):
        from datetime import UTC, datetime

        from apply.schemas.writing import CoverLetter
        return CoverLetter(
            id="cl-real", application_id=kwargs["application_id"],
            draft_version=1, body_markdown="real draft",
            word_count=2, references_company_specifics=[],
            voice_similarity_score=0.8, created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(rt, "_cover_letter_real", fake_real)

    result = await runtime.cover_letter_writer(
        application_id="app-real",
        company_name="Acme",
        company_brief="brief",
        jd_markdown="jd",
        corpus_resume_markdown="resume",
        corpus_voice_samples=["s1"],
    )
    assert result.application_id == "app-real"
    assert result.body_markdown == "real draft"
