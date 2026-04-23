import asyncio

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from apply.agents import runtime
from apply.config import get_settings
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


async def _ensure_local_user(session: AsyncSession) -> str:
    from sqlalchemy import select

    result = await session.execute(select(UserRow).where(UserRow.id == "user-local"))
    existing = result.scalar_one_or_none()
    if existing is None:
        session.add(
            UserRow(
                id="user-local",
                email="local@apply.dev",
                name="Local Dev",
                profile_json={},
            )
        )
        await session.flush()
    return "user-local"


async def _fetch_jd_text(url: str) -> str:
    """Fetch the JD as markdown via Firecrawl; fall back to raw HTTP if unconfigured."""
    settings = get_settings()
    if settings.firecrawl_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
                    json={"url": url, "formats": ["markdown"]},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    md = data.get("markdown") or data.get("content")
                    if md:
                        return md
        except Exception:
            pass
    # Fallback: plain HTTP, return raw body text
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            return resp.text[:50_000]
    except Exception:
        return ""


@router.post("", response_model=CreateApplicationResponse, status_code=201)
async def create_application(
    req: CreateApplicationRequest,
    session: AsyncSession = Depends(get_session),
) -> CreateApplicationResponse:
    settings = get_settings()
    jd_text = ""
    if settings.apply_use_real_agents:
        jd_text = await _fetch_jd_text(str(req.jd_url))

    user_id = await _ensure_local_user(session)

    # Preview listing so we can attach something to the Application row.
    # Uses runtime (stub in dev-default, real if flag on).
    listing = await runtime.intake(
        url=str(req.jd_url),
        jd_text=jd_text,
        raw_html_path="/tmp/apply/intake-preview.html",
    )

    repo = RunRepository(session)
    app_id = await repo.create_application_row(
        user_id=user_id,
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
        jd_text=jd_text,
    )
    ctx.artifacts["job_listing"] = listing.model_dump(mode="json")

    asyncio.create_task(_drive_pipeline(run_id, ctx))

    return CreateApplicationResponse(
        run_id=run_id,
        application_id=app_id,
        state=ctx.state.value,
    )


async def _drive_pipeline(run_id: str, ctx: PipelineContext) -> None:
    bus = get_event_bus()
    await bus.publish(run_id, {"type": "run_started", "state": ctx.state.value})
    try:
        await run_to_next_checkpoint(ctx)
    except Exception as e:
        await bus.publish(run_id, {"type": "error", "message": str(e)})
        return

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
