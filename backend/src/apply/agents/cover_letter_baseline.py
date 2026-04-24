"""B1 baseline: single-shot Claude Sonnet, resume + JD only.

No company research, no voice samples, no structured output beyond the
letter body. This is what a user would get by pasting their resume and
a JD into a ChatGPT-equivalent and asking for a cover letter. The
comparison target for the full Apply pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent

from apply.agents.models import sonnet

SYSTEM_PROMPT = """
Write a cover letter for the candidate described below, applying to the
role described below. 250-350 words. Professional tone. No sign-off
boilerplate — end on the strongest sentence.
"""


class _Out(BaseModel):
    body_markdown: str


_agent = Agent(model=sonnet(), output_type=_Out, system_prompt=SYSTEM_PROMPT, retries=2)


async def generate_baseline_b1(resume_markdown: str, jd_markdown: str) -> str:
    user_prompt = f"RESUME:\n---\n{resume_markdown}\n---\n\nJOB DESCRIPTION:\n---\n{jd_markdown}\n---"
    result = await _agent.run(user_prompt)
    return result.output.body_markdown
