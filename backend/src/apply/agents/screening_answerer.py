from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import ScreeningAnswer


async def screening_answerer_stub(
    question: str,
    origin: ScreeningAnswerOrigin,
) -> ScreeningAnswer:
    """Phase 1 stub: returns a generic-but-plausible answer."""
    answer = (
        "I'm drawn to this role because it sits at the intersection of "
        "applied research and shipping product — both of which I've been "
        "practicing in my recent work on multi-agent systems."
    )
    return ScreeningAnswer(
        question=question,
        answer=answer,
        word_count=len(answer.split()),
        drafted_by=origin,
    )
