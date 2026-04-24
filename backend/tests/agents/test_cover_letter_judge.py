import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.cover_letter_judge import judge_cover_letter
from apply.schemas.writing import CoverLetter
from datetime import datetime, UTC


@pytest.mark.asyncio
async def test_judge_returns_valid_scores():
    letter = CoverLetter(
        id="cl-1", application_id="app-1", draft_version=1,
        body_markdown="Dear Acme, I read your Series A announcement…",
        word_count=50, references_company_specifics=["Series A"],
        voice_similarity_score=0.7, created_at=datetime.now(UTC),
    )

    test_model = TestModel(
        custom_output_args={
            "specificity": 8, "voice_match": 7, "hook_strength": 7,
            "professionalism": 9, "specifics_cited": ["Series A announcement"],
            "rationale": "Solid specific hook; voice is close.",
        }
    )

    from apply.agents import cover_letter_judge as mod

    with mod._agent.override(model=test_model):
        scores = await judge_cover_letter(
            letter=letter,
            company_research_summary="Acme raised Series A in Nov 2025.",
            voice_samples=["Sample one.", "Sample two."],
        )

    assert 0 <= scores.specificity <= 10
    assert 0 <= scores.voice_match <= 10
    assert 0 <= scores.hook_strength <= 10
    assert 0 <= scores.professionalism <= 10
    assert scores.specifics_cited
    assert scores.rationale
