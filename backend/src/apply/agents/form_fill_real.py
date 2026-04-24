"""Real Form-Fill browser-driving agent.

Pydantic AI Agent with:
- Claude Sonnet via OpenRouter (same stack as research agents)
- Playwright MCP as a toolset (browser control)
- One custom tool `answer_screening_question` that calls the real
  Screening Answerer using pipeline context from deps
- Structured output: FormFillResult

The agent navigates to the application URL, inspects the form via
Playwright's accessibility snapshot, fills what it knows from the
profile/cover letter, calls the screening tool for unknown free-text
fields, captures a screenshot, and returns the structured result.

It does NOT submit — submission is a separate step after HITL #3.
"""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from apply.agents.form_context import FormFillDeps
from apply.agents.form_fill import FormFillResult
from apply.agents.mcp_servers import playwright_mcp
from apply.agents.models import sonnet
from apply.schemas.enums import ScreeningAnswerOrigin

SYSTEM_PROMPT = """
You are filling a job application form via a browser. You have Playwright
tools (navigate, click, fill, upload, screenshot, accessibility_snapshot)
and a custom `answer_screening_question` tool that drafts answers to
free-text questions in the candidate's voice.

Your job for THIS application:

1. Navigate to `application_url` (in your deps).
2. Take an accessibility snapshot. Identify every form field.
3. Fill fields you have direct values for from deps.profile:
   - full_name, email, phone, linkedin_url, github_url, portfolio_url,
     location — all optional, fill what's set.
4. Upload the resume: `deps.resume_pdf_path`.
5. Paste `deps.cover_letter_text` into the cover-letter textarea.
6. For any free-text question (like "Why us?", "Tell us about a time…"):
   - Call `answer_screening_question(question)` to get a drafted answer.
   - Fill the field with the returned answer.
7. For fields you truly can't interpret (custom dropdowns, file types
   you don't have), put them in `unknown_fields` with `best_guess=null`
   and a short `reason_flagged`. DO NOT fabricate.
8. Take a final screenshot. Include the absolute path in `screenshot_path`.
9. DO NOT click Submit. Return the structured FormFillResult.

Return JSON only via the structured output — do not narrate.
"""


def _build_agent() -> Agent:
    """Build at call time so MCP subprocess binds to current loop."""
    agent: Agent = Agent(
        model=sonnet(),
        output_type=FormFillResult,
        deps_type=FormFillDeps,
        system_prompt=SYSTEM_PROMPT,
        toolsets=[playwright_mcp()],
        retries=1,
    )

    @agent.tool
    async def answer_screening_question(
        ctx: RunContext[FormFillDeps], question: str
    ) -> str:
        """Draft an answer to a screening question in the candidate's voice."""
        # Import inside to avoid circular import at module load time
        from apply.agents.runtime import screening_answerer

        deps = ctx.deps
        result = await screening_answerer(
            question=question,
            company_name=deps.company_name,
            company_brief=deps.company_brief,
            jd_markdown=deps.jd_markdown,
            corpus_resume_markdown="",  # resume already uploaded as file; text
            corpus_voice_samples=deps.voice_samples,
            origin=ScreeningAnswerOrigin.FORM_FILL_CALLBACK,
        )
        return result.answer

    return agent


async def form_fill_real(deps: FormFillDeps) -> FormFillResult:
    agent = _build_agent()
    async with agent:
        result = await agent.run(
            f"Proceed with the application at {deps.application_url}.",
            deps=deps,
        )
    return result.output
