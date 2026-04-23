import asyncio
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    """In-memory pub/sub keyed by run_id. V1 only (single-process).

    V2+ can swap for Redis pub/sub without changing this interface.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(run_id, []))
        for q in queues:
            await q.put(event)

    async def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._subscribers.setdefault(run_id, []).append(queue)
        try:
            while True:
                ev = await queue.get()
                yield ev
        finally:
            async with self._lock:
                subs = self._subscribers.get(run_id, [])
                if queue in subs:
                    subs.remove(queue)
                if not subs:
                    self._subscribers.pop(run_id, None)


# Singleton instance used by app.
_bus = EventBus()


def get_event_bus() -> EventBus:
    return _bus
