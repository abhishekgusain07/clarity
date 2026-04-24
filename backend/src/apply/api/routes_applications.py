import asyncio
import uuid
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.agents import runtime
from apply.config import get_settings
from apply.db.models import Application as ApplicationRow
from apply.db.models import Outcome as OutcomeRow
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


class ApplicationSummary(BaseModel):
    id: str
    company_name: str
    role_title: str
    status: str
    fit_score: int | None
    cost_usd: float
    created_at: str
    url: str | None


class ListApplicationsResponse(BaseModel):
    items: list[ApplicationSummary]
    total: int


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


@router.get("", response_model=ListApplicationsResponse)
async def list_applications(
    session: AsyncSession = Depends(get_session),
) -> ListApplicationsResponse:
    stmt = select(ApplicationRow).order_by(desc(ApplicationRow.created_at))
    result = await session.execute(stmt)
    rows = result.scalars().all()

    items: list[ApplicationSummary] = []
    for row in rows:
        jd = row.job_listing_json or {}
        fit = row.fit_analysis_json or {}
        cost = (row.cost_breakdown_json or {}).get("per_agent_usd", {})
        items.append(
            ApplicationSummary(
                id=row.id,
                company_name=jd.get("company_name", ""),
                role_title=jd.get("role_title", ""),
                status=str(row.status),
                fit_score=fit.get("overall_score"),
                cost_usd=float(sum(cost.values())) if cost else 0.0,
                created_at=row.created_at.isoformat() if row.created_at else "",
                url=jd.get("url"),
            )
        )

    return ListApplicationsResponse(items=items, total=len(items))


class OutcomeUpdateRequest(BaseModel):
    status: Literal["SUBMITTED", "REPLIED", "INTERVIEWED", "REJECTED", "GHOSTED", "OFFERED"]
    notes: str | None = None
    next_step: str | None = None


class OutcomeUpdateResponse(BaseModel):
    application_id: str
    outcome_id: str
    status: str
    notes: str | None
    next_step: str | None


@router.patch("/{application_id}/outcome", response_model=OutcomeUpdateResponse)
async def update_outcome(
    application_id: str,
    req: OutcomeUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> OutcomeUpdateResponse:
    result = await session.execute(
        select(ApplicationRow).where(ApplicationRow.id == application_id)
    )
    app_row = result.scalar_one_or_none()
    if app_row is None:
        raise HTTPException(status_code=404, detail=f"application {application_id} not found")

    # Pull company + url from the stored JSON listing for denormalization
    listing = app_row.job_listing_json or {}

    outcome_id = f"out-{uuid.uuid4().hex[:8]}"
    outcome_row = OutcomeRow(
        id=outcome_id,
        application_id=application_id,
        status=req.status,
        notes=req.notes,
        next_step=req.next_step,
        company_name=listing.get("company_name"),
        jd_url=listing.get("url"),
        cover_letter_text=(app_row.cover_letter_json or {}).get("body_markdown"),
    )
    session.add(outcome_row)

    # Also update the application's top-level status for display consistency
    app_row.status = req.status
    await session.commit()

    return OutcomeUpdateResponse(
        application_id=application_id,
        outcome_id=outcome_id,
        status=req.status,
        notes=req.notes,
        next_step=req.next_step,
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
