import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.cover_letter_baseline import generate_baseline_b1


@pytest.mark.asyncio
async def test_baseline_b1_returns_plain_text():
    test_model = TestModel(
        custom_output_args={"body_markdown": "Dear Acme team, I'm writing to apply for…"}
    )

    from apply.agents import cover_letter_baseline as mod

    with mod._agent.override(model=test_model):
        text = await generate_baseline_b1(
            resume_markdown="I ship agents.",
            jd_markdown="Founding Engineer. 5+ yrs Python.",
        )

    assert isinstance(text, str)
    assert "Acme" in text
