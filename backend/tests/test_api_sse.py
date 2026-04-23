import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from apply.api.main import create_app
from apply.orchestrator.events import get_event_bus


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_sse_stream_delivers_events(app):
    transport = ASGITransport(app=app)
    bus = get_event_bus()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async def publish_later():
            await asyncio.sleep(0.05)
            await bus.publish("test-run", {"type": "agent_start", "name": "intake"})
            await asyncio.sleep(0.05)
            await bus.publish("test-run", {"type": "checkpoint_reached", "final": True})

        publisher = asyncio.create_task(publish_later())

        collected: list[str] = []
        async with client.stream("GET", "/runs/test-run/events") as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    collected.append(line)
                if "final" in line:
                    break

        await publisher

    assert len(collected) >= 2
    assert any("intake" in l for l in collected)
    assert any("checkpoint_reached" in l for l in collected)
