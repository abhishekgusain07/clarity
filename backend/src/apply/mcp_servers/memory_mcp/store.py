"""memory-mcp storage adapter: Postgres for structured outcomes + Chroma for similarity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

import chromadb
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.db.models import Application, Outcome

_CHROMA_DIR = Path(__file__).resolve().parents[4] / "data" / "chroma"


@dataclass
class OutcomeRow:
    id: str
    application_id: str
    status: str
    notes: str | None
    company_name: str | None
    jd_url: str | None
    cover_letter_text: str | None


@dataclass
class SimilarApplication:
    application_id: str
    company_name: str | None
    cover_letter_text: str | None
    similarity: float


class MemoryStore:
    def __init__(self, session: AsyncSession, chroma_dir: Path | None = None):
        self.session = session
        self._chroma_dir = chroma_dir or _CHROMA_DIR
        self._chroma_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self._chroma_dir))
        self._collection = client.get_or_create_collection("cover_letters")

    async def already_applied(self, company_name: str, role_title: str) -> bool:
        stmt = select(Application).where(
            Application.job_listing_json["company_name"].as_string() == company_name
        )
        result = await self.session.execute(stmt)
        apps = result.scalars().all()
        for app in apps:
            if app.job_listing_json.get("role_title") == role_title:
                return True
        return False

    async def log_outcome(
        self,
        application_id: str,
        status: str,
        company_name: str | None,
        jd_url: str | None,
        cover_letter_text: str | None,
        cover_letter_embedding: list[float] | None,
        notes: str | None = None,
    ) -> str:
        outcome_id = f"out-{uuid.uuid4().hex[:8]}"
        row = Outcome(
            id=outcome_id,
            application_id=application_id,
            status=status,
            notes=notes,
            company_name=company_name,
            jd_url=jd_url,
            cover_letter_text=cover_letter_text,
        )
        self.session.add(row)
        await self.session.commit()

        if cover_letter_embedding is not None and cover_letter_text:
            self._collection.add(
                ids=[outcome_id],
                embeddings=[cover_letter_embedding],
                documents=[cover_letter_text],
                metadatas=[{
                    "application_id": application_id,
                    "company_name": company_name or "",
                    "status": status,
                }],
            )
        return outcome_id

    async def similar_applications(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[SimilarApplication]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["metadatas", "documents", "distances"],
        )
        out: list[SimilarApplication] = []
        ids = results.get("ids", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        docs = results.get("documents", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for i, meta in enumerate(metas):
            sim = 1.0 - float(dists[i])  # chroma returns distance; convert
            out.append(
                SimilarApplication(
                    application_id=meta.get("application_id", ids[i]),
                    company_name=meta.get("company_name"),
                    cover_letter_text=docs[i],
                    similarity=max(0.0, min(1.0, sim)),
                )
            )
        return out

    async def what_landed_replies(self, top_k: int = 10) -> list[OutcomeRow]:
        stmt = select(Outcome).where(Outcome.status.in_(["REPLIED", "INTERVIEWED", "OFFERED"]))
        result = await self.session.execute(stmt.limit(top_k))
        rows = result.scalars().all()
        return [
            OutcomeRow(
                id=r.id,
                application_id=r.application_id,
                status=r.status,
                notes=r.notes,
                company_name=r.company_name,
                jd_url=r.jd_url,
                cover_letter_text=r.cover_letter_text,
            )
            for r in rows
        ]
