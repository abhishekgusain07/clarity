from pydantic import BaseModel, Field

from apply.schemas.enums import FitStrength, FitVerdict, RecommendedAction


class FitPoint(BaseModel):
    dimension: str
    evidence_resume: str | None
    evidence_jd: str
    strength: FitStrength


class FitAnalysis(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    verdict: FitVerdict
    matches: list[FitPoint]
    stretches: list[FitPoint]
    gaps: list[FitPoint]
    reasoning: str
    recommended_action: RecommendedAction
