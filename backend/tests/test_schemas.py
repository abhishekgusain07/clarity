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
