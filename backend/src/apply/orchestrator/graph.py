from dataclasses import dataclass, field
from typing import Any

from apply.agents.company_researcher import company_researcher_stub
from apply.agents.cover_letter_writer import cover_letter_writer_stub
from apply.agents.fit_analyst import fit_analyst_stub
from apply.agents.form_fill import form_fill_stub
from apply.agents.intake import intake_stub
from apply.agents.memory_curator import memory_curator_stub
from apply.observability.langfuse_setup import get_langfuse
from apply.orchestrator.state_machine import advance_state
from apply.schemas.enums import PipelineRunState


@dataclass
class PipelineContext:
    run_id: str
    application_id: str
    jd_url: str
    state: PipelineRunState
    artifacts: dict[str, Any] = field(default_factory=dict)
    cost_accumulated_usd: float = 0.0


async def run_to_next_checkpoint(ctx: PipelineContext) -> None:
    """Advance the pipeline until the next HITL gate or a terminal state.

    Each agent writes its artifact to `ctx.artifacts` and the state machine
    is advanced between agents. On reaching an AWAITING_* state or a
    terminal state, this function returns; the caller persists and waits.
    """
    lf = get_langfuse()
    trace = lf.trace(name="pipeline_run", id=ctx.run_id)

    while True:
        if ctx.state == PipelineRunState.INTAKE_RUNNING:
            with trace.span(name="intake"):
                listing = await intake_stub(url=ctx.jd_url)
            ctx.artifacts["job_listing"] = listing.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.001
            ctx.state = advance_state(ctx.state, PipelineRunState.RESEARCHING)
            continue

        if ctx.state == PipelineRunState.RESEARCHING:
            listing = ctx.artifacts["job_listing"]
            with trace.span(name="company_researcher"):
                research = await company_researcher_stub(company_name=listing["company_name"])
            with trace.span(name="fit_analyst"):
                fit = await fit_analyst_stub(
                    job_listing_id=listing["id"],
                    resume_markdown="[stub resume]",
                )
            ctx.artifacts["company_research"] = research.model_dump(mode="json")
            ctx.artifacts["fit_analysis"] = fit.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.05
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_FIT_APPROVAL)
            return

        if ctx.state == PipelineRunState.DRAFTING:
            listing = ctx.artifacts["job_listing"]
            with trace.span(name="cover_letter_writer"):
                letter = await cover_letter_writer_stub(
                    application_id=ctx.application_id,
                    company_name=listing["company_name"],
                )
            ctx.artifacts["cover_letter"] = letter.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.03
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_CONTENT_APPROVAL)
            return

        if ctx.state == PipelineRunState.FILLING_FORM:
            listing = ctx.artifacts.get("job_listing", {})
            application_url = listing.get("application_url", ctx.jd_url)
            letter = ctx.artifacts.get("cover_letter", {})
            with trace.span(name="form_fill"):
                result = await form_fill_stub(
                    application_url=application_url,
                    cover_letter_body=letter.get("body_markdown", ""),
                )
            ctx.artifacts["form_fill_result"] = result.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.08
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_SUBMIT_APPROVAL)
            return

        if ctx.state == PipelineRunState.SUBMITTING:
            ctx.artifacts["submission_confirmation"] = {"url": "https://stub.example/confirm"}
            with trace.span(name="memory_curator"):
                await memory_curator_stub(application_id=ctx.application_id)
            ctx.state = advance_state(ctx.state, PipelineRunState.COMPLETED)
            return

        return
