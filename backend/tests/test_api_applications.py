import pytest
from httpx import ASGITransport, AsyncClient

from apply.api.main import create_app


@pytest.fixture
def app():
    return create_app()


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
