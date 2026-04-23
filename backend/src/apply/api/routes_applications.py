import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.agents.intake import intake_stub
from apply.db.models import User as UserRow
from apply.db.session import get_session
from apply.orchestrator.events import get_event_bus
from apply.orchestrator.graph import PipelineContext, run_to_next_checkpoint
from apply.orchestrator.run_repository import RunRepository
from apply.schemas.enums import ApplicationStatus, PipelineRunState

router = APIRouter(prefix="/applications", tags=["applications"])


class CreateApplicationRequest(BaseModel):
    jd_url: HttpUrl


class CreateApplicationResponse(BaseModel):
    run_id: str
    application_id: str
    state: str


async def _ensure_local_user(session: AsyncSession, user_id: str = "user-local") -> None:
    """Ensure the local single-user row exists (V1 skeleton)."""
    existing = await session.execute(select(UserRow).where(UserRow.id == user_id))
    if existing.scalar_one_or_none() is None:
        session.add(UserRow(id=user_id, email=f"{user_id}@local", name="Local User"))
        await session.flush()


@router.post("", response_model=CreateApplicationResponse, status_code=201)
async def create_application(
    req: CreateApplicationRequest,
    session: AsyncSession = Depends(get_session),
) -> CreateApplicationResponse:
    # Preview-intake so we have a JobListing to attach to the row.
    listing = await intake_stub(url=str(req.jd_url))

    await _ensure_local_user(session)

    repo = RunRepository(session)
    app_id = await repo.create_application_row(
        user_id="user-local",
        job_listing_json=listing.model_dump(mode="json"),
        status=ApplicationStatus.DRAFTING,
    )
    run_id = await repo.create_run(
        application_id=app_id,
        initial_state=PipelineRunState.INTAKE_RUNNING,
    )

    ctx = PipelineContext(
        run_id=run_id,
        application_id=app_id,
        jd_url=str(req.jd_url),
        state=PipelineRunState.INTAKE_RUNNING,
    )
    ctx.artifacts["job_listing"] = listing.model_dump(mode="json")

    # Kick off background pipeline. Do NOT await — return response to client.
    asyncio.create_task(_drive_pipeline(run_id, ctx, repo_session=session))

    return CreateApplicationResponse(
        run_id=run_id,
        application_id=app_id,
        state=ctx.state.value,
    )


async def _drive_pipeline(run_id: str, ctx: PipelineContext, repo_session: AsyncSession) -> None:
    """Run pipeline to next HITL gate in the background and persist.

    Emits SSE events for the frontend to consume.
    """
    bus = get_event_bus()
    await bus.publish(run_id, {"type": "run_started", "state": ctx.state.value})
    try:
        await run_to_next_checkpoint(ctx)
    except Exception as e:
        await bus.publish(run_id, {"type": "error", "message": str(e)})
        return
    # Persist new state
    from apply.db.session import get_session as session_dep
    async for s in session_dep():
        repo = RunRepository(s)
        await repo.update_run(
            run_id=run_id,
            state=ctx.state,
            cost_accumulated_usd=ctx.cost_accumulated_usd,
            artifacts=ctx.artifacts,
        )
        break
    await bus.publish(
        run_id,
        {
            "type": "checkpoint_reached",
            "state": ctx.state.value,
            "artifacts": ctx.artifacts,
        },
    )
