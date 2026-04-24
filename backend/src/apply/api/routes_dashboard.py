from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.db.models import Application as ApplicationRow
from apply.db.session import get_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStatsResponse(BaseModel):
    total_applications: int
    total_cost_usd: float
    reply_rate: float  # replied-or-better / total
    interview_rate: float  # interviewed-or-better / total
    status_counts: dict[str, int]
    mean_fit_score: float | None


REPLIED_OR_BETTER = {"REPLIED", "INTERVIEWED", "OFFERED"}
INTERVIEWED_OR_BETTER = {"INTERVIEWED", "OFFERED"}


@router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    result = await session.execute(select(ApplicationRow))
    rows = result.scalars().all()

    if not rows:
        return DashboardStatsResponse(
            total_applications=0,
            total_cost_usd=0.0,
            reply_rate=0.0,
            interview_rate=0.0,
            status_counts={},
            mean_fit_score=None,
        )

    total_cost = 0.0
    fit_scores: list[int] = []
    status_counter: Counter = Counter()
    for row in rows:
        cost = (row.cost_breakdown_json or {}).get("per_agent_usd", {})
        if cost:
            total_cost += float(sum(cost.values()))
        fit = (row.fit_analysis_json or {}).get("overall_score")
        if fit is not None:
            fit_scores.append(int(fit))
        status_counter[str(row.status)] += 1

    total = len(rows)
    replied = sum(status_counter[s] for s in REPLIED_OR_BETTER)
    interviewed = sum(status_counter[s] for s in INTERVIEWED_OR_BETTER)
    mean_fit = sum(fit_scores) / len(fit_scores) if fit_scores else None

    return DashboardStatsResponse(
        total_applications=total,
        total_cost_usd=total_cost,
        reply_rate=replied / total,
        interview_rate=interviewed / total,
        status_counts=dict(status_counter),
        mean_fit_score=mean_fit,
    )
