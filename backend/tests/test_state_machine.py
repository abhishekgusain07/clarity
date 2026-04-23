import pytest

from apply.orchestrator.state_machine import (
    InvalidTransitionError,
    advance_state,
    can_transition,
    is_awaiting_user,
    next_state_after_approval,
)
from apply.schemas.enums import PipelineRunState


def test_happy_path_transitions_are_valid():
    path = [
        PipelineRunState.INTAKE_RUNNING,
        PipelineRunState.RESEARCHING,
        PipelineRunState.AWAITING_FIT_APPROVAL,
        PipelineRunState.DRAFTING,
        PipelineRunState.AWAITING_CONTENT_APPROVAL,
        PipelineRunState.FILLING_FORM,
        PipelineRunState.AWAITING_SUBMIT_APPROVAL,
        PipelineRunState.SUBMITTING,
        PipelineRunState.COMPLETED,
    ]
    for a, b in zip(path, path[1:], strict=False):
        assert can_transition(a, b), f"{a} -> {b} should be allowed"


def test_invalid_transition_rejected():
    assert not can_transition(
        PipelineRunState.INTAKE_RUNNING, PipelineRunState.COMPLETED
    )


def test_advance_raises_on_invalid():
    with pytest.raises(InvalidTransitionError):
        advance_state(PipelineRunState.INTAKE_RUNNING, PipelineRunState.COMPLETED)


def test_is_awaiting_user_detects_checkpoints():
    assert is_awaiting_user(PipelineRunState.AWAITING_FIT_APPROVAL)
    assert is_awaiting_user(PipelineRunState.AWAITING_CONTENT_APPROVAL)
    assert is_awaiting_user(PipelineRunState.AWAITING_SUBMIT_APPROVAL)
    assert not is_awaiting_user(PipelineRunState.RESEARCHING)
    assert not is_awaiting_user(PipelineRunState.COMPLETED)


def test_next_state_after_approval():
    assert (
        next_state_after_approval(PipelineRunState.AWAITING_FIT_APPROVAL)
        == PipelineRunState.DRAFTING
    )
    assert (
        next_state_after_approval(PipelineRunState.AWAITING_CONTENT_APPROVAL)
        == PipelineRunState.FILLING_FORM
    )
    assert (
        next_state_after_approval(PipelineRunState.AWAITING_SUBMIT_APPROVAL)
        == PipelineRunState.SUBMITTING
    )


def test_abandoned_is_terminal():
    # ABANDONED should not transition further
    assert not can_transition(
        PipelineRunState.ABANDONED, PipelineRunState.COMPLETED
    )


def test_any_state_can_transition_to_errored():
    # ERRORED is a permissible sink from any active state
    assert can_transition(PipelineRunState.INTAKE_RUNNING, PipelineRunState.ERRORED)
    assert can_transition(PipelineRunState.DRAFTING, PipelineRunState.ERRORED)
