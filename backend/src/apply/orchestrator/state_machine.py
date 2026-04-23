from apply.schemas.enums import PipelineRunState

S = PipelineRunState

# Allowed forward transitions. Keys are sources; values are allowed targets.
_ALLOWED: dict[PipelineRunState, set[PipelineRunState]] = {
    S.INTAKE_RUNNING: {S.RESEARCHING, S.ERRORED},
    S.RESEARCHING: {S.AWAITING_FIT_APPROVAL, S.ERRORED},
    S.AWAITING_FIT_APPROVAL: {S.DRAFTING, S.ABANDONED, S.ERRORED},
    S.DRAFTING: {S.AWAITING_CONTENT_APPROVAL, S.ERRORED},
    S.AWAITING_CONTENT_APPROVAL: {S.DRAFTING, S.FILLING_FORM, S.ABANDONED, S.ERRORED},
    S.FILLING_FORM: {S.AWAITING_SUBMIT_APPROVAL, S.ERRORED},
    S.AWAITING_SUBMIT_APPROVAL: {S.SUBMITTING, S.ABANDONED, S.ERRORED},
    S.SUBMITTING: {S.COMPLETED, S.ERRORED},
    S.COMPLETED: set(),
    S.ABANDONED: set(),
    S.ERRORED: set(),
}

_AWAITING_USER: set[PipelineRunState] = {
    S.AWAITING_FIT_APPROVAL,
    S.AWAITING_CONTENT_APPROVAL,
    S.AWAITING_SUBMIT_APPROVAL,
}

_APPROVAL_NEXT: dict[PipelineRunState, PipelineRunState] = {
    S.AWAITING_FIT_APPROVAL: S.DRAFTING,
    S.AWAITING_CONTENT_APPROVAL: S.FILLING_FORM,
    S.AWAITING_SUBMIT_APPROVAL: S.SUBMITTING,
}


class InvalidTransitionError(ValueError):
    pass


def can_transition(src: PipelineRunState, dst: PipelineRunState) -> bool:
    return dst in _ALLOWED.get(src, set())


def advance_state(src: PipelineRunState, dst: PipelineRunState) -> PipelineRunState:
    if not can_transition(src, dst):
        raise InvalidTransitionError(f"{src} -> {dst} is not allowed")
    return dst


def is_awaiting_user(state: PipelineRunState) -> bool:
    return state in _AWAITING_USER


def next_state_after_approval(state: PipelineRunState) -> PipelineRunState:
    if state not in _APPROVAL_NEXT:
        raise InvalidTransitionError(f"{state} is not an approval checkpoint")
    return _APPROVAL_NEXT[state]
