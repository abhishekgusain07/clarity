from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from apply.schemas.enums import ApplicationStatus, PipelineRunState


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    version: Mapped[int] = mapped_column()
    pdf_path: Mapped[str] = mapped_column(String)
    markdown_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    status: Mapped[ApplicationStatus] = mapped_column(String)
    job_listing_json: Mapped[dict] = mapped_column(JSON)
    company_research_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fit_analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cover_letter_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    screening_answers_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    hitl_decisions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cost_breakdown_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outcome_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list["PipelineRun"]] = relationship(back_populates="application")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    application_id: Mapped[str] = mapped_column(String, ForeignKey("applications.id"))
    state: Mapped[PipelineRunState] = mapped_column(String)
    cost_accumulated_usd: Mapped[float] = mapped_column(Float, default=0.0)
    current_artifacts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    application: Mapped["Application"] = relationship(back_populates="runs")
