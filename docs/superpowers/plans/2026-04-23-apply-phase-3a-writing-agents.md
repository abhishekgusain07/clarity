# Apply — Phase 3a Implementation Plan (Real Writing Agents + resume-mcp)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the two writing-phase stubs (Cover Letter Writer + Screening Answerer) with real LLM-backed agents that read the user's resume + voice corpus via a custom `resume-mcp` FastMCP server, and compute voice-similarity scores via OpenAI embeddings so HITL #2 can show the user how "them-sounding" each draft is.

**Architecture:** A custom FastMCP server (`resume-mcp`) serves the user's resume + profile + voice corpus as MCP tools. The Cover Letter Writer agent (Pydantic AI + Sonnet 4.6) attaches this server as a toolset, pulls relevant voice samples + profile fields during drafting, and outputs a `CoverLetter` with a voice_similarity_score computed as max cosine similarity between the draft and the user's samples using OpenAI's `text-embedding-3-small`. The Screening Answerer (Sonnet single-shot) reuses the same MCP server for per-question answers. Both agents route through `apply.agents.runtime` so the stub path still works when `APPLY_USE_REAL_AGENTS=false`.

**Tech Stack:** FastMCP (for the custom MCP server), Pydantic AI 1.86 (OpenAI via OpenRouter), OpenAI embeddings API (`text-embedding-3-small`) — separate from the Claude LLM routing, uses the existing `OPENAI_API_KEY` env var, numpy for cosine similarity.

**What this plan does NOT cover:** `memory-mcp`, Memory Curator real implementation, LLM-as-judge rubric on writing quality, baseline comparison table against competitors — all Phase 3b.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md` § 6 (Writer agent, Screening Answerer, voice-similarity)

---

## File map

**New files:**
- `backend/seed/__init__.py`
- `backend/seed/profile.json` — one-off seed for the user's profile fields (name, email, etc.)
- `backend/seed/resume.md` — seed resume (starts as goldenset `resume-python-ai`; user can replace)
- `backend/seed/voice_samples.json` — 3–5 writing samples in the user's voice
- `backend/src/apply/mcp_servers/__init__.py`
- `backend/src/apply/mcp_servers/resume_mcp/__init__.py`
- `backend/src/apply/mcp_servers/resume_mcp/server.py` — FastMCP server
- `backend/src/apply/mcp_servers/resume_mcp/corpus.py` — in-process corpus loader (used by both the MCP server AND tests)
- `backend/src/apply/agents/voice_similarity.py` — OpenAI-embedding cosine-max helper
- `backend/src/apply/agents/cover_letter_writer_real.py`
- `backend/src/apply/agents/screening_answerer_real.py`
- `backend/tests/mcp_servers/__init__.py`
- `backend/tests/mcp_servers/test_corpus.py`
- `backend/tests/mcp_servers/test_resume_mcp_server.py`
- `backend/tests/agents/test_voice_similarity.py`
- `backend/tests/agents/test_cover_letter_writer_real.py`
- `backend/tests/agents/test_screening_answerer_real.py`

**Modified files:**
- `backend/pyproject.toml` — add `fastmcp>=2.0`, `numpy` already transitive
- `backend/src/apply/agents/runtime.py` — add `cover_letter_writer` and `screening_answerer` entrypoints
- `backend/src/apply/orchestrator/graph.py` — route these two through runtime instead of direct stub calls
- `LEARNINGS.md` — append entry

---

## Prerequisites

- Phase 2b merged to master (confirm `git log master --oneline | head -5` shows `abf3e39` or later)
- `.env` at repo root has `APPLY_OPENROUTER_API_KEY`, `OPENAI_API_KEY` (the embeddings use OpenAI directly, not via OpenRouter), `APPLY_USE_REAL_AGENTS` set per your preference

---

## Task 1: Add FastMCP dependency + seed fixtures

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/seed/__init__.py`
- Create: `backend/seed/profile.json`
- Create: `backend/seed/resume.md`
- Create: `backend/seed/voice_samples.json`

- [ ] **Step 1: Add fastmcp to dependencies**

In `backend/pyproject.toml`, add to the `dependencies` list (before the closing `]`):

```toml
    "fastmcp>=2.0.0",
```

- [ ] **Step 2: Sync**

```bash
cd backend && uv sync
```

Expected: fastmcp installed. Verify:

```bash
uv run python -c "from fastmcp import FastMCP; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Create seed package**

```bash
mkdir -p backend/seed
touch backend/seed/__init__.py
```

- [ ] **Step 4: Create `backend/seed/profile.json`**

```json
{
  "name": "Sanyam Upadhyay",
  "email": "satish@team.galaxy.ai",
  "phone": "",
  "linkedin_url": "",
  "github_url": "https://github.com/sanyamupadhyay",
  "portfolio_url": "",
  "location": "Remote",
  "work_auth": "OPEN_TO_DISCUSS",
  "salary_expectation_usd": null,
  "remote_preference": "REMOTE_OK"
}
```

- [ ] **Step 5: Create `backend/seed/resume.md`** (copy from goldenset; user can edit later)

```markdown
# Sanyam Upadhyay

satish@team.galaxy.ai · github.com/sanyamupadhyay · Remote

## Summary

Engineer focused on applied AI systems. Recent work on multi-agent
orchestration (Pydantic AI, MCP, Claude Agent SDK) and eval-driven
development. Comfortable with async Python, Postgres, and production
observability.

## Experience

**Apply — Autonomous Job-Application Agent** (side project, 2026)
- Designed and shipped a 7-agent research-and-applications pipeline
  with 3 human-in-the-loop checkpoints (LangGraph-equivalent state
  machine persisted in Postgres).
- Built 2 custom FastMCP servers; integrated Tavily + Firecrawl +
  Playwright MCP for tool access.
- Routed Claude through OpenRouter with custom HTTP-Referer/X-Title
  headers for portability.
- Eval harness with bench runners for field recall, fact recall, and
  Pearson correlation with expert-labeled fit scores.

**Prior engineering experience**
- Async Python systems, Postgres, Redis, FastAPI/TanStack.
- Experience with LLM-backed products, RAG, and agent frameworks.

## Skills

Python (expert), async/await, FastAPI, SQLAlchemy, Postgres, Redis,
Pydantic AI, MCP, Claude Agent SDK, OpenAI SDK, Docker, observability
(Langfuse, OpenTelemetry), React/TanStack.
```

(If the user wants to replace this with their real resume later, it's a single file edit.)

- [ ] **Step 6: Create `backend/seed/voice_samples.json`**

Three seed samples that capture a "thoughtful + specific + not boilerplate" voice. The user can append their own real samples later.

```json
{
  "version": 1,
  "samples": [
    {
      "id": "sample-1",
      "kind": "cover_letter",
      "text": "I read your Series A announcement last week — the framing of agents as products rather than features resonated with work I've been doing independently. Over the last six months I've shipped a 7-agent research pipeline (Pydantic AI, MCP, Claude Agent SDK) with a real HITL state machine and an eval harness that tracks regression on every prompt change. I'd like to bring that same engineering discipline to your team."
    },
    {
      "id": "sample-2",
      "kind": "cover_letter",
      "text": "Your engineering blog post on long-running agents captured exactly the problem I've been wrestling with: the difference between a chat interface and a research product. I built an applications copilot in this space because I wanted to experience that gap from the builder side. The thing I'd most like to talk about is how your team thinks about evaluation — I suspect that's where the real engineering work lives."
    },
    {
      "id": "sample-3",
      "kind": "essay",
      "text": "The best AI systems I've built weren't the clever ones — they were the ones I could actually debug. That meant structured outputs, typed agent boundaries, and traces I could read. It meant an eval harness that fit in a Markdown report I could paste into a PR. When people ask me what I've learned from shipping agents, it's: the discipline that makes a good backend codebase also makes a good agent codebase. Nothing in the stack gets to be mystical."
    }
  ]
}
```

- [ ] **Step 7: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/seed/
git commit -m "chore(seed): add fastmcp dep + seed resume/profile/voice samples"
```

---

## Task 2: Corpus loader (shared by MCP server + tests)

**Files:**
- Create: `backend/src/apply/mcp_servers/__init__.py`
- Create: `backend/src/apply/mcp_servers/resume_mcp/__init__.py`
- Create: `backend/src/apply/mcp_servers/resume_mcp/corpus.py`
- Create: `backend/tests/mcp_servers/__init__.py`
- Create: `backend/tests/mcp_servers/test_corpus.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/mcp_servers/__init__.py` (empty).

Create `backend/tests/mcp_servers/test_corpus.py`:

```python
from pathlib import Path

import pytest

from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus


@pytest.fixture
def corpus(tmp_path) -> ResumeCorpus:
    # Build a self-contained corpus at a tmp_path; don't depend on real seed files
    profile = tmp_path / "profile.json"
    profile.write_text(
        '{"name":"Test User","email":"t@example.com","phone":"","linkedin_url":"",'
        '"github_url":"","portfolio_url":"","location":"Remote","work_auth":"",'
        '"salary_expectation_usd":null,"remote_preference":"REMOTE_OK"}'
    )
    resume = tmp_path / "resume.md"
    resume.write_text("# Test User\n\n## Skills\nPython, async.\n")
    samples = tmp_path / "voice_samples.json"
    samples.write_text(
        '{"version":1,"samples":['
        '{"id":"s1","kind":"cover_letter","text":"I love shipping reliable agent systems."},'
        '{"id":"s2","kind":"essay","text":"Debugging agents starts with a readable trace."}'
        "]}"
    )
    return ResumeCorpus(seed_dir=tmp_path)


def test_load_resume_markdown(corpus):
    md = corpus.resume_markdown()
    assert "Test User" in md
    assert "Python" in md


def test_get_profile_field_existing(corpus):
    assert corpus.profile_field("name") == "Test User"
    assert corpus.profile_field("location") == "Remote"


def test_get_profile_field_missing(corpus):
    assert corpus.profile_field("nonexistent") is None


def test_list_voice_samples(corpus):
    samples = corpus.list_voice_samples()
    assert len(samples) == 2
    assert {s.id for s in samples} == {"s1", "s2"}


def test_find_voice_samples_returns_all_when_unfiltered(corpus):
    hits = corpus.find_voice_samples(query=None, kind=None, top_k=10)
    assert len(hits) == 2


def test_find_voice_samples_filters_by_kind(corpus):
    hits = corpus.find_voice_samples(query=None, kind="essay", top_k=10)
    assert len(hits) == 1
    assert hits[0].id == "s2"


def test_find_voice_samples_top_k(corpus):
    hits = corpus.find_voice_samples(query=None, kind=None, top_k=1)
    assert len(hits) == 1
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/mcp_servers/test_corpus.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apply.mcp_servers'`.

- [ ] **Step 3: Create package + corpus loader**

Create `backend/src/apply/mcp_servers/__init__.py` (empty).
Create `backend/src/apply/mcp_servers/resume_mcp/__init__.py` (empty).

Create `backend/src/apply/mcp_servers/resume_mcp/corpus.py`:

```python
"""In-process loader for the user's resume + profile + voice corpus.

The resume-mcp server wraps this in MCP tools, but it's also directly
importable for tests and for agents that want to bypass the MCP layer.
The seed files live at the repo's `backend/seed/` directory by default;
tests pass an override via `seed_dir=tmp_path`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_SEED_DIR = Path(__file__).resolve().parents[4] / "seed"


@dataclass(frozen=True)
class VoiceSample:
    id: str
    kind: str
    text: str


class ResumeCorpus:
    def __init__(self, seed_dir: Path | None = None) -> None:
        self.seed_dir = seed_dir or _DEFAULT_SEED_DIR
        self._profile_cache: dict | None = None
        self._resume_cache: str | None = None
        self._samples_cache: list[VoiceSample] | None = None

    def _profile(self) -> dict:
        if self._profile_cache is None:
            self._profile_cache = json.loads((self.seed_dir / "profile.json").read_text())
        return self._profile_cache

    def resume_markdown(self) -> str:
        if self._resume_cache is None:
            self._resume_cache = (self.seed_dir / "resume.md").read_text()
        return self._resume_cache

    def profile_field(self, key: str) -> str | None:
        value = self._profile().get(key)
        if value is None or value == "":
            return None
        return value if isinstance(value, str) else str(value)

    def list_voice_samples(self) -> list[VoiceSample]:
        if self._samples_cache is None:
            data = json.loads((self.seed_dir / "voice_samples.json").read_text())
            self._samples_cache = [
                VoiceSample(id=s["id"], kind=s["kind"], text=s["text"])
                for s in data["samples"]
            ]
        return list(self._samples_cache)

    def find_voice_samples(
        self,
        query: str | None,
        kind: str | None,
        top_k: int,
    ) -> list[VoiceSample]:
        """Phase 3a: ignores `query` (no embedding similarity here — that's
        the voice_similarity module). Returns samples filtered by `kind`,
        capped at `top_k`. Phase 3b can add semantic retrieval."""
        samples = self.list_voice_samples()
        if kind:
            samples = [s for s in samples if s.kind == kind]
        return samples[:top_k]
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/mcp_servers/test_corpus.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/mcp_servers/ backend/tests/mcp_servers/
git commit -m "feat(mcp): ResumeCorpus loader for resume/profile/voice samples"
```

---

## Task 3: resume-mcp FastMCP server

**Files:**
- Create: `backend/src/apply/mcp_servers/resume_mcp/server.py`
- Create: `backend/tests/mcp_servers/test_resume_mcp_server.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/mcp_servers/test_resume_mcp_server.py`:

```python
from pathlib import Path

import pytest

from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus
from apply.mcp_servers.resume_mcp.server import build_server


@pytest.fixture
def corpus(tmp_path) -> ResumeCorpus:
    (tmp_path / "profile.json").write_text(
        '{"name":"X","email":"x@e.co","phone":"","linkedin_url":"","github_url":"",'
        '"portfolio_url":"","location":"Remote","work_auth":"","salary_expectation_usd":null,'
        '"remote_preference":"REMOTE_OK"}'
    )
    (tmp_path / "resume.md").write_text("# X\n\nPython.\n")
    (tmp_path / "voice_samples.json").write_text(
        '{"version":1,"samples":['
        '{"id":"s1","kind":"cover_letter","text":"hello"}]}'
    )
    return ResumeCorpus(seed_dir=tmp_path)


def test_build_server_returns_server_with_four_tools(corpus):
    server = build_server(corpus=corpus)
    assert server is not None

    # FastMCP exposes registered tools via its internals; at minimum we can
    # assert the factory produced an object and that the tool names we expect
    # appear in its registry.
    tool_names = set()
    # FastMCP 2.x: tools registered via @server.tool; the registry is internal.
    # Use the public-ish list_tools() helper if available, else inspect __dict__.
    if hasattr(server, "list_tools"):
        for t in server.list_tools():
            tool_names.add(getattr(t, "name", None) or getattr(t, "__name__", ""))
    else:
        # Fallback: scan the internal tool manager
        for name, _ in getattr(server, "_tools", {}).items():
            tool_names.add(name)

    assert {"get_resume_markdown", "get_profile_field", "list_voice_samples",
            "find_voice_samples"} <= tool_names
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/mcp_servers/test_resume_mcp_server.py -v
```

Expected: FAIL with `ImportError` or `ModuleNotFoundError`.

- [ ] **Step 3: Implement the server**

Create `backend/src/apply/mcp_servers/resume_mcp/server.py`:

```python
"""resume-mcp — custom FastMCP server exposing the user's resume + voice corpus.

Tools:
- get_resume_markdown() -> str
- get_profile_field(key: str) -> str | None
- list_voice_samples() -> list[dict]
- find_voice_samples(kind: str | None, top_k: int) -> list[dict]

The corpus is injected at construction time so tests can point at fixtures.
For production use, `build_server()` is called with `ResumeCorpus()` (defaults
to repo `backend/seed/`).
"""
from __future__ import annotations

from fastmcp import FastMCP

from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus


def build_server(corpus: ResumeCorpus | None = None) -> FastMCP:
    """Construct a configured resume-mcp server.

    Injecting corpus (rather than importing a module-level instance) makes the
    server testable against tmp_path fixtures.
    """
    corpus = corpus or ResumeCorpus()
    server: FastMCP = FastMCP(name="resume-mcp")

    @server.tool()
    def get_resume_markdown() -> str:
        """Return the user's resume as Markdown."""
        return corpus.resume_markdown()

    @server.tool()
    def get_profile_field(key: str) -> str | None:
        """Return a single profile field (name, email, linkedin_url, etc.) or null."""
        return corpus.profile_field(key)

    @server.tool()
    def list_voice_samples() -> list[dict]:
        """Return all voice samples as dicts (id, kind, text)."""
        return [
            {"id": s.id, "kind": s.kind, "text": s.text}
            for s in corpus.list_voice_samples()
        ]

    @server.tool()
    def find_voice_samples(kind: str | None = None, top_k: int = 3) -> list[dict]:
        """Return voice samples optionally filtered by kind (cover_letter, essay, email)."""
        return [
            {"id": s.id, "kind": s.kind, "text": s.text}
            for s in corpus.find_voice_samples(query=None, kind=kind, top_k=top_k)
        ]

    return server


def main() -> None:
    """Entry point for running resume-mcp as a standalone MCP stdio server."""
    build_server().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/mcp_servers/test_resume_mcp_server.py -v
```

Expected: PASS. If the test's tool-name lookup fails because FastMCP 2.x doesn't expose `list_tools` or `_tools` as assumed, adapt the assertion to whatever attribute FastMCP does expose (e.g., iterate `server._tool_manager._tools.keys()`). The point of the test is to verify 4 named tools are registered — adjust the lookup path to match the installed version, keep the assertion intent.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/mcp_servers/resume_mcp/server.py backend/tests/mcp_servers/test_resume_mcp_server.py
git commit -m "feat(mcp): resume-mcp FastMCP server with 4 tools"
```

---

## Task 4: Voice-similarity computation

**Files:**
- Create: `backend/src/apply/agents/voice_similarity.py`
- Create: `backend/tests/agents/test_voice_similarity.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_voice_similarity.py`:

```python
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from apply.agents.voice_similarity import (
    compute_voice_similarity,
    embed_text,
)


@pytest.mark.asyncio
async def test_embed_text_uses_openai_small_model():
    fake_embedding = [0.1, 0.2, 0.3]

    mock_client = AsyncMock()
    mock_client.embeddings.create.return_value.data = [type("O", (), {"embedding": fake_embedding})()]

    with patch("apply.agents.voice_similarity._get_openai_client", return_value=mock_client):
        vec = await embed_text("hello world")

    assert vec == pytest.approx(fake_embedding)
    mock_client.embeddings.create.assert_awaited_once()
    _, kwargs = mock_client.embeddings.create.await_args
    assert kwargs["model"] == "text-embedding-3-small"
    assert kwargs["input"] == "hello world"


@pytest.mark.asyncio
async def test_compute_voice_similarity_returns_max_cosine():
    # Craft vectors where we know the cosine answer
    draft_vec = np.array([1.0, 0.0, 0.0])
    sample_vecs = [
        np.array([0.9, 0.1, 0.0]),  # close to draft: cosine ~ 0.994
        np.array([0.0, 1.0, 0.0]),  # orthogonal: cosine 0
    ]

    async def fake_embed(text: str) -> list[float]:
        mapping = {
            "draft": draft_vec.tolist(),
            "close": sample_vecs[0].tolist(),
            "far": sample_vecs[1].tolist(),
        }
        return mapping[text]

    with patch("apply.agents.voice_similarity.embed_text", side_effect=fake_embed):
        score = await compute_voice_similarity(draft="draft", samples=["close", "far"])

    assert 0.99 <= score <= 1.0


@pytest.mark.asyncio
async def test_compute_voice_similarity_empty_samples_returns_neutral():
    score = await compute_voice_similarity(draft="anything", samples=[])
    assert score == 0.5  # neutral when no corpus to compare against
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_voice_similarity.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/voice_similarity.py`:

```python
"""Voice-similarity scoring via OpenAI embeddings.

Uses `text-embedding-3-small` (cheap: $0.02/1M tokens, 1536 dims). Computes
the MAX cosine similarity between the draft and each sample in the corpus.
Max (not mean) because a cover letter that sounds like ANY of the user's
past writings is in-voice; an average gets diluted by stylistic diversity
across kinds (essay vs email vs cover letter).
"""
from __future__ import annotations

import numpy as np
from openai import AsyncOpenAI

from apply.config import get_settings

_EMBED_MODEL = "text-embedding-3-small"
_NEUTRAL_SCORE = 0.5  # returned when there's no corpus to compare against


_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    """Plain OpenAI client (not routed through OpenRouter — embeddings are
    cheap and direct-OpenAI is the canonical endpoint for these models)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_text(text: str) -> list[float]:
    client = _get_openai_client()
    resp = await client.embeddings.create(model=_EMBED_MODEL, input=text)
    return list(resp.data[0].embedding)


def _cosine(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    av = np.asarray(a, dtype=np.float64)
    bv = np.asarray(b, dtype=np.float64)
    na = float(np.linalg.norm(av))
    nb = float(np.linalg.norm(bv))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(av, bv) / (na * nb))


async def compute_voice_similarity(draft: str, samples: list[str]) -> float:
    """Max cosine similarity between `draft` and `samples`. Returns 0.5 if no samples."""
    if not samples:
        return _NEUTRAL_SCORE
    draft_vec = await embed_text(draft)
    best = 0.0
    for sample in samples:
        sample_vec = await embed_text(sample)
        sim = _cosine(draft_vec, sample_vec)
        if sim > best:
            best = sim
    # Clamp to [0, 1] because cosine can dip negative but voice-similarity shouldn't
    return max(0.0, min(1.0, best))
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_voice_similarity.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/voice_similarity.py backend/tests/agents/test_voice_similarity.py
git commit -m "feat(agents): voice-similarity via OpenAI text-embedding-3-small"
```

---

## Task 5: Real Cover Letter Writer

**Files:**
- Create: `backend/src/apply/agents/cover_letter_writer_real.py`
- Create: `backend/tests/agents/test_cover_letter_writer_real.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_cover_letter_writer_real.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from apply.agents.cover_letter_writer_real import cover_letter_writer_real
from apply.schemas.writing import CoverLetter


@pytest.mark.asyncio
async def test_cover_letter_writer_real_returns_valid_draft():
    # TestModel returns the custom_output_args as the agent's structured output
    fake_body = "Dear Acme team, I read your Series A announcement…"
    test_model = TestModel(
        custom_output_args={
            "body_markdown": fake_body,
            "references_company_specifics": ["Series A", "engineering blog"],
        }
    )

    from apply.agents import cover_letter_writer_real as mod

    async def fake_similarity(draft: str, samples: list[str]) -> float:
        assert draft == fake_body
        assert samples  # corpus must be passed through
        return 0.77

    with patch.object(mod, "compute_voice_similarity", side_effect=fake_similarity):
        with mod._agent.override(model=test_model):
            result = await cover_letter_writer_real(
                application_id="app-test",
                company_name="Acme AI",
                company_brief="Series A agent startup",
                jd_markdown="Founding Engineer. 5+ yrs Python, LLM experience.",
                corpus_resume_markdown="I ship agents.",
                corpus_voice_samples=["Sample one.", "Sample two."],
            )

    assert isinstance(result, CoverLetter)
    assert result.application_id == "app-test"
    assert result.draft_version == 1
    assert result.body_markdown == fake_body
    assert result.voice_similarity_score == 0.77
    assert "Series A" in result.references_company_specifics
    assert result.word_count > 0
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_cover_letter_writer_real.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/cover_letter_writer_real.py`:

```python
"""Real Cover Letter Writer.

Sonnet 4.6 single-shot with two structured-output fields (body_markdown and
references_company_specifics). Voice-similarity score is computed
out-of-band via OpenAI embeddings after the agent returns the draft.

Inputs (passed by the orchestrator):
- application_id: used in the returned CoverLetter's application_id
- company_name, company_brief: hook material
- jd_markdown: what the user is applying for
- corpus_resume_markdown: what the user has done (from resume-mcp)
- corpus_voice_samples: the user's past writing (from resume-mcp)
"""
from __future__ import annotations

import uuid
from datetime import datetime, UTC

from pydantic import BaseModel
from pydantic_ai import Agent

from apply.agents.models import sonnet
from apply.agents.voice_similarity import compute_voice_similarity
from apply.schemas.writing import CoverLetter


SYSTEM_PROMPT = """
You are drafting a cover letter that sounds like the candidate — not like
a generic "passionate engineer looking for opportunities" template.

You will receive:
- the candidate's resume (for context on what they've built)
- 2-5 writing samples in the candidate's voice (cover letters, essays, emails)
- the target company's name + a one-line brief about them
- the job description

Your job:
1. Write a cover letter of ~250-350 words that:
   - Opens with a specific observation about the company (never "I'm excited
     to apply for…")
   - Weaves in 2-3 concrete company-specific facts from the brief
   - Reflects the candidate's actual experience quoted or paraphrased from
     the resume (do NOT invent projects)
   - Matches the cadence and vocabulary of the voice samples
2. Return a list of the company-specific facts you actually cited, so the
   user can verify you didn't hallucinate.

Do NOT include sign-off boilerplate ("Sincerely, Name" — the app will add
this later). End on the strongest sentence you can write.
"""


class _AgentOutput(BaseModel):
    body_markdown: str
    references_company_specifics: list[str]


_agent = Agent(
    model=sonnet(),
    output_type=_AgentOutput,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def cover_letter_writer_real(
    application_id: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
) -> CoverLetter:
    user_prompt = (
        f"COMPANY: {company_name}\n"
        f"BRIEF: {company_brief}\n\n"
        f"JD:\n---\n{jd_markdown}\n---\n\n"
        f"CANDIDATE RESUME:\n---\n{corpus_resume_markdown}\n---\n\n"
        f"VOICE SAMPLES (match this cadence):\n---\n"
        + "\n\n—\n\n".join(corpus_voice_samples)
        + "\n---"
    )
    result = await _agent.run(user_prompt)
    out = result.output

    voice_score = await compute_voice_similarity(
        draft=out.body_markdown,
        samples=corpus_voice_samples,
    )

    return CoverLetter(
        id=f"cl-{uuid.uuid4().hex[:8]}",
        application_id=application_id,
        draft_version=1,
        body_markdown=out.body_markdown,
        word_count=len(out.body_markdown.split()),
        references_company_specifics=out.references_company_specifics,
        voice_similarity_score=voice_score,
        created_at=datetime.now(UTC),
    )
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_cover_letter_writer_real.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/cover_letter_writer_real.py backend/tests/agents/test_cover_letter_writer_real.py
git commit -m "feat(agents): real Cover Letter Writer with voice-similarity scoring"
```

---

## Task 6: Real Screening Answerer

**Files:**
- Create: `backend/src/apply/agents/screening_answerer_real.py`
- Create: `backend/tests/agents/test_screening_answerer_real.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_screening_answerer_real.py`:

```python
import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.screening_answerer_real import screening_answerer_real
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import ScreeningAnswer


@pytest.mark.asyncio
async def test_screening_answerer_real_returns_valid_answer():
    test_model = TestModel(
        custom_output_args={
            "answer_markdown": "I'm drawn to Acme because their recent blog on agent product thinking…"
        }
    )

    from apply.agents import screening_answerer_real as mod

    with mod._agent.override(model=test_model):
        result = await screening_answerer_real(
            question="Why do you want to work at Acme AI?",
            company_name="Acme AI",
            company_brief="Series A agent startup",
            jd_markdown="Founding Engineer…",
            corpus_resume_markdown="I ship agents.",
            corpus_voice_samples=["Sample one."],
            origin=ScreeningAnswerOrigin.PROACTIVE,
        )

    assert isinstance(result, ScreeningAnswer)
    assert result.question == "Why do you want to work at Acme AI?"
    assert "Acme" in result.answer
    assert result.word_count > 0
    assert result.drafted_by == ScreeningAnswerOrigin.PROACTIVE
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_screening_answerer_real.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/screening_answerer_real.py`:

```python
"""Real Screening Question Answerer.

Sonnet 4.6 single-shot per question. Uses the same context as the Cover
Letter Writer (resume + voice samples + company brief) but answers ONE
specific screening question. Invoked either proactively (if the JD lists
screening questions up-front) or dynamically by Form-Fill when it
encounters a free-text question mid-fill.
"""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent

from apply.agents.models import sonnet
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import ScreeningAnswer


SYSTEM_PROMPT = """
You are answering a single screening question on a job application, in
the candidate's voice. You will receive the candidate's resume, writing
samples, the company brief, the JD, and one question.

Guidelines:
- 100-200 words unless the form clearly wants something shorter
- Open with a specific observation, not a generic affirmation
- Cite 1-2 concrete things from the candidate's resume — don't invent
- Match the cadence of the voice samples
- End strong. No "I look forward to hearing from you" boilerplate.

Return just the answer text (no question repetition, no heading).
"""


class _AgentOutput(BaseModel):
    answer_markdown: str


_agent = Agent(
    model=sonnet(),
    output_type=_AgentOutput,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def screening_answerer_real(
    question: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
    origin: ScreeningAnswerOrigin,
) -> ScreeningAnswer:
    user_prompt = (
        f"QUESTION: {question}\n\n"
        f"COMPANY: {company_name}\n"
        f"BRIEF: {company_brief}\n\n"
        f"JD:\n---\n{jd_markdown}\n---\n\n"
        f"CANDIDATE RESUME:\n---\n{corpus_resume_markdown}\n---\n\n"
        f"VOICE SAMPLES (match this cadence):\n---\n"
        + "\n\n—\n\n".join(corpus_voice_samples)
        + "\n---"
    )
    result = await _agent.run(user_prompt)
    answer_text = result.output.answer_markdown
    return ScreeningAnswer(
        question=question,
        answer=answer_text,
        word_count=len(answer_text.split()),
        drafted_by=origin,
    )
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_screening_answerer_real.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/screening_answerer_real.py backend/tests/agents/test_screening_answerer_real.py
git commit -m "feat(agents): real Screening Question Answerer"
```

---

## Task 7: Wire writing agents into runtime switch

**Files:**
- Modify: `backend/src/apply/agents/runtime.py`
- Modify: `backend/tests/agents/test_runtime.py`

- [ ] **Step 1: Append failing tests**

Append to `backend/tests/agents/test_runtime.py`:

```python
from apply.schemas.enums import ScreeningAnswerOrigin


@pytest.mark.asyncio
async def test_runtime_cover_letter_writer_stub_path(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.cover_letter_writer(
        application_id="app-x",
        company_name="Acme AI",
        company_brief="brief",
        jd_markdown="jd",
        corpus_resume_markdown="resume",
        corpus_voice_samples=["sample"],
    )
    # Stub path: should call cover_letter_writer_stub and return a CoverLetter
    assert result.application_id == "app-x"


@pytest.mark.asyncio
async def test_runtime_screening_answerer_stub_path(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.screening_answerer(
        question="Why us?",
        company_name="Acme AI",
        company_brief="brief",
        jd_markdown="jd",
        corpus_resume_markdown="resume",
        corpus_voice_samples=["sample"],
        origin=ScreeningAnswerOrigin.PROACTIVE,
    )
    assert result.question == "Why us?"


@pytest.mark.asyncio
async def test_runtime_cover_letter_writer_real_path(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime as rt

    async def fake_real(**kwargs):
        from datetime import datetime, UTC
        from apply.schemas.writing import CoverLetter
        return CoverLetter(
            id="cl-real", application_id=kwargs["application_id"],
            draft_version=1, body_markdown="real draft",
            word_count=2, references_company_specifics=[],
            voice_similarity_score=0.8, created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(rt, "_cover_letter_real", fake_real)

    result = await runtime.cover_letter_writer(
        application_id="app-real",
        company_name="Acme",
        company_brief="brief",
        jd_markdown="jd",
        corpus_resume_markdown="resume",
        corpus_voice_samples=["s1"],
    )
    assert result.application_id == "app-real"
    assert result.body_markdown == "real draft"
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_runtime.py -v -k "cover_letter_writer or screening_answerer"
```

Expected: FAIL — runtime doesn't have these functions yet.

- [ ] **Step 3: Extend runtime.py**

Modify `backend/src/apply/agents/runtime.py` — add the two new entrypoints. Full updated file:

```python
"""Runtime switch: routes agent calls to real or stub implementations
based on the `APPLY_USE_REAL_AGENTS` flag.
"""
from apply.agents.company_researcher import company_researcher_stub as _cr_stub
from apply.agents.company_researcher_real import (
    company_researcher_real as _company_researcher_real,
)
from apply.agents.cover_letter_writer import cover_letter_writer_stub as _cl_stub
from apply.agents.cover_letter_writer_real import (
    cover_letter_writer_real as _cover_letter_real,
)
from apply.agents.fit_analyst import fit_analyst_stub as _fa_stub
from apply.agents.fit_analyst_real import fit_analyst_real as _fit_analyst_real
from apply.agents.intake import intake_stub as _intake_stub
from apply.agents.intake_real import intake_real as _intake_real
from apply.agents.screening_answerer import screening_answerer_stub as _sa_stub
from apply.agents.screening_answerer_real import (
    screening_answerer_real as _screening_answerer_real,
)
from apply.config import get_settings
from apply.schemas.company import CompanyResearch
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing
from apply.schemas.writing import CoverLetter, ScreeningAnswer


def _use_real() -> bool:
    return get_settings().apply_use_real_agents


async def intake(url: str, jd_text: str, raw_html_path: str) -> JobListing:
    if _use_real():
        return await _intake_real(url=url, jd_text=jd_text, raw_html_path=raw_html_path)
    return await _intake_stub(url=url)


async def company_researcher(company_name: str) -> CompanyResearch:
    if _use_real():
        return await _company_researcher_real(company_name=company_name)
    return await _cr_stub(company_name=company_name)


async def fit_analyst(
    resume_markdown: str,
    jd_markdown: str,
    company_brief: str,
) -> FitAnalysis:
    if _use_real():
        return await _fit_analyst_real(
            resume_markdown=resume_markdown,
            jd_markdown=jd_markdown,
            company_brief=company_brief,
        )
    return await _fa_stub(job_listing_id="job-stub", resume_markdown=resume_markdown)


async def cover_letter_writer(
    application_id: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
) -> CoverLetter:
    if _use_real():
        return await _cover_letter_real(
            application_id=application_id,
            company_name=company_name,
            company_brief=company_brief,
            jd_markdown=jd_markdown,
            corpus_resume_markdown=corpus_resume_markdown,
            corpus_voice_samples=corpus_voice_samples,
        )
    return await _cl_stub(application_id=application_id, company_name=company_name)


async def screening_answerer(
    question: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
    origin: ScreeningAnswerOrigin,
) -> ScreeningAnswer:
    if _use_real():
        return await _screening_answerer_real(
            question=question,
            company_name=company_name,
            company_brief=company_brief,
            jd_markdown=jd_markdown,
            corpus_resume_markdown=corpus_resume_markdown,
            corpus_voice_samples=corpus_voice_samples,
            origin=origin,
        )
    return await _sa_stub(question=question, origin=origin)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_runtime.py -v
```

Expected: all runtime tests (old + 3 new) pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/runtime.py backend/tests/agents/test_runtime.py
git commit -m "feat(agents): runtime entrypoints for Cover Letter Writer + Screening Answerer"
```

---

## Task 8: Orchestrator wires writing agents through runtime

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`

The orchestrator's `DRAFTING` branch currently calls `cover_letter_writer_stub` directly. Replace with the runtime call, and load the user's corpus once per run.

- [ ] **Step 1: Update `graph.py`**

Modify `backend/src/apply/orchestrator/graph.py`. Full updated file:

```python
from dataclasses import dataclass, field
from typing import Any

from apply.agents import runtime
from apply.agents.memory_curator import memory_curator_stub
from apply.agents.form_fill import form_fill_stub
from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus
from apply.observability.langfuse_setup import get_langfuse
from apply.orchestrator.state_machine import advance_state
from apply.schemas.enums import PipelineRunState


@dataclass
class PipelineContext:
    run_id: str
    application_id: str
    jd_url: str
    state: PipelineRunState
    artifacts: dict[str, Any] = field(default_factory=dict)
    cost_accumulated_usd: float = 0.0
    jd_text: str = ""
    resume_markdown: str = ""


def _load_corpus_once(ctx: PipelineContext) -> None:
    """Populate ctx.resume_markdown and ctx.artifacts['voice_samples'] from resume-mcp's backing corpus.

    Done eagerly at the top of RESEARCHING so downstream states have both.
    """
    if ctx.resume_markdown:
        return  # already loaded
    corpus = ResumeCorpus()
    ctx.resume_markdown = corpus.resume_markdown()
    samples = corpus.list_voice_samples()
    ctx.artifacts["voice_samples"] = [s.text for s in samples]


async def run_to_next_checkpoint(ctx: PipelineContext) -> None:
    lf = get_langfuse()
    trace = lf.trace(name="pipeline_run", id=ctx.run_id)

    while True:
        if ctx.state == PipelineRunState.INTAKE_RUNNING:
            with trace.span(name="intake"):
                listing = await runtime.intake(
                    url=ctx.jd_url,
                    jd_text=ctx.jd_text,
                    raw_html_path=f"/tmp/apply/{ctx.run_id}.html",
                )
            ctx.artifacts["job_listing"] = listing.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.001
            ctx.state = advance_state(ctx.state, PipelineRunState.RESEARCHING)
            continue

        if ctx.state == PipelineRunState.RESEARCHING:
            _load_corpus_once(ctx)
            listing = ctx.artifacts["job_listing"]
            with trace.span(name="company_researcher"):
                research = await runtime.company_researcher(
                    company_name=listing["company_name"],
                )
            with trace.span(name="fit_analyst"):
                fit = await runtime.fit_analyst(
                    resume_markdown=ctx.resume_markdown,
                    jd_markdown=listing["description_markdown"],
                    company_brief=f"{research.company_name}: {research.signal_score:.2f} signal",
                )
            ctx.artifacts["company_research"] = research.model_dump(mode="json")
            ctx.artifacts["fit_analysis"] = fit.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.05
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_FIT_APPROVAL)
            return

        if ctx.state == PipelineRunState.DRAFTING:
            _load_corpus_once(ctx)
            listing = ctx.artifacts["job_listing"]
            research = ctx.artifacts.get("company_research", {})
            samples: list[str] = ctx.artifacts.get("voice_samples", [])
            brief = (
                f"{research.get('company_name', listing['company_name'])} — "
                f"stage: {research.get('funding_stage') or 'unknown'}, "
                f"signal: {research.get('signal_score', 0):.2f}"
            )
            with trace.span(name="cover_letter_writer"):
                letter = await runtime.cover_letter_writer(
                    application_id=ctx.application_id,
                    company_name=listing["company_name"],
                    company_brief=brief,
                    jd_markdown=listing["description_markdown"],
                    corpus_resume_markdown=ctx.resume_markdown,
                    corpus_voice_samples=samples,
                )
            ctx.artifacts["cover_letter"] = letter.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.05
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_CONTENT_APPROVAL)
            return

        if ctx.state == PipelineRunState.FILLING_FORM:
            listing = ctx.artifacts.get("job_listing", {})
            application_url = listing.get("application_url", ctx.jd_url)
            letter = ctx.artifacts.get("cover_letter", {})
            with trace.span(name="form_fill"):
                result = await form_fill_stub(
                    application_url=application_url,
                    cover_letter_body=letter.get("body_markdown", ""),
                )
            ctx.artifacts["form_fill_result"] = result.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.08
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_SUBMIT_APPROVAL)
            return

        if ctx.state == PipelineRunState.SUBMITTING:
            ctx.artifacts["submission_confirmation"] = {"url": "https://stub.example/confirm"}
            with trace.span(name="memory_curator"):
                await memory_curator_stub(application_id=ctx.application_id)
            ctx.state = advance_state(ctx.state, PipelineRunState.COMPLETED)
            return

        return
```

- [ ] **Step 2: Run full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all prior + new tests pass. Count: 72 + ~12 new (2 corpus + 7 server + 3 voice_sim + 1 cover + 1 screening + 3 runtime = ~17 new) = ~89.

If E2E test fails because `ResumeCorpus` tries to read from real `backend/seed/` during the test and finds something the test doesn't expect, adjust the E2E: it should still work with stub agents because stubs ignore the corpus args. Verify `APPLY_USE_REAL_AGENTS=false` is set.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py
git commit -m "feat(orchestrator): route Cover Letter Writer through runtime + load voice corpus"
```

---

## Task 9: Live integration test (opt-in, real LLM)

**Files:**
- Modify: `backend/tests/test_integration_real_agents.py`

- [ ] **Step 1: Append a live test for the writing agents**

Append to `backend/tests/test_integration_real_agents.py`:

```python
@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_cover_letter_writer(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime

    result = await runtime.cover_letter_writer(
        application_id="app-live-test",
        company_name="Anthropic",
        company_brief="AI safety research lab, Claude models",
        jd_markdown=(
            "Applied AI Engineer. 5+ years Python. "
            "Experience with LLMs and agent frameworks. "
            "Comfort with async systems."
        ),
        corpus_resume_markdown=(
            "Senior Python engineer. Shipped multi-agent systems "
            "with Pydantic AI + MCP. Async systems expertise."
        ),
        corpus_voice_samples=[
            "I read your recent blog on agent product thinking with interest.",
            "The thing I'd most like to talk about is how your team thinks about evaluation.",
        ],
    )

    assert result.body_markdown
    assert result.word_count >= 100
    assert 0.0 <= result.voice_similarity_score <= 1.0


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_screening_answerer(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime
    from apply.schemas.enums import ScreeningAnswerOrigin

    result = await runtime.screening_answerer(
        question="What excites you about applied AI work?",
        company_name="Anthropic",
        company_brief="AI safety research lab",
        jd_markdown="Applied AI Engineer",
        corpus_resume_markdown="Ships agents, cares about eval harnesses.",
        corpus_voice_samples=["The discipline that makes good backend code makes good agent code."],
        origin=ScreeningAnswerOrigin.PROACTIVE,
    )

    assert result.answer
    assert result.word_count >= 30
```

- [ ] **Step 2: Verify with keys if available**

```bash
cd backend && uv run pytest tests/test_integration_real_agents.py -v
```

Expected without keys: 5 skipped.
Expected with keys: 5 passed (3 prior + 2 new). Total cost ~$0.10-0.30.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration_real_agents.py
git commit -m "test(integration): live Cover Letter Writer + Screening Answerer tests"
```

---

## Task 10: Docs + tag

**Files:**
- Modify: `LEARNINGS.md`
- Modify: `README.md`

- [ ] **Step 1: Append LEARNINGS entry**

Append to `LEARNINGS.md`:

```markdown

## 2026-04-23 — Voice similarity is the real differentiator
Tags: agent-design, eval, product-decisions

The Cover Letter Writer's USP isn't the cover letter — it's the
voice-similarity score the user sees in HITL #2. Every auto-apply tool
produces SOME text; only this one tells you how close to your actual
writing style the draft landed.

Implementation: OpenAI `text-embedding-3-small` ($0.02/1M tokens),
max cosine similarity between the draft and each sample in the
user's corpus. Max (not mean) because a draft that resembles ANY of
the user's writings is in-voice; mean gets diluted across kinds (essay
vs cover letter vs email).

Voice-similarity is computed OUT-OF-BAND after the agent returns the
draft — not as a tool call during generation. Reason: asking the LLM
to self-assess its own voice match creates a feedback loop where the
model reports whatever it thinks you want to hear. Embedding similarity
is model-independent and gives you a number you can trust.

**Takeaway:** when a metric will end up in a recruiter-facing
interview story, compute it from a different system than the one
being measured. Self-scoring is cheap theater; cross-system
scoring is information.

---
```

- [ ] **Step 2: Update README**

In `README.md`, find the "Status" callout and update:

```markdown
> **Status:** Phase 3a complete. Real Cover Letter Writer + Screening
> Answerer ship, backed by a custom `resume-mcp` FastMCP server and
> OpenAI embedding-based voice similarity. HITL #2 now renders a real
> draft that sounds like the user. Phase 3b (memory-mcp + LLM-as-judge
> + baseline comparison table) is next.
```

- [ ] **Step 3: Final verify**

```bash
cd backend && uv run pytest --tb=no -q
```

Expected: all tests pass. Count should be ~89 (72 from Phase 2b + 17 new) with 5 skipped live tests when no keys.

```bash
cd backend && uv run ruff check src/ tests/ eval/
```

If issues, fix and commit as `chore: ruff cleanup for Phase 3a`.

- [ ] **Step 4: Tag**

```bash
git tag v0.3.0-writing-agents
```

- [ ] **Step 5: Commit docs**

```bash
git add LEARNINGS.md README.md
git commit -m "docs: Phase 3a LEARNINGS entry + README update"
```

---

## Self-review checklist

- [ ] `resume-mcp` server registers 4 tools and passes its unit test
- [ ] Voice similarity: max cosine, returns 0.5 for empty corpus
- [ ] Cover Letter Writer uses TestModel for unit test; returns valid CoverLetter with voice_similarity_score
- [ ] Screening Answerer uses TestModel; returns valid ScreeningAnswer with correct `drafted_by` origin
- [ ] Runtime switch adds `cover_letter_writer` + `screening_answerer` without breaking existing entrypoints
- [ ] Orchestrator loads corpus once per run via `_load_corpus_once`
- [ ] Walking skeleton E2E still passes with stubs (`APPLY_USE_REAL_AGENTS=false`)
- [ ] Live integration tests skip cleanly without keys
- [ ] No `Co-Authored-By:` trailer on any commit

---

## Out of scope for this plan (Phase 3b)

- `memory-mcp` custom server (`already_applied`, `similar_applications`, `what_landed_replies`, `log_outcome`)
- Real `Memory Curator` (async post-submission indexing)
- LLM-as-judge evaluator on cover letter quality (GPT-4.1, 4-dim rubric)
- Baseline comparison table: Apply vs Claude one-shot vs Perplexity vs LazyApply
- Cover Letter Writer with dynamic retrieval from `memory-mcp` ("what landed replies")
- Resume upload UI + voice-sample ingestion flow (user-facing onboarding)
