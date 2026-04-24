from unittest.mock import patch

import pytest

from apply.agents.memory_curator_real import memory_curator_real


@pytest.mark.asyncio
async def test_memory_curator_real_logs_outcome(db_session):
    from apply.db.models import Application, User
    db_session.add(User(id="u1", email="u1@e.co", name="U1", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-1", user_id="u1", status="SUBMITTED",
        job_listing_json={"company_name": "Acme", "role_title": "Eng"},
    ))
    await db_session.commit()

    async def fake_embed(text):
        return [0.1] * 1536

    # Patch the session dep and the embed function to control behavior
    with patch("apply.agents.memory_curator_real.embed_text", side_effect=fake_embed):
        async def _session_gen():
            yield db_session
        with patch("apply.agents.memory_curator_real.get_session", return_value=_session_gen()):
            result = await memory_curator_real(
                application_id="app-1",
                status="SUBMITTED",
                company_name="Acme",
                jd_url="https://acme.ai/j/1",
                cover_letter_text="Dear Acme, …",
            )

    assert result["indexed"] is True
    assert result["outcome_id"].startswith("out-")


@pytest.mark.asyncio
async def test_memory_curator_real_handles_embed_failure(db_session):
    from apply.db.models import Application, User
    db_session.add(User(id="u1", email="u1@e.co", name="U1", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-2", user_id="u1", status="SUBMITTED",
        job_listing_json={"company_name": "Acme", "role_title": "Eng"},
    ))
    await db_session.commit()

    async def failing_embed(text):
        raise Exception("OpenAI 401")

    with patch("apply.agents.memory_curator_real.embed_text", side_effect=failing_embed):
        async def _session_gen():
            yield db_session
        with patch("apply.agents.memory_curator_real.get_session", return_value=_session_gen()):
            result = await memory_curator_real(
                application_id="app-2",
                status="SUBMITTED",
                company_name="Acme",
                jd_url=None,
                cover_letter_text="Dear…",
            )

    assert result["indexed"] is False
    assert result["outcome_id"].startswith("out-")
