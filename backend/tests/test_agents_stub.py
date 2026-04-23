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


from apply.agents.fit_analyst import fit_analyst_stub
from apply.schemas.enums import FitVerdict, RecommendedAction


@pytest.mark.asyncio
async def test_fit_analyst_stub_returns_valid_analysis():
    analysis = await fit_analyst_stub(
        job_listing_id="job-x",
        resume_markdown="Senior Python engineer",
    )

    assert 0 <= analysis.overall_score <= 100
    assert isinstance(analysis.verdict, FitVerdict)
    assert analysis.recommended_action in [
        RecommendedAction.PROCEED,
        RecommendedAction.PROCEED_WITH_CAUTION,
        RecommendedAction.SKIP,
    ]
    assert analysis.reasoning


from apply.agents.cover_letter_writer import cover_letter_writer_stub


@pytest.mark.asyncio
async def test_cover_letter_writer_stub():
    letter = await cover_letter_writer_stub(
        application_id="app-1",
        company_name="Acme AI",
    )

    assert letter.application_id == "app-1"
    assert letter.draft_version == 1
    assert letter.body_markdown
    assert letter.word_count > 0
    assert len(letter.references_company_specifics) > 0
    assert 0.0 <= letter.voice_similarity_score <= 1.0


from apply.agents.screening_answerer import screening_answerer_stub
from apply.schemas.enums import ScreeningAnswerOrigin


@pytest.mark.asyncio
async def test_screening_answerer_stub():
    answer = await screening_answerer_stub(
        question="Why do you want to work at Acme AI?",
        origin=ScreeningAnswerOrigin.PROACTIVE,
    )

    assert answer.question == "Why do you want to work at Acme AI?"
    assert answer.answer
    assert answer.word_count > 0
    assert answer.drafted_by == ScreeningAnswerOrigin.PROACTIVE


from apply.agents.form_fill import FormFillResult, form_fill_stub


@pytest.mark.asyncio
async def test_form_fill_stub():
    result = await form_fill_stub(
        application_url="https://workatastartup.com/jobs/123/apply",
        cover_letter_body="Dear team, ...",
    )

    assert isinstance(result, FormFillResult)
    assert result.fields_filled  # non-empty
    assert result.unknown_fields is not None  # may be empty list
    assert result.screenshot_path
