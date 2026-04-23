from apply.schemas.enums import (
    ApplicationStatus,
    FitVerdict,
    JobSource,
    PipelineRunState,
    RecommendedAction,
    RemoteType,
)


def test_job_source_values():
    assert JobSource.YC_WAAS.value == "YC_WAAS"
    assert JobSource.GREENHOUSE.value == "GREENHOUSE"
    assert JobSource.OTHER.value == "OTHER"


def test_fit_verdict_values():
    assert FitVerdict.STRONG.value == "STRONG"
    assert FitVerdict.WEAK.value == "WEAK"


def test_recommended_action_values():
    assert RecommendedAction.PROCEED.value == "PROCEED"
    assert RecommendedAction.SKIP.value == "SKIP"


def test_pipeline_run_state_has_all_checkpoints():
    # Every HITL gate must be representable
    states = {s.value for s in PipelineRunState}
    assert "AWAITING_FIT_APPROVAL" in states
    assert "AWAITING_CONTENT_APPROVAL" in states
    assert "AWAITING_SUBMIT_APPROVAL" in states
    assert "COMPLETED" in states


def test_application_status_values():
    assert ApplicationStatus.DRAFTING.value == "DRAFTING"
    assert ApplicationStatus.SUBMITTED.value == "SUBMITTED"


def test_remote_type_values():
    assert RemoteType.REMOTE.value == "REMOTE"


from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing


def test_job_listing_minimal_valid():
    listing = JobListing(
        id="job-1",
        source=JobSource.YC_WAAS,
        url="https://workatastartup.com/jobs/123",
        application_url="https://workatastartup.com/jobs/123/apply",
        company_name="Acme AI",
        role_title="Founding Engineer",
        location="San Francisco, CA",
        remote_type=RemoteType.HYBRID,
        description_markdown="Build agents.",
        requirements=["Python", "Agents"],
        nice_to_haves=["LangGraph experience"],
        raw_html_path="/tmp/jd/job-1.html",
    )

    assert listing.id == "job-1"
    assert listing.source == JobSource.YC_WAAS
    assert len(listing.requirements) == 2
    assert listing.compensation_range is None


def test_job_listing_rejects_bad_url():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        JobListing(
            id="job-2",
            source=JobSource.OTHER,
            url="not-a-url",
            application_url="also-not-a-url",
            company_name="X",
            role_title="Y",
            location="Z",
            remote_type=RemoteType.REMOTE,
            description_markdown="",
            requirements=[],
            nice_to_haves=[],
            raw_html_path="/tmp/x",
        )


from apply.schemas.company import (
    BlogPost,
    CompanyResearch,
    Founder,
    NewsItem,
    Round,
    Source,
)


def test_company_research_with_all_subtypes():
    research = CompanyResearch(
        company_name="Acme AI",
        funding_stage="Series A",
        last_round=Round(stage="Series A", amount_usd=10_000_000, date_iso="2025-11-01"),
        team_size="20-50",
        founders=[Founder(name="A. Smith", background="ex-Google, Stanford PhD")],
        recent_news=[
            NewsItem(
                title="Acme raises Series A",
                url="https://techcrunch.com/acme-a",
                date_iso="2025-11-01",
                summary="$10M to build agents",
            )
        ],
        recent_blog_posts=[
            BlogPost(
                title="Why we build agents",
                url="https://acme.ai/blog/agents",
                summary="Product philosophy",
            )
        ],
        tech_stack_hints=["Python", "LangGraph"],
        signal_score=0.85,
        sources=[Source(url="https://acme.ai", title="Acme homepage", trust_score=0.9)],
    )

    assert research.company_name == "Acme AI"
    assert research.signal_score == 0.85
    assert len(research.founders) == 1
    assert research.last_round is not None


def test_signal_score_bounded():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CompanyResearch(
            company_name="X",
            founders=[],
            recent_news=[],
            recent_blog_posts=[],
            tech_stack_hints=[],
            signal_score=1.5,  # invalid: > 1.0
            sources=[],
        )


from apply.schemas.enums import FitStrength, FitVerdict, RecommendedAction
from apply.schemas.fit import FitAnalysis, FitPoint


def test_fit_analysis_minimal_valid():
    analysis = FitAnalysis(
        overall_score=72,
        verdict=FitVerdict.MODERATE,
        matches=[
            FitPoint(
                dimension="Python",
                evidence_resume="5 years Python, primary language",
                evidence_jd="Strong Python required",
                strength=FitStrength.STRONG,
            )
        ],
        stretches=[
            FitPoint(
                dimension="LangGraph",
                evidence_resume=None,
                evidence_jd="Experience with LangGraph preferred",
                strength=FitStrength.WEAK,
            )
        ],
        gaps=[],
        reasoning="Solid Python, thin on LangGraph but learnable.",
        recommended_action=RecommendedAction.PROCEED,
    )

    assert analysis.overall_score == 72
    assert analysis.verdict == FitVerdict.MODERATE
    assert analysis.recommended_action == RecommendedAction.PROCEED


def test_fit_score_must_be_0_to_100():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FitAnalysis(
            overall_score=150,  # invalid
            verdict=FitVerdict.STRONG,
            matches=[],
            stretches=[],
            gaps=[],
            reasoning="",
            recommended_action=RecommendedAction.PROCEED,
        )


from datetime import datetime

from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import CoverLetter, ScreeningAnswer


def test_cover_letter_valid():
    letter = CoverLetter(
        id="cl-1",
        application_id="app-1",
        draft_version=1,
        body_markdown="Dear team, ...",
        word_count=250,
        references_company_specifics=["Series A in 2025", "shipped agent framework"],
        voice_similarity_score=0.72,
        created_at=datetime(2026, 4, 23, 12, 0, 0),
    )

    assert letter.draft_version == 1
    assert letter.voice_similarity_score == 0.72


def test_screening_answer_valid():
    answer = ScreeningAnswer(
        question="Why this company?",
        answer="Because ...",
        word_count=100,
        drafted_by=ScreeningAnswerOrigin.PROACTIVE,
    )

    assert answer.drafted_by == ScreeningAnswerOrigin.PROACTIVE


from datetime import datetime

from apply.schemas.application import (
    Application,
    CostBreakdown,
    HitlDecision,
    Outcome,
    PipelineRun,
)
from apply.schemas.enums import (
    ApplicationStatus,
    HitlCheckpoint,
    HitlDecisionType,
    PipelineRunState,
)


def test_cost_breakdown_totals():
    breakdown = CostBreakdown(
        per_agent_usd={"intake": 0.001, "company_researcher": 0.05, "fit_analyst": 0.02},
    )
    assert abs(breakdown.total_usd - 0.071) < 1e-6


def test_pipeline_run_valid():
    run = PipelineRun(
        id="run-1",
        application_id="app-1",
        state=PipelineRunState.AWAITING_FIT_APPROVAL,
        cost_accumulated_usd=0.05,
        created_at=datetime(2026, 4, 23),
        updated_at=datetime(2026, 4, 23),
    )
    assert run.state == PipelineRunState.AWAITING_FIT_APPROVAL


def test_hitl_decision_valid():
    decision = HitlDecision(
        checkpoint=HitlCheckpoint.FIT,
        decision=HitlDecisionType.APPROVE,
        user_edits=None,
        notes=None,
        timestamp=datetime(2026, 4, 23),
    )
    assert decision.checkpoint == HitlCheckpoint.FIT
