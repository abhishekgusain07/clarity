from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from apply.agents.cover_letter_writer_real import cover_letter_writer_real
from apply.schemas.writing import CoverLetter


@pytest.mark.asyncio
async def test_cover_letter_writer_real_returns_valid_draft():
    # TestModel returns the custom_output_args as the agent's structured output
    fake_body = "Dear Acme team, I read your Series A announcement…"
    test_model = TestModel(
        custom_output_args={
            "body_markdown": fake_body,
            "references_company_specifics": ["Series A", "engineering blog"],
        }
    )

    from apply.agents import cover_letter_writer_real as mod

    async def fake_similarity(draft: str, samples: list[str]) -> float:
        assert draft == fake_body
        assert samples  # corpus must be passed through
        return 0.77

    with patch.object(mod, "compute_voice_similarity", side_effect=fake_similarity):
        with mod._agent.override(model=test_model):
            result = await cover_letter_writer_real(
                application_id="app-test",
                company_name="Acme AI",
                company_brief="Series A agent startup",
                jd_markdown="Founding Engineer. 5+ yrs Python, LLM experience.",
                corpus_resume_markdown="I ship agents.",
                corpus_voice_samples=["Sample one.", "Sample two."],
            )

    assert isinstance(result, CoverLetter)
    assert result.application_id == "app-test"
    assert result.draft_version == 1
    assert result.body_markdown == fake_body
    assert result.voice_similarity_score == 0.77
    assert "Series A" in result.references_company_specifics
    assert result.word_count > 0
