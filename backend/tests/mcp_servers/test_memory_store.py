import pytest

from apply.mcp_servers.memory_mcp.store import MemoryStore


@pytest.mark.asyncio
async def test_already_applied_false_when_empty(db_session, tmp_path):
    store = MemoryStore(session=db_session, chroma_dir=tmp_path)
    assert await store.already_applied("Acme", "Engineer") is False


@pytest.mark.asyncio
async def test_log_outcome_and_retrieve(db_session, tmp_path):
    store = MemoryStore(session=db_session, chroma_dir=tmp_path)

    # Seed an application row first (FK)
    from apply.db.models import Application, User
    db_session.add(User(id="u1", email="u1@e.co", name="U1", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-1", user_id="u1", status="SUBMITTED",
        job_listing_json={"company_name": "Acme", "role_title": "Engineer"},
    ))
    await db_session.commit()

    out_id = await store.log_outcome(
        application_id="app-1",
        status="SUBMITTED",
        company_name="Acme",
        jd_url="https://acme.ai/jobs/1",
        cover_letter_text="Dear Acme, …",
        cover_letter_embedding=[0.1] * 1536,
        notes=None,
    )
    assert out_id.startswith("out-")


@pytest.mark.asyncio
async def test_already_applied_true_after_seeding(db_session, tmp_path):
    from apply.db.models import Application, User
    db_session.add(User(id="u1", email="u1@e.co", name="U1", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-1", user_id="u1", status="SUBMITTED",
        job_listing_json={"company_name": "Acme", "role_title": "Engineer"},
    ))
    await db_session.commit()

    store = MemoryStore(session=db_session, chroma_dir=tmp_path)
    assert await store.already_applied("Acme", "Engineer") is True
    assert await store.already_applied("Acme", "Designer") is False


@pytest.mark.asyncio
async def test_similar_applications_empty(db_session, tmp_path):
    store = MemoryStore(session=db_session, chroma_dir=tmp_path)
    hits = await store.similar_applications(query_embedding=[0.1] * 1536, top_k=5)
    assert hits == []
