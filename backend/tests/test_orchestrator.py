import pytest

from apply.orchestrator.graph import (
    PipelineContext,
    run_to_next_checkpoint,
)
from apply.schemas.enums import PipelineRunState


@pytest.mark.asyncio
async def test_run_from_start_stops_at_fit_checkpoint():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.INTAKE_RUNNING,
    )

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.AWAITING_FIT_APPROVAL
    assert ctx.artifacts.get("job_listing") is not None
    assert ctx.artifacts.get("company_research") is not None
    assert ctx.artifacts.get("fit_analysis") is not None


@pytest.mark.asyncio
async def test_run_from_fit_approval_stops_at_content_checkpoint():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.DRAFTING,
    )
    # Seed the upstream artifact needed by cover_letter_writer
    ctx.artifacts["job_listing"] = {"id": "job-stub", "company_name": "Acme AI"}

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.AWAITING_CONTENT_APPROVAL
    assert ctx.artifacts.get("cover_letter") is not None


@pytest.mark.asyncio
async def test_run_from_content_approval_stops_at_submit_checkpoint():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.FILLING_FORM,
    )
    # Seed the upstream artifacts needed by form_fill
    ctx.artifacts["cover_letter"] = {"body_markdown": "Dear team, ..."}

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.AWAITING_SUBMIT_APPROVAL
    assert ctx.artifacts.get("form_fill_result") is not None


@pytest.mark.asyncio
async def test_run_from_submitting_reaches_completed():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.SUBMITTING,
    )

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.COMPLETED
