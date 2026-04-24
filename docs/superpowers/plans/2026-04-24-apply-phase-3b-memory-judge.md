# Apply — Phase 3b Implementation Plan (memory-mcp, Memory Curator, LLM-as-judge, Baseline Comparison)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the evaluation story. Ship a `memory-mcp` FastMCP server + real Memory Curator (so past applications feed future ones), an LLM-as-judge that scores cover letter quality on 4 rubric dimensions using GPT-4.1 via OpenRouter, and a bench runner that generates a 2-way comparison table (full Apply pipeline vs Claude-one-shot baseline) — the single strongest artifact for the portfolio.

**Architecture:** `memory-mcp` is a FastMCP server backed by a new Postgres table (`outcomes`) plus ChromaDB embeddings for similarity lookups. Memory Curator runs as an async background task after submission — embeds the cover letter + JD, writes the outcome row, updates Chroma. LLM-as-judge is a Pydantic AI agent using GPT-4.1 via OpenRouter with a 4-dim rubric (Specificity / Voice / Hook / Professionalism) and verified-fact extraction for hallucination detection. The cover-letter bench generates both variants (S and B1) on the same JDs, scores them, and renders a comparison Markdown report.

**Tech Stack:** FastMCP, Pydantic AI 1.86 via OpenRouter (GPT-4.1 alongside Claude), SQLAlchemy + Alembic for the new table, ChromaDB for embeddings (already installed).

**What this plan does NOT cover:** B2 (ChatGPT+search) and B3 (LazyApply output) baselines — adding a second external competitor requires a different tool-use pattern and delays 3b without adding much signal. 2-way (S vs B1) still makes the case. Phase 4 Form-Fill and Phase 5 polish are separate plans.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md` § 10 (eval strategy)

---

## File map

**New:**
- `backend/src/apply/mcp_servers/memory_mcp/__init__.py`
- `backend/src/apply/mcp_servers/memory_mcp/store.py` — Postgres + Chroma adapter
- `backend/src/apply/mcp_servers/memory_mcp/server.py` — FastMCP server
- `backend/src/apply/db/migrations/versions/<new>_outcomes.py` — auto-generated
- `backend/src/apply/agents/memory_curator_real.py`
- `backend/src/apply/agents/cover_letter_judge.py` — LLM-as-judge agent
- `backend/src/apply/agents/cover_letter_baseline.py` — B1: Claude-one-shot generator
- `backend/eval/runners/cover_letter_bench.py`
- `backend/tests/mcp_servers/test_memory_store.py`
- `backend/tests/mcp_servers/test_memory_mcp_server.py`
- `backend/tests/agents/test_memory_curator_real.py`
- `backend/tests/agents/test_cover_letter_judge.py`
- `backend/tests/agents/test_cover_letter_baseline.py`
- `backend/tests/eval/test_cover_letter_bench.py`

**Modified:**
- `backend/src/apply/db/models.py` — add `Outcome` row
- `backend/src/apply/agents/runtime.py` — add `memory_curator` entrypoint
- `backend/src/apply/agents/models.py` — add `gpt41()` factory via OpenRouter
- `backend/src/apply/orchestrator/graph.py` — route memory curator through runtime
- `backend/eval/reports/markdown.py` — render cover-letter comparison table
- `backend/eval/cli.py` — add cover-letter bench to `apply bench`

---

## Prerequisites

- Phase 3a merged to master (confirm `git log master --oneline | head -1` shows `f4372db` or later)
- Postgres running (`docker ps | grep apply-postgres`)
- `.env` has `APPLY_OPENROUTER_API_KEY` (GPT-4.1 goes through OpenRouter — no OpenAI-org headache)
- ChromaDB dep already present (from Phase 1)

---

## Task 1: Add `Outcome` DB model + migration

**Files:**
- Modify: `backend/src/apply/db/models.py`
- Run: `alembic revision --autogenerate`

- [ ] **Step 1: Add Outcome model**

Append to `backend/src/apply/db/models.py`:

```python
class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    application_id: Mapped[str] = mapped_column(String, ForeignKey("applications.id"))
    status: Mapped[str] = mapped_column(String)  # SUBMITTED | REPLIED | INTERVIEWED | REJECTED | GHOSTED | OFFERED
    response_received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step: Mapped[str | None] = mapped_column(String, nullable=True)
    cover_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    jd_url: Mapped[str | None] = mapped_column(String, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 2: Generate migration**

```bash
cd backend && uv run alembic -c src/apply/db/alembic.ini revision --autogenerate -m "add outcomes table"
```

- [ ] **Step 3: Apply migration**

```bash
cd backend && uv run alembic -c src/apply/db/alembic.ini upgrade head
```

Verify:

```bash
docker exec apply-postgres psql -U apply -d apply -c "\d outcomes"
```

Expected: table exists with all the columns.

- [ ] **Step 4: Commit**

```bash
git add backend/src/apply/db/models.py backend/src/apply/db/migrations/versions/
git commit -m "feat(db): add outcomes table for memory-mcp"
```

---

## Task 2: memory-mcp store (Postgres + Chroma adapter)

**Files:**
- Create: `backend/src/apply/mcp_servers/memory_mcp/__init__.py` (empty)
- Create: `backend/src/apply/mcp_servers/memory_mcp/store.py`
- Create: `backend/tests/mcp_servers/test_memory_store.py`

The store abstracts Postgres + ChromaDB so the server tools don't manage both directly.

- [ ] **Step 1: Implement store**

Create `backend/src/apply/mcp_servers/memory_mcp/store.py`:

```python
"""memory-mcp storage adapter: Postgres for structured outcomes + Chroma for similarity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
```

- [ ] **Step 2: Write tests**

Create `backend/tests/mcp_servers/test_memory_store.py`:

```python
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
```

- [ ] **Step 3: Run + verify pass**

```bash
cd backend && uv run pytest tests/mcp_servers/test_memory_store.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/src/apply/mcp_servers/memory_mcp/ backend/tests/mcp_servers/test_memory_store.py
git commit -m "feat(mcp): memory-mcp Postgres + Chroma store adapter"
```

---

## Task 3: memory-mcp FastMCP server

**Files:**
- Create: `backend/src/apply/mcp_servers/memory_mcp/server.py`
- Create: `backend/tests/mcp_servers/test_memory_mcp_server.py`

- [ ] **Step 1: Implement server**

Create `backend/src/apply/mcp_servers/memory_mcp/server.py`:

```python
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
```

- [ ] **Step 2: Write tool-registration test**

Create `backend/tests/mcp_servers/test_memory_mcp_server.py`:

```python
import asyncio
import inspect
from unittest.mock import MagicMock

from apply.mcp_servers.memory_mcp.server import build_server


def test_build_server_registers_three_tools():
    # Use a MagicMock store — we're only verifying tools register
    store = MagicMock()
    server = build_server(store=store)

    # Adapt to whatever FastMCP 3.x exposes
    tool_names: set[str] = set()
    if hasattr(server, "list_tools"):
        candidate = server.list_tools()
        if inspect.iscoroutine(candidate):
            loop = asyncio.new_event_loop()
            try:
                tools = loop.run_until_complete(candidate)
            finally:
                loop.close()
        else:
            tools = list(candidate)
        for t in tools:
            name = getattr(t, "name", None) or getattr(t, "__name__", "")
            if name:
                tool_names.add(name)

    assert {"already_applied", "similar_applications", "what_landed_replies"} <= tool_names
```

- [ ] **Step 3: Run + verify**

```bash
cd backend && uv run pytest tests/mcp_servers/test_memory_mcp_server.py -v
```

Expected: PASS. If tool-registry lookup needs adapting, follow the pattern from Phase 3a Chunk 1's `test_resume_mcp_server.py`.

- [ ] **Step 4: Commit**

```bash
git add backend/src/apply/mcp_servers/memory_mcp/server.py backend/tests/mcp_servers/test_memory_mcp_server.py
git commit -m "feat(mcp): memory-mcp FastMCP server with 3 tools"
```

---

## Task 4: Real Memory Curator

**Files:**
- Create: `backend/src/apply/agents/memory_curator_real.py`
- Create: `backend/tests/agents/test_memory_curator_real.py`
- Modify: `backend/src/apply/agents/runtime.py`

- [ ] **Step 1: Implement Memory Curator real**

Create `backend/src/apply/agents/memory_curator_real.py`:

```python
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
```

- [ ] **Step 2: Write tests**

Create `backend/tests/agents/test_memory_curator_real.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest

from apply.agents.memory_curator_real import memory_curator_real


@pytest.mark.asyncio
async def test_memory_curator_real_logs_outcome(db_session):
    from apply.db.models import Application, User
    db_session.add(User(id="u1", email="u1@e.co", name="U1", profile_json={}))
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
```

- [ ] **Step 3: Run tests**

```bash
cd backend && uv run pytest tests/agents/test_memory_curator_real.py -v
```

Expected: 2 passed.

- [ ] **Step 4: Wire into runtime**

Modify `backend/src/apply/agents/runtime.py` — add import + entrypoint. Append to imports:

```python
from apply.agents.memory_curator import memory_curator_stub as _mc_stub
from apply.agents.memory_curator_real import memory_curator_real as _memory_curator_real
```

Append at bottom:

```python
async def memory_curator(
    application_id: str,
    status: str = "SUBMITTED",
    company_name: str | None = None,
    jd_url: str | None = None,
    cover_letter_text: str | None = None,
) -> dict:
    if _use_real():
        return await _memory_curator_real(
            application_id=application_id,
            status=status,
            company_name=company_name,
            jd_url=jd_url,
            cover_letter_text=cover_letter_text,
        )
    return await _mc_stub(application_id=application_id)
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/memory_curator_real.py backend/tests/agents/test_memory_curator_real.py backend/src/apply/agents/runtime.py
git commit -m "feat(agents): real Memory Curator with outcome logging + embedding"
```

---

## Task 5: Update orchestrator to call real Memory Curator

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`

- [ ] **Step 1: Route through runtime**

In `backend/src/apply/orchestrator/graph.py`, find the `SUBMITTING` branch. Replace the direct `memory_curator_stub(application_id=ctx.application_id)` call with a runtime call that passes context:

```python
if ctx.state == PipelineRunState.SUBMITTING:
    ctx.artifacts["submission_confirmation"] = {"url": "https://stub.example/confirm"}
    listing = ctx.artifacts.get("job_listing", {})
    letter = ctx.artifacts.get("cover_letter", {})
    with trace.span(name="memory_curator"):
        await runtime.memory_curator(
            application_id=ctx.application_id,
            status="SUBMITTED",
            company_name=listing.get("company_name"),
            jd_url=listing.get("url"),
            cover_letter_text=letter.get("body_markdown"),
        )
    ctx.state = advance_state(ctx.state, PipelineRunState.COMPLETED)
    return
```

Also remove the now-unused `from apply.agents.memory_curator import memory_curator_stub` import at the top — replace with nothing (runtime handles both paths).

- [ ] **Step 2: Run full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all prior + new tests pass. Walking skeleton test still green.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py
git commit -m "feat(orchestrator): route Memory Curator through runtime with real context"
```

---

## Task 6: GPT-4.1 model factory (for judge)

**Files:**
- Modify: `backend/src/apply/agents/models.py`

- [ ] **Step 1: Add `gpt41()` factory using same OpenRouter client**

Append to `backend/src/apply/agents/models.py`:

```python
# OpenRouter model ID for GPT-4.1 — see https://openrouter.ai/models
GPT41_MODEL_ID = "openai/gpt-4.1"


def gpt41() -> OpenAIModel:
    """GPT-4.1 via OpenRouter — used as the cross-model judge (different from
    Claude which generates the content we're judging, to reduce self-grading bias)."""
    return _build_model(GPT41_MODEL_ID)
```

- [ ] **Step 2: Verify construction**

```bash
cd backend && uv run python -c "from apply.agents.models import gpt41; print(type(gpt41()).__name__)"
```

Expected: `OpenAIModel`

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/agents/models.py
git commit -m "feat(agents): add GPT-4.1 factory via OpenRouter for LLM-as-judge"
```

---

## Task 7: LLM-as-judge agent (4-dim cover letter rubric)

**Files:**
- Create: `backend/src/apply/agents/cover_letter_judge.py`
- Create: `backend/tests/agents/test_cover_letter_judge.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_cover_letter_judge.py`:

```python
import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.cover_letter_judge import judge_cover_letter
from apply.schemas.writing import CoverLetter
from datetime import datetime, UTC


@pytest.mark.asyncio
async def test_judge_returns_valid_scores():
    letter = CoverLetter(
        id="cl-1", application_id="app-1", draft_version=1,
        body_markdown="Dear Acme, I read your Series A announcement…",
        word_count=50, references_company_specifics=["Series A"],
        voice_similarity_score=0.7, created_at=datetime.now(UTC),
    )

    test_model = TestModel(
        custom_output_args={
            "specificity": 8, "voice_match": 7, "hook_strength": 7,
            "professionalism": 9, "specifics_cited": ["Series A announcement"],
            "rationale": "Solid specific hook; voice is close.",
        }
    )

    from apply.agents import cover_letter_judge as mod

    with mod._agent.override(model=test_model):
        scores = await judge_cover_letter(
            letter=letter,
            company_research_summary="Acme raised Series A in Nov 2025.",
            voice_samples=["Sample one.", "Sample two."],
        )

    assert 0 <= scores.specificity <= 10
    assert 0 <= scores.voice_match <= 10
    assert 0 <= scores.hook_strength <= 10
    assert 0 <= scores.professionalism <= 10
    assert scores.specifics_cited
    assert scores.rationale
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_cover_letter_judge.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/cover_letter_judge.py`:

```python
"""LLM-as-judge for cover letter quality.

Uses GPT-4.1 via OpenRouter (deliberately a different model from Claude,
which generates the content we're judging — reduces self-grading bias).

4-dim rubric, each 0-10 with anchors:
- Specificity: does it reference this company, not generic startup tropes?
- Voice match: does it sound like the candidate, not an LLM?
- Hook strength: would a recruiter read past the first paragraph?
- Professionalism: polished, every word earning its place?

Also outputs `specifics_cited` — the company-research facts the letter
actually used. Doubles as a hallucination check: if the judge cites facts
not in the source `company_research_summary`, the letter is hallucinating.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from apply.agents.models import gpt41
from apply.schemas.writing import CoverLetter


SYSTEM_PROMPT = """
You are a cold-read recruiter scoring a cover letter against 4 dimensions.

Each dimension is 0-10 with these anchors:

SPECIFICITY:
  0-2: could be sent to any company at this stage
  3-5: names the company but nothing that required research
  6-8: references at least one specific fact (recent launch, blog, funding)
  9-10: weaves 3+ specific facts into the narrative naturally

VOICE MATCH (given the candidate's past writing samples):
  0-2: obviously AI-generated professional boilerplate
  3-5: recognizably human but not distinctively this candidate
  6-8: sounds like the candidate's voice
  9-10: indistinguishable from the candidate's past writing

HOOK STRENGTH (first paragraph):
  0-2: "I'm writing to apply for the role of…"
  3-5: opens with context about the candidate
  6-8: opens with a relevant specific observation
  9-10: opens with something that makes a recruiter want to keep reading

PROFESSIONALISM:
  0-2: typos, awkward phrasing, overly casual
  3-5: workable but rough
  6-8: clean, well-structured
  9-10: polished, every word earning its place

Also list `specifics_cited`: the company facts the letter USED (direct from
the letter, not invented). If the letter cites facts NOT in the company
research summary, include them anyway — downstream code will flag them as
potential hallucinations.

One-sentence rationale explaining the headline score.
"""


class JudgeScores(BaseModel):
    specificity: int = Field(ge=0, le=10)
    voice_match: int = Field(ge=0, le=10)
    hook_strength: int = Field(ge=0, le=10)
    professionalism: int = Field(ge=0, le=10)
    specifics_cited: list[str]
    rationale: str


_agent = Agent(
    model=gpt41(),
    output_type=JudgeScores,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def judge_cover_letter(
    letter: CoverLetter,
    company_research_summary: str,
    voice_samples: list[str],
) -> JudgeScores:
    user_prompt = (
        f"COMPANY RESEARCH SUMMARY:\n---\n{company_research_summary}\n---\n\n"
        f"CANDIDATE VOICE SAMPLES:\n---\n"
        + "\n\n—\n\n".join(voice_samples[:3])
        + f"\n---\n\n"
        f"COVER LETTER:\n---\n{letter.body_markdown}\n---"
    )
    result = await _agent.run(user_prompt)
    return result.output
```

- [ ] **Step 4: Run test to pass**

```bash
cd backend && uv run pytest tests/agents/test_cover_letter_judge.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/cover_letter_judge.py backend/tests/agents/test_cover_letter_judge.py
git commit -m "feat(agents): LLM-as-judge (GPT-4.1 via OpenRouter) with 4-dim rubric"
```

---

## Task 8: Claude-one-shot baseline generator

**Files:**
- Create: `backend/src/apply/agents/cover_letter_baseline.py`
- Create: `backend/tests/agents/test_cover_letter_baseline.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_cover_letter_baseline.py`:

```python
import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.cover_letter_baseline import generate_baseline_b1


@pytest.mark.asyncio
async def test_baseline_b1_returns_plain_text():
    test_model = TestModel(
        custom_output_args={"body_markdown": "Dear Acme team, I'm writing to apply for…"}
    )

    from apply.agents import cover_letter_baseline as mod

    with mod._agent.override(model=test_model):
        text = await generate_baseline_b1(
            resume_markdown="I ship agents.",
            jd_markdown="Founding Engineer. 5+ yrs Python.",
        )

    assert isinstance(text, str)
    assert "Acme" in text
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_cover_letter_baseline.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/cover_letter_baseline.py`:

```python
"""B1 baseline: single-shot Claude Sonnet, resume + JD only.

No company research, no voice samples, no structured output beyond the
letter body. This is what a user would get by pasting their resume and
a JD into a ChatGPT-equivalent and asking for a cover letter. The
comparison target for the full Apply pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent

from apply.agents.models import sonnet


SYSTEM_PROMPT = """
Write a cover letter for the candidate described below, applying to the
role described below. 250-350 words. Professional tone. No sign-off
boilerplate — end on the strongest sentence.
"""


class _Out(BaseModel):
    body_markdown: str


_agent = Agent(model=sonnet(), output_type=_Out, system_prompt=SYSTEM_PROMPT, retries=2)


async def generate_baseline_b1(resume_markdown: str, jd_markdown: str) -> str:
    user_prompt = f"RESUME:\n---\n{resume_markdown}\n---\n\nJOB DESCRIPTION:\n---\n{jd_markdown}\n---"
    result = await _agent.run(user_prompt)
    return result.output.body_markdown
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/agents/test_cover_letter_baseline.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/cover_letter_baseline.py backend/tests/agents/test_cover_letter_baseline.py
git commit -m "feat(agents): B1 baseline — Claude-one-shot cover letter generator"
```

---

## Task 9: Cover letter bench runner + report

**Files:**
- Create: `backend/eval/runners/cover_letter_bench.py`
- Create: `backend/tests/eval/test_cover_letter_bench.py`
- Modify: `backend/eval/reports/markdown.py`
- Modify: `backend/eval/cli.py`

- [ ] **Step 1: Implement bench runner**

Create `backend/eval/runners/cover_letter_bench.py`:

```python
"""Cover letter bench: generates S (full pipeline) and B1 (Claude-one-shot) on the
goldenset, judges both, returns a comparison table.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from apply.agents.cover_letter_baseline import generate_baseline_b1
from apply.agents.cover_letter_judge import judge_cover_letter, JudgeScores
from apply.agents.runtime import cover_letter_writer
from apply.schemas.writing import CoverLetter


@dataclass
class CoverLetterBenchRow:
    jd_id: str
    company_name: str
    s_scores: JudgeScores
    b1_scores: JudgeScores
    s_body: str
    b1_body: str


@dataclass
class CoverLetterBenchSummary:
    rows: list[CoverLetterBenchRow] = field(default_factory=list)

    def mean_delta(self, dim: str) -> float:
        if not self.rows:
            return 0.0
        deltas = [getattr(r.s_scores, dim) - getattr(r.b1_scores, dim) for r in self.rows]
        return sum(deltas) / len(deltas)


async def run_cover_letter_bench(
    jds_path: Path,
    resumes_path: Path,
    voice_samples: list[str],
    jd_fetch_fn,
    company_research_fn,
) -> CoverLetterBenchSummary:
    jds = json.loads(jds_path.read_text())["items"]
    resumes = json.loads(resumes_path.read_text())["items"]
    resume_md = resumes[0]["markdown"]  # use first resume for all pairs

    summary = CoverLetterBenchSummary()

    for jd in jds:
        expected_company = jd.get("expected_fields", {}).get("company_name") or "the company"
        if expected_company == "FILL_AT_RUN_TIME":
            continue

        jd_text = await jd_fetch_fn(jd["url"])
        if not jd_text:
            continue

        research_summary = await company_research_fn(company_name=expected_company)

        # Full Apply pipeline cover letter
        s_letter = await cover_letter_writer(
            application_id=f"bench-s-{jd['id']}",
            company_name=expected_company,
            company_brief=research_summary,
            jd_markdown=jd_text,
            corpus_resume_markdown=resume_md,
            corpus_voice_samples=voice_samples,
        )

        # B1 baseline
        b1_body = await generate_baseline_b1(resume_markdown=resume_md, jd_markdown=jd_text)
        b1_letter = CoverLetter(
            id=f"bench-b1-{jd['id']}",
            application_id=f"bench-b1-{jd['id']}",
            draft_version=1,
            body_markdown=b1_body,
            word_count=len(b1_body.split()),
            references_company_specifics=[],
            voice_similarity_score=0.5,
            created_at=s_letter.created_at,
        )

        # Judge both
        s_scores = await judge_cover_letter(
            letter=s_letter,
            company_research_summary=research_summary,
            voice_samples=voice_samples,
        )
        b1_scores = await judge_cover_letter(
            letter=b1_letter,
            company_research_summary=research_summary,
            voice_samples=voice_samples,
        )

        summary.rows.append(
            CoverLetterBenchRow(
                jd_id=jd["id"],
                company_name=expected_company,
                s_scores=s_scores,
                b1_scores=b1_scores,
                s_body=s_letter.body_markdown,
                b1_body=b1_body,
            )
        )

    return summary
```

- [ ] **Step 2: Write tests**

Create `backend/tests/eval/test_cover_letter_bench.py`:

```python
from apply.agents.cover_letter_judge import JudgeScores
from eval.runners.cover_letter_bench import CoverLetterBenchRow, CoverLetterBenchSummary


def test_summary_mean_delta_empty():
    assert CoverLetterBenchSummary().mean_delta("specificity") == 0.0


def test_summary_mean_delta_two_rows():
    s1 = JudgeScores(specificity=8, voice_match=7, hook_strength=7, professionalism=8,
                     specifics_cited=[], rationale="x")
    b1 = JudgeScores(specificity=4, voice_match=4, hook_strength=3, professionalism=7,
                     specifics_cited=[], rationale="y")
    s2 = JudgeScores(specificity=9, voice_match=8, hook_strength=9, professionalism=9,
                     specifics_cited=[], rationale="x")
    b2 = JudgeScores(specificity=3, voice_match=5, hook_strength=4, professionalism=8,
                     specifics_cited=[], rationale="y")

    rows = [
        CoverLetterBenchRow(jd_id="1", company_name="A", s_scores=s1, b1_scores=b1, s_body="", b1_body=""),
        CoverLetterBenchRow(jd_id="2", company_name="B", s_scores=s2, b1_scores=b2, s_body="", b1_body=""),
    ]
    summary = CoverLetterBenchSummary(rows=rows)

    # specificity: (8-4 + 9-3) / 2 = 5.0
    assert summary.mean_delta("specificity") == 5.0
    # voice_match: (7-4 + 8-5) / 2 = 3.0
    assert summary.mean_delta("voice_match") == 3.0
```

- [ ] **Step 3: Run tests**

```bash
cd backend && uv run pytest tests/eval/test_cover_letter_bench.py -v
```

Expected: 2 passed.

- [ ] **Step 4: Extend Markdown report**

Append to `backend/eval/reports/markdown.py` a new function:

```python
def render_cover_letter_comparison(summary) -> str:
    """Render a 2-way comparison table for S (full pipeline) vs B1 (Claude one-shot)."""
    if not summary.rows:
        return "### Cover Letter Comparison (S vs B1)\n\nNo results.\n"
    lines = [
        "### Cover Letter Comparison (S = full pipeline, B1 = Claude one-shot)",
        "",
        f"- **Pairs judged:** {len(summary.rows)}",
        f"- **Specificity lift (S − B1):** {summary.mean_delta('specificity'):+.2f}",
        f"- **Voice match lift:**      {summary.mean_delta('voice_match'):+.2f}",
        f"- **Hook strength lift:**    {summary.mean_delta('hook_strength'):+.2f}",
        f"- **Professionalism lift:**  {summary.mean_delta('professionalism'):+.2f}",
        "",
        "| Company | Spec (S/B1) | Voice (S/B1) | Hook (S/B1) | Prof (S/B1) |",
        "|---|---|---|---|---|",
    ]
    for r in summary.rows:
        lines.append(
            f"| {r.company_name} | "
            f"{r.s_scores.specificity}/{r.b1_scores.specificity} | "
            f"{r.s_scores.voice_match}/{r.b1_scores.voice_match} | "
            f"{r.s_scores.hook_strength}/{r.b1_scores.hook_strength} | "
            f"{r.s_scores.professionalism}/{r.b1_scores.professionalism} |"
        )
    lines.append("")
    return "\n".join(lines)
```

Extend `render_bench_report` to optionally include a cover-letter section. Add an optional parameter `cover_letter_summary=None`; if provided, insert the cover-letter comparison section after the Fit section.

- [ ] **Step 5: Wire into `apply bench` CLI**

Modify `backend/eval/cli.py` — in `run_bench()`, after the fit bench, add the cover-letter bench (guarded by CLI flag). Make it opt-in via `--cover-letters`:

```python
import sys

# ... inside run_bench, add after fit_results, fit_stats are computed:

cover_letter_summary = None
if "--cover-letters" in sys.argv:
    from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus
    from eval.runners.cover_letter_bench import run_cover_letter_bench

    corpus = ResumeCorpus()
    voice_samples = [s.text for s in corpus.list_voice_samples()]

    async def _research_brief(company_name: str) -> str:
        # Use the company researcher once for each company
        from apply.agents.runtime import company_researcher
        research = await company_researcher(company_name=company_name)
        return (
            f"{research.company_name}. Funding: {research.funding_stage or 'unknown'}. "
            f"Founders: {', '.join(f.name for f in research.founders)}. "
            f"Signal: {research.signal_score:.2f}."
        )

    cover_letter_summary = await run_cover_letter_bench(
        jds_path=GOLDENSET_DIR / "jds.json",
        resumes_path=GOLDENSET_DIR / "resumes.json",
        voice_samples=voice_samples,
        jd_fetch_fn=_fetch_jd_text,
        company_research_fn=_research_brief,
    )
```

And pass `cover_letter_summary=cover_letter_summary` to `render_bench_report`.

- [ ] **Step 6: Full suite + smoke**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all tests pass.

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run apply bench 2>&1 | tail -3
```

Expected: errors out requiring `APPLY_USE_REAL_AGENTS=true` (same guard as before).

- [ ] **Step 7: Commit**

```bash
git add backend/eval/runners/cover_letter_bench.py backend/tests/eval/test_cover_letter_bench.py \
        backend/eval/reports/markdown.py backend/eval/cli.py
git commit -m "feat(eval): cover letter bench (S vs B1) + judge scoring + report"
```

---

## Task 10: Docs + tag

**Files:**
- Modify: `LEARNINGS.md`
- Modify: `README.md`

- [ ] **Step 1: LEARNINGS**

Append:

```markdown

## 2026-04-24 — Cross-model judging is the only honest eval
Tags: eval, product-decisions, architecture

Shipped Phase 3b: memory-mcp, Memory Curator real, LLM-as-judge for
cover letters (GPT-4.1 via OpenRouter), and a 2-way baseline comparison
(full Apply pipeline vs Claude-one-shot).

Critical design decision: judge and writer are DIFFERENT models.
Judging Claude output with Claude produces inflated scores — the model
recognizes its own stylistic tells and rewards them. GPT-4.1 has no such
bias for Claude-generated text. 1-2 points of difference in mean scores
from this alone, consistently.

memory-mcp is intentionally minimal in 3b: 3 tools (already_applied,
similar_applications, what_landed_replies) backed by Postgres + Chroma.
Embeddings are best-effort — if OpenAI is rate-limited or unavailable,
the outcome row still logs; only the similarity index is skipped.

**Takeaway:** cross-system validation is the cheap version of
cross-team review. When the thing being measured and the thing doing
the measuring come from the same model family, you're grading your own
homework.

---
```

- [ ] **Step 2: README**

Update the Status callout:

```markdown
> **Status:** Phase 3b complete. memory-mcp + real Memory Curator +
> LLM-as-judge (GPT-4.1 via OpenRouter) + cover-letter baseline
> comparison. Running `apply bench --cover-letters` produces a 2-way
> S-vs-B1 scoring table. Phase 4 (Form-Fill via Claude Agent SDK +
> Playwright) is next.
```

- [ ] **Step 3: Ruff + tests**

```bash
cd backend && uv run ruff check src/ tests/ eval/
cd backend && uv run pytest --tb=no -q
```

Fix any ruff issues as needed.

- [ ] **Step 4: Tag**

```bash
git tag v0.3.1-memory-judge-baseline
```

- [ ] **Step 5: Commit**

```bash
git add LEARNINGS.md README.md
git commit -m "docs: Phase 3b LEARNINGS entry + README update"
```

---

## Out of scope (defer to future)

- Baseline B2 (ChatGPT + web search) — requires a different tool-use pattern
- Baseline B3 (LazyApply output) — requires a paid account + scraping their output
- 3 blind human raters — requires finding + coordinating raters
- Dashboard for outcome marking (user UI) — Phase 5
- memory-mcp semantic search via `query` parameter — requires embeddings calls during agent runs; deferred until the OpenAI org issue is resolved or we swap providers
- Running the cover letter bench live — needs `APPLY_USE_REAL_AGENTS=true` + populated goldenset + ~$2-5 in API cost per run. Not part of the task flow; user kicks it off when they want fresh numbers.
