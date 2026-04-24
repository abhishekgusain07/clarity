import pytest
from httpx import ASGITransport, AsyncClient

import apply.db.session as session_module
from apply.api.main import create_app
from apply.config import get_settings


@pytest.fixture
async def app(db_session):
    """FastAPI app with a freshly built session factory bound to the
    current test's event loop. The module-level ``_session_factory`` is
    repointed to this new factory for the duration of the test so that
    in-route dependencies and background tasks share one engine/loop.
    """
    # Dispose any engine left over from a previous test's loop and
    # re-create bound to the loop running this test.
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


@pytest.mark.asyncio
async def test_post_applications_creates_run(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/applications",
            json={"jd_url": "https://workatastartup.com/jobs/123"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["run_id"].startswith("run-")
    assert body["application_id"].startswith("app-")
    assert body["state"] in {"INTAKE_RUNNING", "AWAITING_FIT_APPROVAL"}


import asyncio


@pytest.mark.asyncio
async def test_get_run_returns_state_and_artifacts(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/applications",
            json={"jd_url": "https://workatastartup.com/jobs/456"},
        )
        run_id = create.json()["run_id"]

        # Give the background task a moment to run
        await asyncio.sleep(0.2)

        response = await client.get(f"/runs/{run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["state"] in {"AWAITING_FIT_APPROVAL", "INTAKE_RUNNING", "RESEARCHING"}
    assert "artifacts" in body


@pytest.mark.asyncio
async def test_approve_advances_state(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/applications",
            json={"jd_url": "https://workatastartup.com/jobs/789"},
        )
        run_id = create.json()["run_id"]

        # Wait for pipeline to reach HITL #1
        for _ in range(20):
            await asyncio.sleep(0.05)
            check = await client.get(f"/runs/{run_id}")
            if check.json()["state"] == "AWAITING_FIT_APPROVAL":
                break
        else:
            pytest.fail("pipeline did not reach AWAITING_FIT_APPROVAL")

        approve = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "FIT", "decision": "APPROVE"},
        )
        assert approve.status_code == 200

        # Wait for pipeline to reach HITL #2
        for _ in range(20):
            await asyncio.sleep(0.05)
            check = await client.get(f"/runs/{run_id}")
            if check.json()["state"] == "AWAITING_CONTENT_APPROVAL":
                break
        else:
            pytest.fail("pipeline did not reach AWAITING_CONTENT_APPROVAL")


@pytest.mark.asyncio
async def test_list_applications_empty(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/applications")

    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0}


@pytest.mark.asyncio
async def test_list_applications_returns_summaries(app, db_session):
    from apply.db.models import Application, User

    db_session.add(User(id="user-local", email="local@apply.dev", name="Local", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-1",
        user_id="user-local",
        status="SUBMITTED",
        job_listing_json={
            "id": "job-1",
            "company_name": "Acme AI",
            "role_title": "Founding Engineer",
            "url": "https://example.com/jobs/1",
        },
        fit_analysis_json={"overall_score": 78, "verdict": "MODERATE"},
        cost_breakdown_json={"per_agent_usd": {"intake": 0.001, "researcher": 0.05}},
    ))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/applications")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["id"] == "app-1"
    assert item["company_name"] == "Acme AI"
    assert item["role_title"] == "Founding Engineer"
    assert item["status"] == "SUBMITTED"
    assert item["fit_score"] == 78
    assert item["cost_usd"] == pytest.approx(0.051)


@pytest.mark.asyncio
async def test_update_outcome_new(app, db_session):
    from apply.db.models import Application, User

    db_session.add(User(id="user-local", email="l@e.co", name="L", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-2", user_id="user-local", status="SUBMITTED",
        job_listing_json={"company_name": "Acme", "role_title": "E"},
    ))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/applications/app-2/outcome",
            json={"status": "REPLIED", "notes": "Recruiter reached out"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["application_id"] == "app-2"
    assert body["status"] == "REPLIED"
    assert body["notes"] == "Recruiter reached out"


@pytest.mark.asyncio
async def test_update_outcome_404_on_unknown_app(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/applications/nonexistent/outcome",
            json={"status": "REPLIED"},
        )
    assert response.status_code == 404
