import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.db.models import Application as ApplicationRow
from apply.db.models import PipelineRun as PipelineRunRow
from apply.schemas.enums import ApplicationStatus, PipelineRunState


@dataclass
class LoadedRun:
    id: str
    application_id: str
    state: PipelineRunState
    cost_accumulated_usd: float
    artifacts: dict[str, Any]


class RunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_application_row(
        self,
        user_id: str,
        job_listing_json: dict[str, Any],
        status: ApplicationStatus,
    ) -> str:
        app_id = f"app-{uuid.uuid4().hex[:8]}"
        row = ApplicationRow(
            id=app_id,
            user_id=user_id,
            status=status,
            job_listing_json=job_listing_json,
        )
        self.session.add(row)
        await self.session.flush()
        return app_id

    async def create_run(
        self,
        application_id: str,
        initial_state: PipelineRunState,
    ) -> str:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        row = PipelineRunRow(
            id=run_id,
            application_id=application_id,
            state=initial_state,
            cost_accumulated_usd=0.0,
            current_artifacts_json={},
        )
        self.session.add(row)
        await self.session.commit()
        return run_id

    async def load_run(self, run_id: str) -> LoadedRun:
        stmt = select(PipelineRunRow).where(PipelineRunRow.id == run_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        return LoadedRun(
            id=row.id,
            application_id=row.application_id,
            state=PipelineRunState(row.state),
            cost_accumulated_usd=row.cost_accumulated_usd,
            artifacts=row.current_artifacts_json or {},
        )

    async def update_run(
        self,
        run_id: str,
        state: PipelineRunState,
        cost_accumulated_usd: float,
        artifacts: dict[str, Any],
    ) -> None:
        stmt = select(PipelineRunRow).where(PipelineRunRow.id == run_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.state = state
        row.cost_accumulated_usd = cost_accumulated_usd
        row.current_artifacts_json = artifacts
        await self.session.commit()
