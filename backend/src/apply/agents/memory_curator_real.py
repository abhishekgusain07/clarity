"""Memory Curator — async post-submission. Logs outcome + embeds cover letter."""
from __future__ import annotations

from apply.agents.voice_similarity import embed_text
from apply.db.session import get_session
from apply.mcp_servers.memory_mcp.store import MemoryStore


async def memory_curator_real(
    application_id: str,
    status: str,
    company_name: str | None,
    jd_url: str | None,
    cover_letter_text: str | None,
) -> dict:
    """Embed the cover letter and log an Outcome row. Returns {indexed, outcome_id}."""
    embedding: list[float] | None = None
    if cover_letter_text:
        try:
            embedding = await embed_text(cover_letter_text)
        except Exception:
            # If embedding fails (e.g., OpenAI org issue), still log the outcome
            embedding = None

    async for session in get_session():
        store = MemoryStore(session=session)
        outcome_id = await store.log_outcome(
            application_id=application_id,
            status=status,
            company_name=company_name,
            jd_url=jd_url,
            cover_letter_text=cover_letter_text,
            cover_letter_embedding=embedding,
        )
        return {"indexed": embedding is not None, "outcome_id": outcome_id}

    return {"indexed": False, "outcome_id": None}
