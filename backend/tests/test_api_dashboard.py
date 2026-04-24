import pytest
from httpx import ASGITransport, AsyncClient

import apply.db.session as session_module
from apply.api.main import create_app
from apply.config import get_settings


@pytest.fixture
async def app(db_session):
    """FastAPI app with a freshly built session factory bound to the
    current test's event loop. Mirrors the pattern in test_api_applications.
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


@pytest.mark.asyncio
async def test_dashboard_stats_empty(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/dashboard/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_applications"] == 0
    assert body["total_cost_usd"] == 0.0
    assert body["reply_rate"] == 0.0
    assert body["interview_rate"] == 0.0
    assert body["status_counts"] == {}


@pytest.mark.asyncio
async def test_dashboard_stats_with_applications(app, db_session):
    from apply.db.models import Application, User

    db_session.add(User(id="user-local", email="l@e.co", name="L", profile_json={}))
    await db_session.flush()

    # 3 apps: 1 SUBMITTED, 1 REPLIED, 1 INTERVIEWED
    db_session.add_all([
        Application(
            id="app-1", user_id="user-local", status="SUBMITTED",
            job_listing_json={"company_name": "A"},
            cost_breakdown_json={"per_agent_usd": {"a": 0.10}},
            fit_analysis_json={"overall_score": 70},
        ),
        Application(
            id="app-2", user_id="user-local", status="REPLIED",
            job_listing_json={"company_name": "B"},
            cost_breakdown_json={"per_agent_usd": {"a": 0.20}},
            fit_analysis_json={"overall_score": 85},
        ),
        Application(
            id="app-3", user_id="user-local", status="INTERVIEWED",
            job_listing_json={"company_name": "C"},
            cost_breakdown_json={"per_agent_usd": {"a": 0.30}},
            fit_analysis_json={"overall_score": 82},
        ),
    ])
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/dashboard/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_applications"] == 3
    assert body["total_cost_usd"] == pytest.approx(0.60)
    # reply_rate = replied-or-better / total = 2/3
    assert body["reply_rate"] == pytest.approx(2 / 3)
    assert body["interview_rate"] == pytest.approx(1 / 3)
    assert body["status_counts"]["SUBMITTED"] == 1
    assert body["status_counts"]["REPLIED"] == 1
    assert body["status_counts"]["INTERVIEWED"] == 1
    assert body["mean_fit_score"] == pytest.approx((70 + 85 + 82) / 3)
