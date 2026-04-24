from dataclasses import dataclass, field
from typing import Any

from apply.agents import runtime
from apply.agents.form_fill import form_fill_stub
from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus
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
    jd_text: str = ""
    resume_markdown: str = ""


def _load_corpus_once(ctx: PipelineContext) -> None:
    """Populate ctx.resume_markdown and ctx.artifacts['voice_samples'].

    Reads from resume-mcp's backing corpus. Done eagerly at the top of
    RESEARCHING so downstream states have both.
    """
    if ctx.resume_markdown:
        return  # already loaded
    corpus = ResumeCorpus()
    ctx.resume_markdown = corpus.resume_markdown()
    samples = corpus.list_voice_samples()
    ctx.artifacts["voice_samples"] = [s.text for s in samples]


async def run_to_next_checkpoint(ctx: PipelineContext) -> None:
    lf = get_langfuse()
    trace = lf.trace(name="pipeline_run", id=ctx.run_id)

    while True:
        if ctx.state == PipelineRunState.INTAKE_RUNNING:
            with trace.span(name="intake"):
                listing = await runtime.intake(
                    url=ctx.jd_url,
                    jd_text=ctx.jd_text,
                    raw_html_path=f"/tmp/apply/{ctx.run_id}.html",
                )
            ctx.artifacts["job_listing"] = listing.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.001
            ctx.state = advance_state(ctx.state, PipelineRunState.RESEARCHING)
            continue

        if ctx.state == PipelineRunState.RESEARCHING:
            _load_corpus_once(ctx)
            listing = ctx.artifacts["job_listing"]
            with trace.span(name="company_researcher"):
                research = await runtime.company_researcher(
                    company_name=listing["company_name"],
                )
            with trace.span(name="fit_analyst"):
                fit = await runtime.fit_analyst(
                    resume_markdown=ctx.resume_markdown,
                    jd_markdown=listing["description_markdown"],
                    company_brief=f"{research.company_name}: {research.signal_score:.2f} signal",
                )
            ctx.artifacts["company_research"] = research.model_dump(mode="json")
            ctx.artifacts["fit_analysis"] = fit.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.05
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_FIT_APPROVAL)
            return

        if ctx.state == PipelineRunState.DRAFTING:
            _load_corpus_once(ctx)
            listing = ctx.artifacts["job_listing"]
            research = ctx.artifacts.get("company_research", {})
            samples: list[str] = ctx.artifacts.get("voice_samples", [])
            brief = (
                f"{research.get('company_name', listing['company_name'])} — "
                f"stage: {research.get('funding_stage') or 'unknown'}, "
                f"signal: {research.get('signal_score', 0):.2f}"
            )
            with trace.span(name="cover_letter_writer"):
                letter = await runtime.cover_letter_writer(
                    application_id=ctx.application_id,
                    company_name=listing["company_name"],
                    company_brief=brief,
                    jd_markdown=listing["description_markdown"],
                    corpus_resume_markdown=ctx.resume_markdown,
                    corpus_voice_samples=samples,
                )
            ctx.artifacts["cover_letter"] = letter.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.05
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
            listing = ctx.artifacts.get("job_listing", {})
            letter = ctx.artifacts.get("cover_letter", {})
            with trace.span(name="memory_curator"):
                await runtime.memory_curator(
                    application_id=ctx.application_id,
                    status="SUBMITTED",
                    company_name=listing.get("company_name"),
                    jd_url=listing.get("url"),
                    cover_letter_text=letter.get("body_markdown"),
                )
            ctx.state = advance_state(ctx.state, PipelineRunState.COMPLETED)
            return

        return
