"""Real Cover Letter Writer.

Sonnet 4.6 single-shot with two structured-output fields (body_markdown and
references_company_specifics). Voice-similarity score is computed
out-of-band via OpenAI embeddings after the agent returns the draft.

Inputs (passed by the orchestrator):
- application_id: used in the returned CoverLetter's application_id
- company_name, company_brief: hook material
- jd_markdown: what the user is applying for
- corpus_resume_markdown: what the user has done (from resume-mcp)
- corpus_voice_samples: the user's past writing (from resume-mcp)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from pydantic_ai import Agent

from apply.agents.models import sonnet
from apply.agents.voice_similarity import compute_voice_similarity
from apply.schemas.writing import CoverLetter

SYSTEM_PROMPT = """
You are drafting a cover letter that sounds like the candidate — not like
a generic "passionate engineer looking for opportunities" template.

You will receive:
- the candidate's resume (for context on what they've built)
- 2-5 writing samples in the candidate's voice (cover letters, essays, emails)
- the target company's name + a one-line brief about them
- the job description

Your job:
1. Write a cover letter of ~250-350 words that:
   - Opens with a specific observation about the company (never "I'm excited
     to apply for…")
   - Weaves in 2-3 concrete company-specific facts from the brief
   - Reflects the candidate's actual experience quoted or paraphrased from
     the resume (do NOT invent projects)
   - Matches the cadence and vocabulary of the voice samples
2. Return a list of the company-specific facts you actually cited, so the
   user can verify you didn't hallucinate.

Do NOT include sign-off boilerplate ("Sincerely, Name" — the app will add
this later). End on the strongest sentence you can write.
"""


class _AgentOutput(BaseModel):
    body_markdown: str
    references_company_specifics: list[str]


_agent = Agent(
    model=sonnet(),
    output_type=_AgentOutput,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def cover_letter_writer_real(
    application_id: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
) -> CoverLetter:
    user_prompt = (
        f"COMPANY: {company_name}\n"
        f"BRIEF: {company_brief}\n\n"
        f"JD:\n---\n{jd_markdown}\n---\n\n"
        f"CANDIDATE RESUME:\n---\n{corpus_resume_markdown}\n---\n\n"
        f"VOICE SAMPLES (match this cadence):\n---\n"
        + "\n\n—\n\n".join(corpus_voice_samples)
        + "\n---"
    )
    result = await _agent.run(user_prompt)
    out = result.output

    voice_score = await compute_voice_similarity(
        draft=out.body_markdown,
        samples=corpus_voice_samples,
    )

    return CoverLetter(
        id=f"cl-{uuid.uuid4().hex[:8]}",
        application_id=application_id,
        draft_version=1,
        body_markdown=out.body_markdown,
        word_count=len(out.body_markdown.split()),
        references_company_specifics=out.references_company_specifics,
        voice_similarity_score=voice_score,
        created_at=datetime.now(UTC),
    )
