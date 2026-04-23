import json
from collections.abc import AsyncIterator

from apply.orchestrator.events import get_event_bus


async def sse_stream(run_id: str) -> AsyncIterator[dict[str, str]]:
    """Produce SSE-formatted events for a run.

    Terminates the stream when an event contains ``final: True`` or has
    type ``completed``/``errored``. This makes the stream naturally end
    after terminal states (useful for test harnesses without real
    chunked-transfer streaming).
    """
    bus = get_event_bus()
    async for event in bus.subscribe(run_id):
        yield {"event": event.get("type", "message"), "data": json.dumps(event)}
        if event.get("final"):
            return
        if event.get("type") in {"completed", "errored"}:
            return
