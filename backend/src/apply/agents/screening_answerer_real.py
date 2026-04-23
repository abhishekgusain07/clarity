"""Real Screening Question Answerer.

Sonnet 4.6 single-shot per question. Uses the same context as the Cover
Letter Writer (resume + voice samples + company brief) but answers ONE
specific screening question. Invoked either proactively (if the JD lists
screening questions up-front) or dynamically by Form-Fill when it
encounters a free-text question mid-fill.
"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent

from apply.agents.models import sonnet
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import ScreeningAnswer

SYSTEM_PROMPT = """
You are answering a single screening question on a job application, in
the candidate's voice. You will receive the candidate's resume, writing
samples, the company brief, the JD, and one question.

Guidelines:
- 100-200 words unless the form clearly wants something shorter
- Open with a specific observation, not a generic affirmation
- Cite 1-2 concrete things from the candidate's resume — don't invent
- Match the cadence of the voice samples
- End strong. No "I look forward to hearing from you" boilerplate.

Return just the answer text (no question repetition, no heading).
"""


class _AgentOutput(BaseModel):
    answer_markdown: str


_agent = Agent(
    model=sonnet(),
    output_type=_AgentOutput,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def screening_answerer_real(
    question: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
    origin: ScreeningAnswerOrigin,
) -> ScreeningAnswer:
    user_prompt = (
        f"QUESTION: {question}\n\n"
        f"COMPANY: {company_name}\n"
        f"BRIEF: {company_brief}\n\n"
        f"JD:\n---\n{jd_markdown}\n---\n\n"
        f"CANDIDATE RESUME:\n---\n{corpus_resume_markdown}\n---\n\n"
        f"VOICE SAMPLES (match this cadence):\n---\n"
        + "\n\n—\n\n".join(corpus_voice_samples)
        + "\n---"
    )
    result = await _agent.run(user_prompt)
    answer_text = result.output.answer_markdown
    return ScreeningAnswer(
        question=question,
        answer=answer_text,
        word_count=len(answer_text.split()),
        drafted_by=origin,
    )
