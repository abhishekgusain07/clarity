import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

import apply.db.session as session_module
from apply.api.main import create_app
from apply.config import get_settings


@pytest.fixture
async def app(db_session):
    """Mirror test_api_applications's fixture: rebind the module-level
    session factory to this test's loop so the app + background tasks
    share one engine/loop binding.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    settings = get_settings()
    fresh_engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    fresh_factory = async_sessionmaker(fresh_engine, expire_on_commit=False)

    old_factory = session_module._session_factory
    old_engine = session_module._engine
    session_module._session_factory = fresh_factory
    session_module._engine = fresh_engine

    try:
        yield create_app()
    finally:
        await fresh_engine.dispose()
        session_module._session_factory = old_factory
        session_module._engine = old_engine


async def _wait_for_state(client, run_id: str, target: str, timeout: float = 3.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        r = await client.get(f"/runs/{run_id}")
        if r.json()["state"] == target:
            return
        await asyncio.sleep(0.05)
    raise AssertionError(f"state {target} not reached within {timeout}s")


@pytest.mark.asyncio
async def test_full_stub_pipeline_paste_to_completed(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. paste URL
        create = await client.post(
            "/applications",
            json={"jd_url": "https://workatastartup.com/jobs/e2e"},
        )
        assert create.status_code == 201
        run_id = create.json()["run_id"]

        # 2. reach HITL #1
        await _wait_for_state(client, run_id, "AWAITING_FIT_APPROVAL")

        # 3. approve fit gate
        r = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "FIT", "decision": "APPROVE"},
        )
        assert r.status_code == 200

        # 4. reach HITL #2
        await _wait_for_state(client, run_id, "AWAITING_CONTENT_APPROVAL")

        # 5. approve content
        r = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "CONTENT", "decision": "APPROVE"},
        )
        assert r.status_code == 200

        # 6. reach HITL #3
        await _wait_for_state(client, run_id, "AWAITING_SUBMIT_APPROVAL")

        # 7. approve submission
        r = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "SUBMIT", "decision": "APPROVE"},
        )
        assert r.status_code == 200

        # 8. reach terminal state
        await _wait_for_state(client, run_id, "COMPLETED")

        # 9. verify artifacts exist
        final = await client.get(f"/runs/{run_id}")
        artifacts = final.json()["artifacts"]
        assert "job_listing" in artifacts
        assert "company_research" in artifacts
        assert "fit_analysis" in artifacts
        assert "cover_letter" in artifacts
        assert "form_fill_result" in artifacts
