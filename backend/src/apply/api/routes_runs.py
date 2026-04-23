import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from apply.api.sse import sse_stream
from apply.db.session import get_session
from apply.orchestrator.events import get_event_bus
from apply.orchestrator.graph import PipelineContext, run_to_next_checkpoint
from apply.orchestrator.run_repository import RunRepository
from apply.orchestrator.state_machine import (
    InvalidTransitionError,
    is_awaiting_user,
    next_state_after_approval,
)
from apply.schemas.enums import HitlCheckpoint, HitlDecisionType

router = APIRouter(prefix="/runs", tags=["runs"])


class RunResponse(BaseModel):
    run_id: str
    application_id: str
    state: str
    cost_accumulated_usd: float
    artifacts: dict


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> RunResponse:
    repo = RunRepository(session)
    try:
        run = await repo.load_run(run_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"run not found: {e}") from e

    return RunResponse(
        run_id=run.id,
        application_id=run.application_id,
        state=run.state.value,
        cost_accumulated_usd=run.cost_accumulated_usd,
        artifacts=run.artifacts,
    )


@router.get("/{run_id}/events")
async def run_events(run_id: str) -> EventSourceResponse:
    return EventSourceResponse(sse_stream(run_id))


class ApproveRequest(BaseModel):
    checkpoint: HitlCheckpoint
    decision: HitlDecisionType
    user_edits: str | None = None
    notes: str | None = None


class ApproveResponse(BaseModel):
    run_id: str
    new_state: str


@router.post("/{run_id}/approve", response_model=ApproveResponse)
async def approve_run(
    run_id: str,
    req: ApproveRequest,
    session: AsyncSession = Depends(get_session),
) -> ApproveResponse:
    repo = RunRepository(session)
    run = await repo.load_run(run_id)

    if not is_awaiting_user(run.state):
        raise HTTPException(
            status_code=409,
            detail=f"run is not awaiting approval (state={run.state.value})",
        )

    if req.decision != HitlDecisionType.APPROVE:
        # SKIP / CANCEL / EDIT flows extended in later phases
        raise HTTPException(
            status_code=400,
            detail=f"decision {req.decision.value} not handled in phase 1 skeleton",
        )

    try:
        new_state = next_state_after_approval(run.state)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    await repo.update_run(
        run_id=run_id,
        state=new_state,
        cost_accumulated_usd=run.cost_accumulated_usd,
        artifacts=run.artifacts,
    )

    # Drive the pipeline to the next checkpoint in the background.
    ctx = PipelineContext(
        run_id=run_id,
        application_id=run.application_id,
        jd_url=run.artifacts.get("job_listing", {}).get("url", ""),
        state=new_state,
        artifacts=run.artifacts,
        cost_accumulated_usd=run.cost_accumulated_usd,
    )
    asyncio.create_task(_continue_pipeline(run_id, ctx))

    return ApproveResponse(run_id=run_id, new_state=new_state.value)


async def _continue_pipeline(run_id: str, ctx: PipelineContext) -> None:
    from apply.db.session import get_session as session_dep

    bus = get_event_bus()
    await bus.publish(run_id, {"type": "run_resumed", "state": ctx.state.value})
    try:
        await run_to_next_checkpoint(ctx)
    except Exception as e:
        await bus.publish(run_id, {"type": "error", "message": str(e)})
        return

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
