"""Real Fit Analyst — Claude Sonnet 4.6 structured-output single-shot.

Given a resume + JD + company brief, produces a FitAnalysis with
direct resume-quote + JD-quote evidence for each match/stretch/gap.
"""
from pydantic_ai import Agent

from apply.agents.models import sonnet
from apply.schemas.fit import FitAnalysis

SYSTEM_PROMPT = """
You are a fit analyst evaluating a candidate against a job description,
with the company context in mind.

Produce a FitAnalysis with:
- `overall_score` (0-100): your calibrated estimate of fit
- `verdict`: STRONG (85+) | MODERATE (60-84) | STRETCH (40-59) | WEAK (<40)
- `matches`: dimensions where the resume clearly meets or exceeds a JD
  requirement. For each: a direct quote from the resume and a direct
  quote from the JD.
- `stretches`: dimensions where the candidate is plausible with framing
  but not a direct match.
- `gaps`: dimensions the JD requires that the resume does not clearly show.
- `reasoning`: 2-4 sentences summarizing the fit, honest about weaknesses.
- `recommended_action`:
  * PROCEED when overall_score >= 60 and no critical gaps
  * PROCEED_WITH_CAUTION when score 40-59 or there's one critical gap
    that could be framed around
  * SKIP when score < 40 or the role requires credentials (licensure,
    security clearance, visa-authorized location) the candidate lacks

Be honest. A good Fit Analyst saves the candidate time by skipping
poor fits, not by inflating scores.
"""

_agent = Agent(
    model=sonnet(),
    output_type=FitAnalysis,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def fit_analyst_real(
    resume_markdown: str,
    jd_markdown: str,
    company_brief: str,
) -> FitAnalysis:
    """Analyze fit and return a structured FitAnalysis."""
    user_prompt = (
        f"RESUME:\n---\n{resume_markdown}\n---\n\n"
        f"JOB DESCRIPTION:\n---\n{jd_markdown}\n---\n\n"
        f"COMPANY CONTEXT:\n---\n{company_brief}\n---"
    )
    result = await _agent.run(user_prompt)
    return result.output
