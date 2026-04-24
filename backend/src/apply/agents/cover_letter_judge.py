"""LLM-as-judge for cover letter quality.

Uses GPT-4.1 via OpenRouter (deliberately a different model from Claude,
which generates the content we're judging — reduces self-grading bias).

4-dim rubric, each 0-10 with anchors:
- Specificity: does it reference this company, not generic startup tropes?
- Voice match: does it sound like the candidate, not an LLM?
- Hook strength: would a recruiter read past the first paragraph?
- Professionalism: polished, every word earning its place?

Also outputs `specifics_cited` — the company-research facts the letter
actually used. Doubles as a hallucination check: if the judge cites facts
not in the source `company_research_summary`, the letter is hallucinating.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from apply.agents.models import gpt41
from apply.schemas.writing import CoverLetter


SYSTEM_PROMPT = """
You are a cold-read recruiter scoring a cover letter against 4 dimensions.

Each dimension is 0-10 with these anchors:

SPECIFICITY:
  0-2: could be sent to any company at this stage
  3-5: names the company but nothing that required research
  6-8: references at least one specific fact (recent launch, blog, funding)
  9-10: weaves 3+ specific facts into the narrative naturally

VOICE MATCH (given the candidate's past writing samples):
  0-2: obviously AI-generated professional boilerplate
  3-5: recognizably human but not distinctively this candidate
  6-8: sounds like the candidate's voice
  9-10: indistinguishable from the candidate's past writing

HOOK STRENGTH (first paragraph):
  0-2: "I'm writing to apply for the role of…"
  3-5: opens with context about the candidate
  6-8: opens with a relevant specific observation
  9-10: opens with something that makes a recruiter want to keep reading

PROFESSIONALISM:
  0-2: typos, awkward phrasing, overly casual
  3-5: workable but rough
  6-8: clean, well-structured
  9-10: polished, every word earning its place

Also list `specifics_cited`: the company facts the letter USED (direct from
the letter, not invented). If the letter cites facts NOT in the company
research summary, include them anyway — downstream code will flag them as
potential hallucinations.

One-sentence rationale explaining the headline score.
"""


class JudgeScores(BaseModel):
    specificity: int = Field(ge=0, le=10)
    voice_match: int = Field(ge=0, le=10)
    hook_strength: int = Field(ge=0, le=10)
    professionalism: int = Field(ge=0, le=10)
    specifics_cited: list[str]
    rationale: str


_agent = Agent(
    model=gpt41(),
    output_type=JudgeScores,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def judge_cover_letter(
    letter: CoverLetter,
    company_research_summary: str,
    voice_samples: list[str],
) -> JudgeScores:
    user_prompt = (
        f"COMPANY RESEARCH SUMMARY:\n---\n{company_research_summary}\n---\n\n"
        f"CANDIDATE VOICE SAMPLES:\n---\n"
        + "\n\n—\n\n".join(voice_samples[:3])
        + f"\n---\n\n"
        f"COVER LETTER:\n---\n{letter.body_markdown}\n---"
    )
    result = await _agent.run(user_prompt)
    return result.output
