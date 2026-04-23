# Apply — Phase 2a Implementation Plan (Real Research Agents)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the three research-phase stubs (Intake, Company Researcher, Fit Analyst) with real LLM-backed agents using Pydantic AI, wiring Tavily and Firecrawl as MCP servers, so the user-facing pipeline produces genuine research output at HITL #1.

**Architecture:** Each agent is a `pydantic_ai.Agent` with a typed `result_type` (JobListing / CompanyResearch / FitAnalysis). Intake uses Haiku + a single Firecrawl scrape to get JD text, then a structured-output call. Company Researcher uses Sonnet 4.6 with Tavily + Firecrawl MCP servers in a ReAct loop. Fit Analyst uses Sonnet 4.6 in a single-shot call over resume + JD + company research. An `APPLY_USE_REAL_AGENTS` env flag switches between real and stub implementations so the walking skeleton still demos without API keys. LLM calls in tests are recorded with VCR.

**Tech Stack:** Pydantic AI 0.0.14+, Anthropic Python SDK, pydantic-ai-slim MCP support, Tavily MCP server (`tavily-mcp` via npx), Firecrawl MCP server (`firecrawl-mcp` via npx), pytest + pytest-vcr for deterministic test runs.

**What this plan does NOT cover:** Eval harness, goldenset, baseline comparisons, LLM-as-judge (those are Phase 2b). Cover Letter Writer, Screening, Form-Fill, Memory Curator replacements (Phase 3+).

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md`

---

## File map

**New files:**
- `backend/src/apply/agents/models.py` — shared Claude model factories
- `backend/src/apply/agents/mcp_servers.py` — Tavily + Firecrawl MCP server factories
- `backend/src/apply/agents/intake_real.py`
- `backend/src/apply/agents/company_researcher_real.py`
- `backend/src/apply/agents/fit_analyst_real.py`
- `backend/src/apply/agents/runtime.py` — stub/real switch based on env flag
- `backend/tests/agents/__init__.py`
- `backend/tests/agents/cassettes/.gitkeep`
- `backend/tests/agents/test_intake_real.py`
- `backend/tests/agents/test_company_researcher_real.py`
- `backend/tests/agents/test_fit_analyst_real.py`
- `backend/tests/agents/test_runtime.py`

**Modified files:**
- `backend/pyproject.toml` — add anthropic upgrade, pydantic-ai upgrade, pytest-vcr, pytest-recording
- `.env.example` — mark required keys for Phase 2a
- `backend/src/apply/config.py` — add `apply_use_real_agents` flag
- `backend/src/apply/orchestrator/graph.py` — route agent calls through `runtime` helpers
- `LEARNINGS.md` — append entries as issues surface

---

## Prerequisites (verify before starting)

Before dispatching Task 1:

```bash
which npx          # Node must be installed for MCP servers
node --version     # >= 18
```

If `npx` isn't available: `brew install node` then retry.

Copy API keys to `.env` at repo root:

```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
```

Without the keys, most tasks still ship code (they use VCR cassettes), but Task 13's live integration test will skip.

---

## Task 1: Upgrade LLM dependencies + add VCR

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Update backend/pyproject.toml dependencies**

Replace the `dependencies` section and `[dependency-groups].dev` with:

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "pydantic-ai-slim[anthropic,mcp]>=0.0.52",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "sse-starlette>=2.1.3",
    "langfuse>=2.57.0",
    "httpx>=0.28.0",
    "anthropic>=0.39.0",
    "openai>=1.54.0",
    "python-multipart>=0.0.20",
]

[dependency-groups]
dev = [
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "pytest-recording>=0.13.2",
    "vcrpy>=6.0.2",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]
```

- [ ] **Step 2: Sync**

```bash
cd backend && uv sync
```

Expected: resolves and installs `pydantic-ai-slim`, `pytest-recording`, `vcrpy`.

- [ ] **Step 3: Verify imports**

```bash
cd backend && uv run python -c "from pydantic_ai import Agent; from pydantic_ai.mcp import MCPServerStdio; from pydantic_ai.models.anthropic import AnthropicModel; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Verify existing tests still pass**

```bash
cd backend && uv run pytest --tb=no -q
```

Expected: 46 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore(deps): upgrade pydantic-ai with anthropic+mcp extras; add VCR"
```

---

## Task 2: Extend config with `apply_use_real_agents` flag

**Files:**
- Modify: `backend/src/apply/config.py`
- Modify: `.env.example`
- Modify: `backend/tests/test_config.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_config.py`:

```python
def test_settings_use_real_agents_default_false(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.delenv("APPLY_USE_REAL_AGENTS", raising=False)

    settings = Settings()

    assert settings.apply_use_real_agents is False


def test_settings_use_real_agents_true(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")

    settings = Settings()

    assert settings.apply_use_real_agents is True
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_config.py -v -k use_real_agents
```

Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'apply_use_real_agents'` (or similar).

- [ ] **Step 3: Implement**

Add to `backend/src/apply/config.py`, after the `apply_daily_cap_usd` field:

```python
    apply_use_real_agents: bool = Field(default=False, alias="APPLY_USE_REAL_AGENTS")
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/test_config.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Update .env.example**

Append to `.env.example`:

```
# Phase 2a: set to true to use real LLM agents instead of stubs
APPLY_USE_REAL_AGENTS=false
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/config.py backend/tests/test_config.py .env.example
git commit -m "feat(config): add APPLY_USE_REAL_AGENTS switch"
```

---

## Task 3: Model factory for Claude Haiku + Sonnet

**Files:**
- Create: `backend/src/apply/agents/models.py`

- [ ] **Step 1: Implement model factory**

Create `backend/src/apply/agents/models.py`:

```python
"""Shared Claude model factories for Pydantic AI agents.

Centralizes model IDs so upgrading (Sonnet 4.6 → 4.7, Haiku 4.5 → 5.0) is one-file.
"""
from pydantic_ai.models.anthropic import AnthropicModel

# Model IDs — update in one place when Anthropic ships new models.
HAIKU_MODEL_ID = "claude-haiku-4-5-20251001"
SONNET_MODEL_ID = "claude-sonnet-4-6"


def haiku() -> AnthropicModel:
    """Cheap, fast model for structured parsing + classification."""
    return AnthropicModel(HAIKU_MODEL_ID)


def sonnet() -> AnthropicModel:
    """Reasoning model for research + fit analysis."""
    return AnthropicModel(SONNET_MODEL_ID)
```

- [ ] **Step 2: Verify import**

```bash
cd backend && uv run python -c "from apply.agents.models import haiku, sonnet; h = haiku(); s = sonnet(); print(type(h).__name__, type(s).__name__)"
```

Expected: `AnthropicModel AnthropicModel`

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/agents/models.py
git commit -m "feat(agents): Claude Haiku + Sonnet model factories"
```

---

## Task 4: MCP server factories for Tavily + Firecrawl

**Files:**
- Create: `backend/src/apply/agents/mcp_servers.py`

- [ ] **Step 1: Implement MCP factories**

Create `backend/src/apply/agents/mcp_servers.py`:

```python
"""Factories for Tavily and Firecrawl MCP server subprocesses.

Both servers run as Node subprocesses invoked via `npx`. API keys are
passed through environment variables. Callers hold the `MCPServerStdio`
instances for the lifetime of an agent run; Pydantic AI's Agent context
manages start/stop.
"""
from pydantic_ai.mcp import MCPServerStdio

from apply.config import get_settings


def tavily_mcp() -> MCPServerStdio:
    """Tavily web-search MCP server — search, news_search, etc."""
    settings = get_settings()
    return MCPServerStdio(
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={"TAVILY_API_KEY": settings.tavily_api_key},
    )


def firecrawl_mcp() -> MCPServerStdio:
    """Firecrawl scraping MCP server — scrape, map, crawl."""
    settings = get_settings()
    return MCPServerStdio(
        command="npx",
        args=["-y", "firecrawl-mcp"],
        env={"FIRECRAWL_API_KEY": settings.firecrawl_api_key},
    )
```

- [ ] **Step 2: Verify import**

```bash
cd backend && uv run python -c "from apply.agents.mcp_servers import tavily_mcp, firecrawl_mcp; print(type(tavily_mcp()).__name__)"
```

Expected: `MCPServerStdio`

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/agents/mcp_servers.py
git commit -m "feat(agents): Tavily + Firecrawl MCP server factories"
```

---

## Task 5: Test fixtures for agent tests (VCR setup)

**Files:**
- Create: `backend/tests/agents/__init__.py`
- Create: `backend/tests/agents/conftest.py`
- Create: `backend/tests/agents/cassettes/.gitkeep`

- [ ] **Step 1: Create agents test package**

```bash
mkdir -p backend/tests/agents/cassettes
touch backend/tests/agents/__init__.py
touch backend/tests/agents/cassettes/.gitkeep
```

- [ ] **Step 2: Write conftest with VCR config**

Create `backend/tests/agents/conftest.py`:

```python
"""VCR configuration for agent tests.

Records real LLM + MCP responses on first run; replays them afterward.
Filters sensitive headers so cassettes are safe to commit.
"""
from pathlib import Path

import pytest


@pytest.fixture
def vcr_config():
    return {
        "filter_headers": [
            "authorization",
            "x-api-key",
            "anthropic-api-key",
            "cookie",
        ],
        "filter_query_parameters": [
            "api_key",
            "token",
        ],
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "record_mode": "once",
    }


@pytest.fixture
def vcr_cassette_dir(request):
    return str(Path(__file__).parent / "cassettes")
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/agents/__init__.py backend/tests/agents/conftest.py backend/tests/agents/cassettes/.gitkeep
git commit -m "test(agents): VCR conftest for agent test cassettes"
```

---

## Task 6: Real Intake agent

**Files:**
- Create: `backend/src/apply/agents/intake_real.py`
- Create: `backend/tests/agents/test_intake_real.py`

- [ ] **Step 1: Write failing test (unit, mocks the LLM)**

Create `backend/tests/agents/test_intake_real.py`:

```python
import pytest
from pydantic_ai import models

from apply.agents.intake_real import intake_real
from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing


@pytest.fixture
def sample_jd_text():
    return """
    Founding Engineer — Acme AI (YC W24)
    Location: San Francisco, CA (Hybrid)
    Salary: $180k-$240k + equity

    We're building long-running agents for enterprise workflows.

    Requirements:
    - 5+ years Python
    - Experience with LLMs and agent frameworks
    - Strong async systems background

    Nice to haves:
    - LangGraph / Claude Agent SDK experience
    - Published open-source agent work
    """


@pytest.mark.asyncio
async def test_intake_real_returns_valid_job_listing_unit(sample_jd_text):
    """Unit test using Pydantic AI's TestModel — no network."""
    from pydantic_ai.models.test import TestModel

    test_model = TestModel(
        custom_output_args={
            "id": "job-test",
            "source": "YC_WAAS",
            "url": "https://workatastartup.com/jobs/123",
            "application_url": "https://workatastartup.com/jobs/123/apply",
            "company_name": "Acme AI",
            "role_title": "Founding Engineer",
            "location": "San Francisco, CA",
            "remote_type": "HYBRID",
            "description_markdown": sample_jd_text.strip(),
            "requirements": ["5+ years Python", "LLM experience"],
            "nice_to_haves": ["LangGraph experience"],
            "compensation_range": "$180k-$240k + equity",
            "raw_html_path": "/tmp/apply/stub-jd.html",
        }
    )

    with models.override(test_model):
        result = await intake_real(
            url="https://workatastartup.com/jobs/123",
            jd_text=sample_jd_text,
            raw_html_path="/tmp/apply/stub-jd.html",
        )

    assert isinstance(result, JobListing)
    assert result.company_name == "Acme AI"
    assert result.source == JobSource.YC_WAAS
    assert result.remote_type == RemoteType.HYBRID
    assert len(result.requirements) >= 1
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_intake_real.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apply.agents.intake_real'`.

- [ ] **Step 3: Implement the real Intake agent**

Create `backend/src/apply/agents/intake_real.py`:

```python
"""Real Intake agent — parses a JD URL + text into a typed JobListing.

Uses Claude Haiku for cheap, deterministic structured extraction.
The caller is responsible for having already fetched the JD text
(Firecrawl, Tavily, or user paste); this agent does not scrape.
"""
import uuid

from pydantic_ai import Agent

from apply.agents.models import haiku
from apply.schemas.job import JobListing

SYSTEM_PROMPT = """
You are a job listing parser. Given a JD URL and its plaintext/markdown
content, extract a typed JobListing.

Guidance:
- `source`: infer from the URL hostname:
  * workatastartup.com → YC_WAAS
  * wellfound.com or angel.co → WELLFOUND
  * jobs.lever.co → LEVER
  * boards.greenhouse.io → GREENHOUSE
  * jobs.ashbyhq.com → ASHBY
  * myworkdayjobs.com → WORKDAY
  * otherwise → COMPANY_PAGE or OTHER
- `application_url`: if the JD contains an "Apply" button with a distinct
  URL, use it. Otherwise reuse the listing URL.
- `remote_type`: classify into REMOTE | HYBRID | ONSITE based on the
  location/work-style copy.
- `requirements`: hard requirements only. Short items (< 80 chars each).
- `nice_to_haves`: bonus/optional items.
- `compensation_range`: quote the text verbatim if present, else null.
- `description_markdown`: copy the JD content near-verbatim as Markdown.

Be precise. Do not invent facts. If a field is absent, leave it null.
"""


_agent = Agent(
    model=haiku(),
    output_type=JobListing,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def intake_real(url: str, jd_text: str, raw_html_path: str) -> JobListing:
    """Parse a JD URL + text into a typed JobListing via Claude Haiku."""
    user_prompt = (
        f"Listing URL: {url}\n"
        f"Generate id: job-{uuid.uuid4().hex[:8]}\n"
        f"Save raw HTML at: {raw_html_path}\n\n"
        f"JD content:\n---\n{jd_text}\n---"
    )
    result = await _agent.run(user_prompt)
    return result.output
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_intake_real.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/intake_real.py backend/tests/agents/test_intake_real.py
git commit -m "feat(agents): real Intake agent with Claude Haiku structured output"
```

---

## Task 7: Real Company Researcher agent

**Files:**
- Create: `backend/src/apply/agents/company_researcher_real.py`
- Create: `backend/tests/agents/test_company_researcher_real.py`

- [ ] **Step 1: Write failing test (unit, mocks the LLM via TestModel)**

Create `backend/tests/agents/test_company_researcher_real.py`:

```python
import pytest
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from apply.agents.company_researcher_real import company_researcher_real
from apply.schemas.company import CompanyResearch


@pytest.mark.asyncio
async def test_company_researcher_real_returns_valid_research():
    test_model = TestModel(
        custom_output_args={
            "company_name": "Acme AI",
            "funding_stage": "Series A",
            "last_round": None,
            "team_size": "20-50",
            "founders": [
                {"name": "Jordan Smith", "background": "ex-Anthropic", "linkedin_url": None}
            ],
            "recent_news": [
                {"title": "Acme raises $12M Series A", "url": "https://techcrunch.com/acme", "date_iso": "2025-11-15", "summary": None}
            ],
            "recent_blog_posts": [],
            "tech_stack_hints": ["Python", "LangGraph"],
            "signal_score": 0.72,
            "sources": [
                {"url": "https://acme.ai", "title": "Acme homepage", "trust_score": 0.9}
            ],
        }
    )

    with models.override(test_model):
        result = await company_researcher_real(company_name="Acme AI")

    assert isinstance(result, CompanyResearch)
    assert result.company_name == "Acme AI"
    assert 0.0 <= result.signal_score <= 1.0
    assert result.founders
    assert result.sources
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_company_researcher_real.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the real Company Researcher**

Create `backend/src/apply/agents/company_researcher_real.py`:

```python
"""Real Company Researcher — Claude Sonnet 4.6 in a ReAct loop over Tavily + Firecrawl MCP.

Gathers structured company context (funding, founders, recent news, blogs,
tech stack hints) with source attribution and a signal_score reflecting
whether enough hook material was found to write a non-generic cover letter.
"""
from pydantic_ai import Agent

from apply.agents.mcp_servers import firecrawl_mcp, tavily_mcp
from apply.agents.models import sonnet
from apply.schemas.company import CompanyResearch

SYSTEM_PROMPT = """
You are a company researcher preparing context for a cover letter. Given a
company name, use the available tools to gather:

- funding stage and most recent round (amount, date if public)
- estimated team size
- founders (name + one-line background)
- recent news from the last 90 days
- 1-3 recent blog posts relevant to engineering culture/product philosophy
- tech stack hints (from JD mentions, engineering blog, job postings)

Tools:
- Tavily search tools — use these first to find authoritative URLs
- Firecrawl scrape — use to pull clean content from a specific page

Strategy:
1. Search for the company by name + "funding" to find recent coverage.
2. Search for the company's homepage or crunchbase page.
3. Scrape the most informative 1-3 pages for deeper detail.
4. Stop when you have enough to fill the CompanyResearch schema. Do not
   iterate forever — max 4-6 tool calls per run is plenty.

`signal_score` (0-1): high when you found specific, recent, distinctive
facts (a launch post, a named founder background, a funding date).
Low when the company is stealth or you only found generic content.

Be precise. Quote sources via the `sources` field. Do not hallucinate
funding amounts, dates, or names that you didn't see in a tool result.
"""


def _build_agent() -> Agent:
    """Construct the agent at call time so MCP servers bind to current loop."""
    return Agent(
        model=sonnet(),
        output_type=CompanyResearch,
        system_prompt=SYSTEM_PROMPT,
        mcp_servers=[tavily_mcp(), firecrawl_mcp()],
        retries=2,
    )


async def company_researcher_real(company_name: str) -> CompanyResearch:
    """Research a company using Tavily + Firecrawl MCP, return structured output."""
    agent = _build_agent()
    user_prompt = f"Research the company: {company_name}"
    async with agent.run_mcp_servers():
        result = await agent.run(user_prompt)
    return result.output
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_company_researcher_real.py -v
```

Expected: PASS (TestModel short-circuits the LLM call; MCP servers never spin up because `run_mcp_servers()` honors `models.override`).

Note: if the test fails because `models.override` doesn't bypass `run_mcp_servers()` in your pydantic-ai version, swap the test to mock `_build_agent` to return an agent without MCP servers:

```python
from unittest.mock import patch

@pytest.mark.asyncio
async def test_company_researcher_real_returns_valid_research():
    test_model = TestModel(custom_output_args={...})  # same as above

    from apply.agents import company_researcher_real as mod
    agent_stub = Agent(
        model=test_model,
        output_type=CompanyResearch,
        system_prompt="",
    )
    with patch.object(mod, "_build_agent", return_value=agent_stub):
        result = await mod.company_researcher_real(company_name="Acme AI")

    assert result.company_name == "Acme AI"
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/company_researcher_real.py backend/tests/agents/test_company_researcher_real.py
git commit -m "feat(agents): real Company Researcher with Tavily+Firecrawl MCP ReAct"
```

---

## Task 8: Real Fit Analyst agent

**Files:**
- Create: `backend/src/apply/agents/fit_analyst_real.py`
- Create: `backend/tests/agents/test_fit_analyst_real.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_fit_analyst_real.py`:

```python
import pytest
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from apply.agents.fit_analyst_real import fit_analyst_real
from apply.schemas.fit import FitAnalysis


@pytest.mark.asyncio
async def test_fit_analyst_real_returns_valid_analysis():
    test_model = TestModel(
        custom_output_args={
            "overall_score": 74,
            "verdict": "MODERATE",
            "matches": [
                {
                    "dimension": "Python",
                    "evidence_resume": "5 years Python as primary",
                    "evidence_jd": "5+ years Python required",
                    "strength": "strong",
                }
            ],
            "stretches": [],
            "gaps": [],
            "reasoning": "Strong language match, plausible stretch on MCP familiarity.",
            "recommended_action": "PROCEED",
        }
    )

    resume_md = "Senior Python engineer with 5 years of async systems experience."
    jd_md = "Founding Engineer. 5+ years Python. Experience with LLMs preferred."
    company_brief = "Acme AI — Series A, building long-running agents."

    with models.override(test_model):
        result = await fit_analyst_real(
            resume_markdown=resume_md,
            jd_markdown=jd_md,
            company_brief=company_brief,
        )

    assert isinstance(result, FitAnalysis)
    assert 0 <= result.overall_score <= 100
    assert result.verdict in {"STRONG", "MODERATE", "STRETCH", "WEAK"}
    assert result.recommended_action in {"PROCEED", "PROCEED_WITH_CAUTION", "SKIP"}
    assert result.reasoning
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_fit_analyst_real.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/fit_analyst_real.py`:

```python
"""Real Fit Analyst — Claude Sonnet 4.6 structured-output single-shot.

Given a resume + JD + company brief, produces a FitAnalysis with
direct resume-quote + JD-quote evidence for each match/stretch/gap.
"""
from pydantic_ai import Agent

from apply.agents.models import sonnet
from apply.schemas.fit import FitAnalysis

SYSTEM_PROMPT = """
You are a fit analyst evaluating a candidate against a job description,
with the company context in mind.

Produce a FitAnalysis with:
- `overall_score` (0-100): your calibrated estimate of fit
- `verdict`: STRONG (85+) | MODERATE (60-84) | STRETCH (40-59) | WEAK (<40)
- `matches`: dimensions where the resume clearly meets or exceeds a JD
  requirement. For each: a direct quote from the resume and a direct
  quote from the JD.
- `stretches`: dimensions where the candidate is plausible with framing
  but not a direct match.
- `gaps`: dimensions the JD requires that the resume does not clearly show.
- `reasoning`: 2-4 sentences summarizing the fit, honest about weaknesses.
- `recommended_action`:
  * PROCEED when overall_score >= 60 and no critical gaps
  * PROCEED_WITH_CAUTION when score 40-59 or there's one critical gap
    that could be framed around
  * SKIP when score < 40 or the role requires credentials (licensure,
    security clearance, visa-authorized location) the candidate lacks

Be honest. A good Fit Analyst saves the candidate time by skipping
poor fits, not by inflating scores.
"""

_agent = Agent(
    model=sonnet(),
    output_type=FitAnalysis,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def fit_analyst_real(
    resume_markdown: str,
    jd_markdown: str,
    company_brief: str,
) -> FitAnalysis:
    """Analyze fit and return a structured FitAnalysis."""
    user_prompt = (
        f"RESUME:\n---\n{resume_markdown}\n---\n\n"
        f"JOB DESCRIPTION:\n---\n{jd_markdown}\n---\n\n"
        f"COMPANY CONTEXT:\n---\n{company_brief}\n---"
    )
    result = await _agent.run(user_prompt)
    return result.output
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_fit_analyst_real.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/fit_analyst_real.py backend/tests/agents/test_fit_analyst_real.py
git commit -m "feat(agents): real Fit Analyst with Claude Sonnet structured output"
```

---

## Task 9: Runtime switch between stubs and real agents

**Files:**
- Create: `backend/src/apply/agents/runtime.py`
- Create: `backend/tests/agents/test_runtime.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/agents/test_runtime.py`:

```python
import pytest

from apply.agents import runtime


@pytest.mark.asyncio
async def test_runtime_routes_to_stub_when_flag_false(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")

    # Reset cached settings so monkeypatch is picked up
    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    listing = await runtime.intake(
        url="https://workatastartup.com/jobs/test",
        jd_text="(ignored in stub)",
        raw_html_path="/tmp/stub.html",
    )
    assert listing.company_name == "Acme AI"  # matches intake_stub fixture


@pytest.mark.asyncio
async def test_runtime_routes_to_real_when_flag_true(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")

    from apply import config as config_mod
    config_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    # Patch the real function to avoid a real LLM call
    from apply.agents import runtime as rt

    async def fake_intake_real(url, jd_text, raw_html_path):
        from apply.schemas.enums import JobSource, RemoteType
        from apply.schemas.job import JobListing
        return JobListing(
            id="job-real",
            source=JobSource.OTHER,
            url=url,
            application_url=url,
            company_name="Real Corp",
            role_title="Engineer",
            location="Remote",
            remote_type=RemoteType.REMOTE,
            description_markdown="",
            requirements=[],
            nice_to_haves=[],
            raw_html_path=raw_html_path,
        )

    monkeypatch.setattr(rt, "_intake_real", fake_intake_real)

    listing = await runtime.intake(
        url="https://example.com/jobs/1",
        jd_text="text",
        raw_html_path="/tmp/real.html",
    )
    assert listing.company_name == "Real Corp"
```

- [ ] **Step 2: Make `get_settings` cacheable + update config**

Modify `backend/src/apply/config.py` — replace the `get_settings` function with a cached version:

```python
from functools import lru_cache


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 3: Run test to verify failure (before runtime.py exists)**

```bash
cd backend && uv run pytest tests/agents/test_runtime.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apply.agents.runtime'`.

- [ ] **Step 4: Implement runtime switch**

Create `backend/src/apply/agents/runtime.py`:

```python
"""Runtime switch: routes agent calls to real or stub implementations
based on the `APPLY_USE_REAL_AGENTS` flag.

The orchestrator always calls functions from this module. Whether they
execute stubs or real LLM-backed agents is a config decision, not a
code-path decision.
"""
from apply.agents.company_researcher import company_researcher_stub as _cr_stub
from apply.agents.company_researcher_real import (
    company_researcher_real as _company_researcher_real,
)
from apply.agents.fit_analyst import fit_analyst_stub as _fa_stub
from apply.agents.fit_analyst_real import fit_analyst_real as _fit_analyst_real
from apply.agents.intake import intake_stub as _intake_stub
from apply.agents.intake_real import intake_real as _intake_real
from apply.config import get_settings
from apply.schemas.company import CompanyResearch
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing


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
    # Stub signature differs — adapt
    return await _fa_stub(job_listing_id="job-stub", resume_markdown=resume_markdown)
```

- [ ] **Step 5: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_runtime.py -v
```

Expected: PASS (both tests).

- [ ] **Step 6: Run full suite**

```bash
cd backend && uv run pytest --tb=no -q
```

Expected: prior tests + new tests all pass. Count ~53.

- [ ] **Step 7: Commit**

```bash
git add backend/src/apply/config.py backend/src/apply/agents/runtime.py backend/tests/agents/test_runtime.py
git commit -m "feat(agents): runtime switch between stubs and real via APPLY_USE_REAL_AGENTS"
```

---

## Task 10: Wire orchestrator through the runtime switch

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`

- [ ] **Step 1: Replace direct stub imports with runtime calls**

In `backend/src/apply/orchestrator/graph.py`, replace the existing imports and INTAKE_RUNNING / RESEARCHING branches so they call `runtime.intake`, `runtime.company_researcher`, and `runtime.fit_analyst` instead of the `_stub` functions directly.

Full updated file content:

```python
from dataclasses import dataclass, field
from typing import Any

from apply.agents import runtime
from apply.agents.cover_letter_writer import cover_letter_writer_stub
from apply.agents.form_fill import form_fill_stub
from apply.agents.memory_curator import memory_curator_stub
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
    # Phase 2a additions (optional, defaulted for backwards compat)
    jd_text: str = ""
    resume_markdown: str = "[stub resume]"


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
            listing = ctx.artifacts["job_listing"]
            with trace.span(name="cover_letter_writer"):
                letter = await cover_letter_writer_stub(
                    application_id=ctx.application_id,
                    company_name=listing["company_name"],
                )
            ctx.artifacts["cover_letter"] = letter.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.03
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

- [ ] **Step 2: Run the full test suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all tests pass (stubs still selected because `APPLY_USE_REAL_AGENTS` defaults to false). Count stays at ~53.

If tests that construct `PipelineContext` positionally fail because of the new fields, fix by adjusting them to named kwargs or providing defaults — all existing tests should already use the `run_id=..., application_id=..., jd_url=..., state=...` pattern which is unaffected.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py
git commit -m "feat(orchestrator): route agent calls through runtime switch"
```

---

## Task 11: Scrape JD text at intake time

**Files:**
- Modify: `backend/src/apply/api/routes_applications.py`

This task makes the real intake actually fed with real JD text. In Phase 1 the stub ignored `jd_text`; the real agent needs the actual posting body.

- [ ] **Step 1: Update routes_applications.py to scrape JD text via Firecrawl when real agents are on**

Replace `backend/src/apply/api/routes_applications.py`:

```python
import asyncio

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from apply.agents import runtime
from apply.config import get_settings
from apply.db.models import User as UserRow
from apply.db.session import get_session
from apply.orchestrator.events import get_event_bus
from apply.orchestrator.graph import PipelineContext, run_to_next_checkpoint
from apply.orchestrator.run_repository import RunRepository
from apply.schemas.enums import ApplicationStatus, PipelineRunState

router = APIRouter(prefix="/applications", tags=["applications"])


class CreateApplicationRequest(BaseModel):
    jd_url: HttpUrl


class CreateApplicationResponse(BaseModel):
    run_id: str
    application_id: str
    state: str


async def _ensure_local_user(session: AsyncSession) -> str:
    from sqlalchemy import select

    result = await session.execute(select(UserRow).where(UserRow.id == "user-local"))
    existing = result.scalar_one_or_none()
    if existing is None:
        session.add(
            UserRow(
                id="user-local",
                email="local@apply.dev",
                name="Local Dev",
                profile_json={},
            )
        )
        await session.flush()
    return "user-local"


async def _fetch_jd_text(url: str) -> str:
    """Fetch the JD as markdown via Firecrawl; fall back to raw HTTP if unconfigured."""
    settings = get_settings()
    if settings.firecrawl_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
                    json={"url": url, "formats": ["markdown"]},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    md = data.get("markdown") or data.get("content")
                    if md:
                        return md
        except httpx.HTTPError:
            pass
    # Fallback: plain HTTP, return raw body text
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            return resp.text[:50_000]
    except httpx.HTTPError:
        return ""


@router.post("", response_model=CreateApplicationResponse, status_code=201)
async def create_application(
    req: CreateApplicationRequest,
    session: AsyncSession = Depends(get_session),
) -> CreateApplicationResponse:
    settings = get_settings()
    jd_text = ""
    if settings.apply_use_real_agents:
        jd_text = await _fetch_jd_text(str(req.jd_url))

    user_id = await _ensure_local_user(session)

    # Preview listing so we can attach something to the Application row.
    # Uses runtime (stub in dev-default, real if flag on).
    listing = await runtime.intake(
        url=str(req.jd_url),
        jd_text=jd_text,
        raw_html_path="/tmp/apply/intake-preview.html",
    )

    repo = RunRepository(session)
    app_id = await repo.create_application_row(
        user_id=user_id,
        job_listing_json=listing.model_dump(mode="json"),
        status=ApplicationStatus.DRAFTING,
    )
    run_id = await repo.create_run(
        application_id=app_id,
        initial_state=PipelineRunState.INTAKE_RUNNING,
    )

    ctx = PipelineContext(
        run_id=run_id,
        application_id=app_id,
        jd_url=str(req.jd_url),
        state=PipelineRunState.INTAKE_RUNNING,
        jd_text=jd_text,
    )
    ctx.artifacts["job_listing"] = listing.model_dump(mode="json")

    asyncio.create_task(_drive_pipeline(run_id, ctx))

    return CreateApplicationResponse(
        run_id=run_id,
        application_id=app_id,
        state=ctx.state.value,
    )


async def _drive_pipeline(run_id: str, ctx: PipelineContext) -> None:
    bus = get_event_bus()
    await bus.publish(run_id, {"type": "run_started", "state": ctx.state.value})
    try:
        await run_to_next_checkpoint(ctx)
    except Exception as e:
        await bus.publish(run_id, {"type": "error", "message": str(e)})
        return

    from apply.db.session import get_session as session_dep

    async for s in session_dep():
        repo = RunRepository(s)
        await repo.update_run(
            run_id=run_id,
            state=ctx.state,
            cost_accumulated_usd=ctx.cost_accumulated_usd,
            artifacts=ctx.artifacts,
        )
        break

    await bus.publish(
        run_id,
        {
            "type": "checkpoint_reached",
            "state": ctx.state.value,
            "artifacts": ctx.artifacts,
        },
    )
```

- [ ] **Step 2: Run full test suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all tests pass. The `_fetch_jd_text` is only called when `apply_use_real_agents=true`, which is false in tests — so tests don't hit the network.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/api/routes_applications.py
git commit -m "feat(api): fetch JD text via Firecrawl when real agents are enabled"
```

---

## Task 12: Live integration test (opt-in, skipped without API keys)

**Files:**
- Create: `backend/tests/test_integration_real_agents.py`

- [ ] **Step 1: Write opt-in live test**

Create `backend/tests/test_integration_real_agents.py`:

```python
"""Live integration test. Runs against real Anthropic + Tavily + Firecrawl.

Skipped unless ANTHROPIC_API_KEY, TAVILY_API_KEY, and FIRECRAWL_API_KEY
are all set. Costs ~$0.10 per run. Not run in CI.
"""
import os

import pytest

from apply.agents import runtime
from apply.schemas.company import CompanyResearch
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing

REQUIRED_KEYS = ("ANTHROPIC_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY")
_HAS_KEYS = all(os.getenv(k) for k in REQUIRED_KEYS)


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_intake_on_sample_text(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    sample = """
    Founding Engineer at Acme AI (YC W24).
    San Francisco, hybrid. $180k-$240k + equity.
    Requirements: 5+ years Python, LLM experience. Nice to have: LangGraph.
    """
    result = await runtime.intake(
        url="https://workatastartup.com/jobs/test-123",
        jd_text=sample,
        raw_html_path="/tmp/apply/test.html",
    )
    assert isinstance(result, JobListing)
    assert "Acme" in result.company_name
    assert result.requirements


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_fit_analyst(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.fit_analyst(
        resume_markdown="Senior Python engineer, 5 years async + ML infra.",
        jd_markdown="Founding engineer. 5+ years Python. LLM experience required.",
        company_brief="Acme AI — Series A, building agents.",
    )
    assert isinstance(result, FitAnalysis)
    assert 0 <= result.overall_score <= 100


@pytest.mark.skipif(not _HAS_KEYS, reason="Missing live API keys")
@pytest.mark.asyncio
async def test_real_company_researcher(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    result = await runtime.company_researcher(company_name="Anthropic")
    assert isinstance(result, CompanyResearch)
    assert result.company_name
    assert result.sources
```

- [ ] **Step 2: Run the file**

```bash
cd backend && uv run pytest tests/test_integration_real_agents.py -v
```

Expected **without keys**: 3 SKIPPED with reason "Missing live API keys".
Expected **with keys**: 3 PASS, real API calls made, costs ~$0.10 total.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration_real_agents.py
git commit -m "test(integration): opt-in live real-agent tests"
```

---

## Task 13: LEARNINGS entry + README note for Phase 2a

**Files:**
- Modify: `LEARNINGS.md`
- Modify: `README.md`

- [ ] **Step 1: Append LEARNINGS entry**

Append to `LEARNINGS.md`:

```markdown

## 2026-04-23 — Stub/real runtime switch isolates skeleton from LLM dependencies
Tags: architecture, agent-design, product-decisions

Shipped Phase 2a (real Intake + Company Researcher + Fit Analyst) behind an
`APPLY_USE_REAL_AGENTS` env flag. The orchestrator only ever calls
`apply.agents.runtime.*`; the runtime module decides stub vs real based
on config at the point of call.

Why this mattered:
- Unit tests don't need API keys or network
- The skeleton demo still works when keys aren't configured
- Future chunks can replace agents one at a time the same way — the
  runtime module grows one entry per replacement
- VCR cassettes capture LLM shapes once, so tests stay fast and
  deterministic even as we add real calls

**Takeaway:** when adding a layer that has two implementations (stub/real,
local/cloud, batch/stream), put the switch at the module boundary, not
inside agent code. One clean env flag, one routing file, one line in every
test to flip it.

---
```

- [ ] **Step 2: Update README**

In `README.md`, replace the `Status:` callout with:

```markdown
> **Status:** Phase 2a complete. Real Intake, Company Researcher, and
> Fit Analyst agents are wired behind the `APPLY_USE_REAL_AGENTS` flag.
> Walking skeleton still runs with stubs by default. Phase 2b (eval
> harness + baseline comparison) is next.
```

Add a section after "Local development":

```markdown

## Running with real agents

Set `APPLY_USE_REAL_AGENTS=true` in `.env` and ensure these keys are set:

- `ANTHROPIC_API_KEY` — Claude Haiku + Sonnet
- `TAVILY_API_KEY` — web search (free tier: 1000/mo)
- `FIRECRAWL_API_KEY` — scraping (free tier: 500/mo)

Also needs `npx` in PATH — the Tavily and Firecrawl MCP servers run as
Node subprocesses.

With keys set, the live integration test runs:

```bash
cd backend && uv run pytest tests/test_integration_real_agents.py -v
```
```

- [ ] **Step 3: Commit**

```bash
git add LEARNINGS.md README.md
git commit -m "docs: Phase 2a LEARNINGS entry + README section on real-agents mode"
```

---

## Task 14: Final verification

- [ ] **Step 1: Full test suite green**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all prior tests (46) + Task 2 config (2) + Task 6 intake (1) + Task 7 company_researcher (1) + Task 8 fit_analyst (1) + Task 9 runtime (2) + Task 12 live (3 skipped without keys) = **~56 passed**, 3 skipped (live tests).

- [ ] **Step 2: Ruff clean**

```bash
cd backend && uv run ruff check src/ tests/
```

If any issues, fix minimally and commit as `chore: ruff cleanup for Phase 2a`.

- [ ] **Step 3: Walking skeleton still demoable end-to-end**

```bash
cd backend && uv run pytest tests/test_e2e_skeleton.py -v
```

Expected: 1 passed. (Still uses stubs — that's the point.)

- [ ] **Step 4: Tag milestone**

```bash
git tag v0.2.0-real-research-agents
```

---

## Self-review checklist

Before declaring the plan done:

- [ ] Every real-agent task (Intake, Company Researcher, Fit Analyst) has a unit test that passes without network via `TestModel` or mock
- [ ] Every real-agent task lands the code at its canonical path under `backend/src/apply/agents/*_real.py`
- [ ] The runtime switch (Task 9) is exercised by a test in both directions (stub + real)
- [ ] The orchestrator (Task 10) only imports from `apply.agents.runtime`, never from `_stub` or `_real` files directly
- [ ] The live integration test (Task 12) is opt-in via env keys and won't run in CI without keys
- [ ] README explains how to enable real agents and what the costs/dependencies are
- [ ] Commit messages verbatim, no co-author trailer on any
- [ ] The walking skeleton still passes end-to-end with stubs

---

## Out of scope for this plan (Phase 2b and beyond)

- Goldenset with 5 curated JDs + expected fact recall
- LLM-as-judge evaluator on cover letters
- Baseline comparison table (Claude one-shot vs Perplexity vs S)
- Trajectory evals via Langfuse span inspection
- `apply bench` CLI command
- Cover Letter Writer, Screening Answerer, Form-Fill, Memory Curator real implementations
- Resume upload flow + onboarding UI
- Dashboard + outcome logging

Each will get its own plan in its phase.
