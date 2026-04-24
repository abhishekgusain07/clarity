"""memory-mcp — FastMCP server exposing past-application memory."""
from __future__ import annotations

from fastmcp import FastMCP

from apply.mcp_servers.memory_mcp.store import MemoryStore


def build_server(store: MemoryStore) -> FastMCP:
    server: FastMCP = FastMCP(name="memory-mcp")

    @server.tool()
    async def already_applied(company_name: str, role_title: str) -> bool:
        """True if the user has already applied to this company for this role."""
        return await store.already_applied(company_name=company_name, role_title=role_title)

    @server.tool()
    async def similar_applications(query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Return up to top_k past applications with cover letters similar to the query embedding."""
        hits = await store.similar_applications(query_embedding=query_embedding, top_k=top_k)
        return [
            {
                "application_id": h.application_id,
                "company_name": h.company_name,
                "cover_letter_text": h.cover_letter_text,
                "similarity": h.similarity,
            }
            for h in hits
        ]

    @server.tool()
    async def what_landed_replies(top_k: int = 10) -> list[dict]:
        """Return outcomes where the user received a reply (REPLIED/INTERVIEWED/OFFERED)."""
        rows = await store.what_landed_replies(top_k=top_k)
        return [
            {
                "id": r.id,
                "application_id": r.application_id,
                "status": r.status,
                "company_name": r.company_name,
                "cover_letter_text": r.cover_letter_text,
            }
            for r in rows
        ]

    return server
