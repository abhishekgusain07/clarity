import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.screening_answerer_real import screening_answerer_real
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import ScreeningAnswer


@pytest.mark.asyncio
async def test_screening_answerer_real_returns_valid_answer():
    test_model = TestModel(
        custom_output_args={
            "answer_markdown": "I'm drawn to Acme because their recent blog on agent product thinking…"
        }
    )

    from apply.agents import screening_answerer_real as mod

    with mod._agent.override(model=test_model):
        result = await screening_answerer_real(
            question="Why do you want to work at Acme AI?",
            company_name="Acme AI",
            company_brief="Series A agent startup",
            jd_markdown="Founding Engineer…",
            corpus_resume_markdown="I ship agents.",
            corpus_voice_samples=["Sample one."],
            origin=ScreeningAnswerOrigin.PROACTIVE,
        )

    assert isinstance(result, ScreeningAnswer)
    assert result.question == "Why do you want to work at Acme AI?"
    assert "Acme" in result.answer
    assert result.word_count > 0
    assert result.drafted_by == ScreeningAnswerOrigin.PROACTIVE
