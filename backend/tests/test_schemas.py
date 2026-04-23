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
