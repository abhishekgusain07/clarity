from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from apply.schemas.company import CompanyResearch
from apply.schemas.enums import (
    ApplicationStatus,
    HitlCheckpoint,
    HitlDecisionType,
    PipelineRunState,
)
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing
from apply.schemas.writing import CoverLetter, ScreeningAnswer


class CostBreakdown(BaseModel):
    per_agent_usd: dict[str, float] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def total_usd(self) -> float:
        return sum(self.per_agent_usd.values())


class Outcome(BaseModel):
    status: ApplicationStatus
    response_received_at: datetime | None = None
    notes: str | None = None
    next_step: str | None = None


class HitlDecision(BaseModel):
    checkpoint: HitlCheckpoint
    decision: HitlDecisionType
    user_edits: str | None = None
    notes: str | None = None
    timestamp: datetime


class PipelineRun(BaseModel):
    id: str
    application_id: str
    state: PipelineRunState
    cost_accumulated_usd: float = 0.0
    created_at: datetime
    updated_at: datetime


class Application(BaseModel):
    id: str
    user_id: str
    job_listing: JobListing
    company_research: CompanyResearch | None = None
    fit_analysis: FitAnalysis | None = None
    cover_letter: CoverLetter | None = None
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    status: ApplicationStatus
    hitl_decisions: list[HitlDecision] = Field(default_factory=list)
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    submitted_at: datetime | None = None
    outcome: Outcome | None = None
