from datetime import datetime

from pydantic import BaseModel, Field

from apply.schemas.enums import ScreeningAnswerOrigin


class CoverLetter(BaseModel):
    id: str
    application_id: str
    draft_version: int = Field(ge=1)
    body_markdown: str
    word_count: int = Field(ge=0)
    references_company_specifics: list[str]
    voice_similarity_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime


class ScreeningAnswer(BaseModel):
    question: str
    answer: str
    word_count: int = Field(ge=0)
    drafted_by: ScreeningAnswerOrigin
