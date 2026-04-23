from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from apply.api.sse import sse_stream
from apply.db.session import get_session
from apply.orchestrator.run_repository import RunRepository

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
