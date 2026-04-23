# Apply — Phase 0 + Phase 1 Implementation Plan (Walking Skeleton)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the project foundation (Phase 0) and build a walking skeleton (Phase 1) where every layer of the pipeline is wired end-to-end with stub agents, so subsequent phases can drop in real agents one at a time without re-architecting.

**Architecture:** Python 3.12 FastAPI backend with Pydantic AI orchestration over a Postgres-backed state machine. Stub agents return hardcoded fixtures that conform to the real schemas. Existing TanStack Start frontend subscribes to agent events via SSE and exposes 3 HITL approval screens. Everything runs locally under Docker Compose (Postgres + Langfuse). ChromaDB runs embedded in the backend process.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, Pydantic AI, SQLAlchemy 2.0 async, asyncpg, Alembic, sse-starlette, Langfuse, pytest, httpx. Frontend: TanStack Start (existing), React 19, EventSource.

**What this plan does NOT cover:** Real LLM calls, real MCP servers, real browser automation, real evals. Those arrive in Phase 2–5 plans.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md`

---

## File map (what gets created/modified in this plan)

**Repo root:**
- Modify: `package.json` (rename project)
- Create: `docker-compose.yml`
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `LEARNINGS.md`

**Backend (new):**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/src/apply/__init__.py`
- Create: `backend/src/apply/config.py`
- Create: `backend/src/apply/schemas/__init__.py`
- Create: `backend/src/apply/schemas/enums.py`
- Create: `backend/src/apply/schemas/job.py`
- Create: `backend/src/apply/schemas/company.py`
- Create: `backend/src/apply/schemas/fit.py`
- Create: `backend/src/apply/schemas/writing.py`
- Create: `backend/src/apply/schemas/application.py`
- Create: `backend/src/apply/db/__init__.py`
- Create: `backend/src/apply/db/session.py`
- Create: `backend/src/apply/db/models.py`
- Create: `backend/src/apply/db/alembic.ini`
- Create: `backend/src/apply/db/migrations/env.py`
- Create: `backend/src/apply/db/migrations/script.py.mako`
- Create: `backend/src/apply/db/migrations/versions/.gitkeep`
- Create: `backend/src/apply/orchestrator/__init__.py`
- Create: `backend/src/apply/orchestrator/state_machine.py`
- Create: `backend/src/apply/orchestrator/graph.py`
- Create: `backend/src/apply/agents/__init__.py`
- Create: `backend/src/apply/agents/intake.py`
- Create: `backend/src/apply/agents/company_researcher.py`
- Create: `backend/src/apply/agents/fit_analyst.py`
- Create: `backend/src/apply/agents/cover_letter_writer.py`
- Create: `backend/src/apply/agents/screening_answerer.py`
- Create: `backend/src/apply/agents/form_fill.py`
- Create: `backend/src/apply/agents/memory_curator.py`
- Create: `backend/src/apply/api/__init__.py`
- Create: `backend/src/apply/api/main.py`
- Create: `backend/src/apply/api/routes_health.py`
- Create: `backend/src/apply/api/routes_applications.py`
- Create: `backend/src/apply/api/routes_runs.py`
- Create: `backend/src/apply/api/sse.py`
- Create: `backend/src/apply/observability/__init__.py`
- Create: `backend/src/apply/observability/langfuse_setup.py`
- Create: `backend/src/apply/cli.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_config.py`
- Create: `backend/tests/test_schemas.py`
- Create: `backend/tests/test_state_machine.py`
- Create: `backend/tests/test_agents_stub.py`
- Create: `backend/tests/test_orchestrator.py`
- Create: `backend/tests/test_api_health.py`
- Create: `backend/tests/test_api_applications.py`
- Create: `backend/tests/test_api_sse.py`

**Frontend (existing repo, additions):**
- Create: `src/lib/api.ts`
- Create: `src/lib/sse.ts`
- Create: `src/lib/types.ts`
- Create: `src/routes/applications.index.tsx`
- Create: `src/routes/applications.new.tsx`
- Create: `src/routes/applications.$id.tsx`
- Create: `src/components/PipelineTimeline.tsx`
- Create: `src/components/HitlFitGate.tsx`
- Create: `src/components/HitlContentApproval.tsx`
- Create: `src/components/HitlSubmissionGate.tsx`
- Modify: `src/routes/__root.tsx` (add nav link)

---

## Phase 0 — Bootstrap (Tasks 1-6)

### Task 1: Rename project + set up root config files

**Files:**
- Modify: `package.json` (name field)
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `LEARNINGS.md`

- [ ] **Step 1: Update `package.json` name**

Modify the `name` field from `"clarity-research-agent"` to `"apply"`:

```json
{
  "name": "apply",
  "private": true,
  "type": "module",
  ...
}
```

- [ ] **Step 2: Create `.env.example` at repo root**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://apply:apply@localhost:5432/apply

# LLM Providers (not needed for Phase 1 stubs, but wired now)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Tools (not needed for Phase 1)
TAVILY_API_KEY=
FIRECRAWL_API_KEY=

# Observability
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3001

# App
APPLY_ENV=dev
APPLY_PORT=8000
APPLY_COST_CAP_USD=0.50
APPLY_DAILY_CAP_USD=5.00
```

- [ ] **Step 3: Extend `.gitignore` for Python and env**

Append to existing `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
backend/.venv/
backend/dist/
backend/build/
backend/*.egg-info/
backend/.pytest_cache/
backend/.ruff_cache/
backend/.mypy_cache/

# Environment
.env
.env.*
!.env.example

# Databases (local)
*.db
*.sqlite
*.sqlite3
backend/data/
```

- [ ] **Step 4: Create `LEARNINGS.md` skeleton**

```markdown
# Learnings — Apply

A running log of non-obvious things learned building this project.

## Top 5 lessons (synthesized, updated as we go)

_Will fill as patterns emerge._

## Index by tag

- `agent-design`
- `prompt-engineering`
- `mcp`
- `tooling`
- `debugging`
- `architecture`
- `product-decisions`
- `eval`

---

## YYYY-MM-DD — template entry
Tags: tag-1, tag-2

[Context: what I was doing]

[What happened / what I found]

**Takeaway:** [the insight, not the event]
```

- [ ] **Step 5: Commit**

```bash
git add package.json .env.example .gitignore LEARNINGS.md
git commit -m "chore: rename project to Apply; add root config scaffolding"
```

---

### Task 2: Docker Compose for Postgres and Langfuse

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `docker-compose.yml` at repo root**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: apply-postgres
    environment:
      POSTGRES_USER: apply
      POSTGRES_PASSWORD: apply
      POSTGRES_DB: apply
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U apply"]
      interval: 5s
      timeout: 5s
      retries: 5

  langfuse-db:
    image: postgres:16-alpine
    container_name: apply-langfuse-db
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    volumes:
      - langfuse_data:/var/lib/postgresql/data

  langfuse:
    image: langfuse/langfuse:latest
    container_name: apply-langfuse
    depends_on:
      - langfuse-db
    ports:
      - "3001:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
      NEXTAUTH_SECRET: dev-only-secret-change-in-prod
      SALT: dev-only-salt-change-in-prod
      NEXTAUTH_URL: http://localhost:3001
      TELEMETRY_ENABLED: "false"

volumes:
  postgres_data:
  langfuse_data:
```

- [ ] **Step 2: Bring up services and verify**

```bash
docker compose up -d
docker compose ps
```

Expected: both `apply-postgres` and `apply-langfuse` show `running (healthy)` / `running` within ~30s.

- [ ] **Step 3: Verify Postgres is reachable**

```bash
docker exec apply-postgres psql -U apply -d apply -c "SELECT 1;"
```

Expected output: a table with `?column?` and value `1`.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add docker-compose for Postgres and Langfuse"
```

---

### Task 3: Python backend skeleton with uv

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/src/apply/__init__.py`

- [ ] **Step 1: Create `backend/.python-version`**

```
3.12
```

- [ ] **Step 2: Create `backend/pyproject.toml`**

```toml
[project]
name = "apply"
version = "0.1.0"
description = "Autonomous job application agent"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "pydantic-ai>=0.0.14",
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

[project.scripts]
apply = "apply.cli:main"

[dependency-groups]
dev = [
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/apply"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
```

- [ ] **Step 3: Create package init**

Create `backend/src/apply/__init__.py` with content:

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Sync dependencies**

```bash
cd backend && uv sync
```

Expected: creates `.venv/`, installs all dependencies, exits 0.

- [ ] **Step 5: Verify Python env**

```bash
cd backend && uv run python -c "import fastapi, pydantic_ai, sqlalchemy; print('ok')"
```

Expected output: `ok`

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/.python-version backend/src/apply/__init__.py
# .gitignore already covers backend/.venv and uv.lock is OK to commit
git add backend/uv.lock
git commit -m "chore(backend): initialize Python package with uv"
```

---

### Task 4: Config loader via pydantic-settings

**Files:**
- Create: `backend/src/apply/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/__init__.py` (empty file), then `backend/tests/test_config.py`:

```python
from apply.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("APPLY_ENV", "test")
    monkeypatch.setenv("APPLY_COST_CAP_USD", "0.75")

    settings = Settings()

    assert settings.database_url == "postgresql+asyncpg://u:p@h/db"
    assert settings.apply_env == "test"
    assert settings.apply_cost_cap_usd == 0.75


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")

    settings = Settings()

    assert settings.apply_env == "dev"
    assert settings.apply_port == 8000
    assert settings.apply_cost_cap_usd == 0.50
    assert settings.apply_daily_cap_usd == 5.00
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apply.config'`.

- [ ] **Step 3: Implement `config.py`**

Create `backend/src/apply/config.py`:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(alias="DATABASE_URL")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    firecrawl_api_key: str = Field(default="", alias="FIRECRAWL_API_KEY")

    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="http://localhost:3001", alias="LANGFUSE_HOST")

    apply_env: str = Field(default="dev", alias="APPLY_ENV")
    apply_port: int = Field(default=8000, alias="APPLY_PORT")
    apply_cost_cap_usd: float = Field(default=0.50, alias="APPLY_COST_CAP_USD")
    apply_daily_cap_usd: float = Field(default=5.00, alias="APPLY_DAILY_CAP_USD")


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_config.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/config.py backend/tests/__init__.py backend/tests/test_config.py
git commit -m "feat(config): add settings loader with env-var support"
```

---

### Task 5: FastAPI app with `/health` endpoint

**Files:**
- Create: `backend/src/apply/api/__init__.py`
- Create: `backend/src/apply/api/routes_health.py`
- Create: `backend/src/apply/api/main.py`
- Create: `backend/tests/test_api_health.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_api_health.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from apply.api.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_health_returns_ok(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_api_health.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apply.api'`.

- [ ] **Step 3: Create API package**

Create `backend/src/apply/api/__init__.py` (empty).

- [ ] **Step 4: Implement health route**

Create `backend/src/apply/api/routes_health.py`:

```python
from fastapi import APIRouter

from apply import __version__

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
```

- [ ] **Step 5: Implement app factory**

Create `backend/src/apply/api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apply.api.routes_health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Apply", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)

    return app


app = create_app()
```

- [ ] **Step 6: Run test**

```bash
cd backend && uv run pytest tests/test_api_health.py -v
```

Expected: PASS.

- [ ] **Step 7: Verify live server works**

Terminal A:

```bash
cd backend && uv run uvicorn apply.api.main:app --host 0.0.0.0 --port 8000
```

Terminal B:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","version":"0.1.0"}`

Kill Terminal A with Ctrl-C.

- [ ] **Step 8: Commit**

```bash
git add backend/src/apply/api/ backend/tests/test_api_health.py
git commit -m "feat(api): add FastAPI app with /health endpoint"
```

---

### Task 6: Frontend → backend /health integration

**Files:**
- Create: `src/lib/api.ts`
- Create: `src/lib/types.ts`
- Modify: `src/routes/__root.tsx`

- [ ] **Step 1: Create API client**

Create `src/lib/api.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<{ status: string; version: string }> {
  return apiFetch("/health");
}
```

- [ ] **Step 2: Create types file (placeholder for later)**

Create `src/lib/types.ts`:

```typescript
// Shared types between frontend and backend.
// Will grow as we add endpoints.

export type HealthResponse = {
  status: string;
  version: string;
};
```

- [ ] **Step 3: Add health indicator to root layout**

Read current `src/routes/__root.tsx` first, then add an effect that pings the backend. The exact edit depends on the current file. Find the component that renders the nav/shell, and add inside it:

```tsx
import { useEffect, useState } from "react";
import { getHealth } from "#/lib/api";

// Inside the shell component:
const [backend, setBackend] = useState<"unknown" | "up" | "down">("unknown");

useEffect(() => {
  getHealth()
    .then(() => setBackend("up"))
    .catch(() => setBackend("down"));
}, []);

// In the JSX:
<span className={`text-sm ${backend === "up" ? "text-green-600" : "text-red-600"}`}>
  backend: {backend}
</span>
```

- [ ] **Step 4: Run both stacks and verify integration**

Terminal A:

```bash
cd backend && uv run uvicorn apply.api.main:app --port 8000
```

Terminal B:

```bash
pnpm dev
```

Open `http://localhost:3000`. Expected: the nav bar shows `backend: up` in green.

Kill both.

- [ ] **Step 5: Commit**

```bash
git add src/lib/api.ts src/lib/types.ts src/routes/__root.tsx
git commit -m "feat(frontend): wire /health check into root layout"
```

---

## Phase 1 — Walking skeleton (Tasks 7-44)

### Section A: Schemas (Tasks 7-12)

### Task 7: Core enums module

**Files:**
- Create: `backend/src/apply/schemas/__init__.py`
- Create: `backend/src/apply/schemas/enums.py`

- [ ] **Step 1: Write failing test**

Append to `backend/tests/test_schemas.py` (create the file):

```python
from apply.schemas.enums import (
    ApplicationStatus,
    FitVerdict,
    JobSource,
    PipelineRunState,
    RecommendedAction,
    RemoteType,
)


def test_job_source_values():
    assert JobSource.YC_WAAS.value == "YC_WAAS"
    assert JobSource.GREENHOUSE.value == "GREENHOUSE"
    assert JobSource.OTHER.value == "OTHER"


def test_fit_verdict_values():
    assert FitVerdict.STRONG.value == "STRONG"
    assert FitVerdict.WEAK.value == "WEAK"


def test_recommended_action_values():
    assert RecommendedAction.PROCEED.value == "PROCEED"
    assert RecommendedAction.SKIP.value == "SKIP"


def test_pipeline_run_state_has_all_checkpoints():
    # Every HITL gate must be representable
    states = {s.value for s in PipelineRunState}
    assert "AWAITING_FIT_APPROVAL" in states
    assert "AWAITING_CONTENT_APPROVAL" in states
    assert "AWAITING_SUBMIT_APPROVAL" in states
    assert "COMPLETED" in states


def test_application_status_values():
    assert ApplicationStatus.DRAFTING.value == "DRAFTING"
    assert ApplicationStatus.SUBMITTED.value == "SUBMITTED"


def test_remote_type_values():
    assert RemoteType.REMOTE.value == "REMOTE"
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_schemas.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create schemas package + enums**

Create `backend/src/apply/schemas/__init__.py` (empty).

Create `backend/src/apply/schemas/enums.py`:

```python
from enum import StrEnum


class JobSource(StrEnum):
    YC_WAAS = "YC_WAAS"
    WELLFOUND = "WELLFOUND"
    GREENHOUSE = "GREENHOUSE"
    LEVER = "LEVER"
    ASHBY = "ASHBY"
    WORKDAY = "WORKDAY"
    COMPANY_PAGE = "COMPANY_PAGE"
    OTHER = "OTHER"


class RemoteType(StrEnum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"


class FitVerdict(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    STRETCH = "STRETCH"
    WEAK = "WEAK"


class FitStrength(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class RecommendedAction(StrEnum):
    PROCEED = "PROCEED"
    PROCEED_WITH_CAUTION = "PROCEED_WITH_CAUTION"
    SKIP = "SKIP"


class ScreeningAnswerOrigin(StrEnum):
    PROACTIVE = "PROACTIVE"
    FORM_FILL_CALLBACK = "FORM_FILL_CALLBACK"


class ApplicationStatus(StrEnum):
    DRAFTING = "DRAFTING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    SUBMITTED = "SUBMITTED"
    SUBMITTED_UNCONFIRMED = "SUBMITTED_UNCONFIRMED"
    REPLIED = "REPLIED"
    INTERVIEWED = "INTERVIEWED"
    REJECTED = "REJECTED"
    GHOSTED = "GHOSTED"
    SKIPPED = "SKIPPED"


class PipelineRunState(StrEnum):
    INTAKE_RUNNING = "INTAKE_RUNNING"
    RESEARCHING = "RESEARCHING"
    AWAITING_FIT_APPROVAL = "AWAITING_FIT_APPROVAL"
    DRAFTING = "DRAFTING"
    AWAITING_CONTENT_APPROVAL = "AWAITING_CONTENT_APPROVAL"
    FILLING_FORM = "FILLING_FORM"
    AWAITING_SUBMIT_APPROVAL = "AWAITING_SUBMIT_APPROVAL"
    SUBMITTING = "SUBMITTING"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    ERRORED = "ERRORED"


class HitlCheckpoint(StrEnum):
    FIT = "FIT"
    CONTENT = "CONTENT"
    SUBMIT = "SUBMIT"


class HitlDecisionType(StrEnum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REGENERATE = "REGENERATE"
    SKIP = "SKIP"
    CANCEL = "CANCEL"
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v
```

Expected: PASS on all enum tests.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/schemas/ backend/tests/test_schemas.py
git commit -m "feat(schemas): add core enums for pipeline states and verdicts"
```

---

### Task 8: JobListing schema

**Files:**
- Create: `backend/src/apply/schemas/job.py`
- Modify: `backend/tests/test_schemas.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_schemas.py`:

```python
from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing


def test_job_listing_minimal_valid():
    listing = JobListing(
        id="job-1",
        source=JobSource.YC_WAAS,
        url="https://workatastartup.com/jobs/123",
        application_url="https://workatastartup.com/jobs/123/apply",
        company_name="Acme AI",
        role_title="Founding Engineer",
        location="San Francisco, CA",
        remote_type=RemoteType.HYBRID,
        description_markdown="Build agents.",
        requirements=["Python", "Agents"],
        nice_to_haves=["LangGraph experience"],
        raw_html_path="/tmp/jd/job-1.html",
    )

    assert listing.id == "job-1"
    assert listing.source == JobSource.YC_WAAS
    assert len(listing.requirements) == 2
    assert listing.compensation_range is None


def test_job_listing_rejects_bad_url():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        JobListing(
            id="job-2",
            source=JobSource.OTHER,
            url="not-a-url",
            application_url="also-not-a-url",
            company_name="X",
            role_title="Y",
            location="Z",
            remote_type=RemoteType.REMOTE,
            description_markdown="",
            requirements=[],
            nice_to_haves=[],
            raw_html_path="/tmp/x",
        )
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k job_listing
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apply.schemas.job'`.

- [ ] **Step 3: Implement JobListing**

Create `backend/src/apply/schemas/job.py`:

```python
from pydantic import BaseModel, HttpUrl

from apply.schemas.enums import JobSource, RemoteType


class JobListing(BaseModel):
    id: str
    source: JobSource
    url: HttpUrl
    application_url: HttpUrl
    company_name: str
    role_title: str
    location: str
    remote_type: RemoteType
    description_markdown: str
    requirements: list[str]
    nice_to_haves: list[str]
    compensation_range: str | None = None
    raw_html_path: str
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k job_listing
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/schemas/job.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add JobListing schema"
```

---

### Task 9: CompanyResearch schema

**Files:**
- Create: `backend/src/apply/schemas/company.py`
- Modify: `backend/tests/test_schemas.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_schemas.py`:

```python
from apply.schemas.company import (
    BlogPost,
    CompanyResearch,
    Founder,
    NewsItem,
    Round,
    Source,
)


def test_company_research_with_all_subtypes():
    research = CompanyResearch(
        company_name="Acme AI",
        funding_stage="Series A",
        last_round=Round(stage="Series A", amount_usd=10_000_000, date_iso="2025-11-01"),
        team_size="20-50",
        founders=[Founder(name="A. Smith", background="ex-Google, Stanford PhD")],
        recent_news=[
            NewsItem(
                title="Acme raises Series A",
                url="https://techcrunch.com/acme-a",
                date_iso="2025-11-01",
                summary="$10M to build agents",
            )
        ],
        recent_blog_posts=[
            BlogPost(
                title="Why we build agents",
                url="https://acme.ai/blog/agents",
                summary="Product philosophy",
            )
        ],
        tech_stack_hints=["Python", "LangGraph"],
        signal_score=0.85,
        sources=[Source(url="https://acme.ai", title="Acme homepage", trust_score=0.9)],
    )

    assert research.company_name == "Acme AI"
    assert research.signal_score == 0.85
    assert len(research.founders) == 1
    assert research.last_round is not None


def test_signal_score_bounded():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CompanyResearch(
            company_name="X",
            founders=[],
            recent_news=[],
            recent_blog_posts=[],
            tech_stack_hints=[],
            signal_score=1.5,  # invalid: > 1.0
            sources=[],
        )
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k company_research
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement CompanyResearch**

Create `backend/src/apply/schemas/company.py`:

```python
from pydantic import BaseModel, Field, HttpUrl


class Round(BaseModel):
    stage: str
    amount_usd: int | None = None
    date_iso: str | None = None


class Founder(BaseModel):
    name: str
    background: str | None = None
    linkedin_url: HttpUrl | None = None


class NewsItem(BaseModel):
    title: str
    url: HttpUrl
    date_iso: str | None = None
    summary: str | None = None


class BlogPost(BaseModel):
    title: str
    url: HttpUrl
    summary: str | None = None


class Source(BaseModel):
    url: HttpUrl
    title: str
    trust_score: float = Field(ge=0.0, le=1.0)


class CompanyResearch(BaseModel):
    company_name: str
    funding_stage: str | None = None
    last_round: Round | None = None
    team_size: str | None = None
    founders: list[Founder]
    recent_news: list[NewsItem]
    recent_blog_posts: list[BlogPost]
    tech_stack_hints: list[str]
    signal_score: float = Field(ge=0.0, le=1.0)
    sources: list[Source]
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k company_research
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/schemas/company.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add CompanyResearch and related subtypes"
```

---

### Task 10: FitAnalysis + FitPoint schemas

**Files:**
- Create: `backend/src/apply/schemas/fit.py`
- Modify: `backend/tests/test_schemas.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_schemas.py`:

```python
from apply.schemas.enums import FitStrength, FitVerdict, RecommendedAction
from apply.schemas.fit import FitAnalysis, FitPoint


def test_fit_analysis_minimal_valid():
    analysis = FitAnalysis(
        overall_score=72,
        verdict=FitVerdict.MODERATE,
        matches=[
            FitPoint(
                dimension="Python",
                evidence_resume="5 years Python, primary language",
                evidence_jd="Strong Python required",
                strength=FitStrength.STRONG,
            )
        ],
        stretches=[
            FitPoint(
                dimension="LangGraph",
                evidence_resume=None,
                evidence_jd="Experience with LangGraph preferred",
                strength=FitStrength.WEAK,
            )
        ],
        gaps=[],
        reasoning="Solid Python, thin on LangGraph but learnable.",
        recommended_action=RecommendedAction.PROCEED,
    )

    assert analysis.overall_score == 72
    assert analysis.verdict == FitVerdict.MODERATE
    assert analysis.recommended_action == RecommendedAction.PROCEED


def test_fit_score_must_be_0_to_100():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FitAnalysis(
            overall_score=150,  # invalid
            verdict=FitVerdict.STRONG,
            matches=[],
            stretches=[],
            gaps=[],
            reasoning="",
            recommended_action=RecommendedAction.PROCEED,
        )
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k fit_analysis
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement FitAnalysis**

Create `backend/src/apply/schemas/fit.py`:

```python
from pydantic import BaseModel, Field

from apply.schemas.enums import FitStrength, FitVerdict, RecommendedAction


class FitPoint(BaseModel):
    dimension: str
    evidence_resume: str | None
    evidence_jd: str
    strength: FitStrength


class FitAnalysis(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    verdict: FitVerdict
    matches: list[FitPoint]
    stretches: list[FitPoint]
    gaps: list[FitPoint]
    reasoning: str
    recommended_action: RecommendedAction
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k fit_analysis
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/schemas/fit.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add FitAnalysis and FitPoint"
```

---

### Task 11: CoverLetter + ScreeningAnswer schemas

**Files:**
- Create: `backend/src/apply/schemas/writing.py`
- Modify: `backend/tests/test_schemas.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_schemas.py`:

```python
from datetime import datetime

from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import CoverLetter, ScreeningAnswer


def test_cover_letter_valid():
    letter = CoverLetter(
        id="cl-1",
        application_id="app-1",
        draft_version=1,
        body_markdown="Dear team, ...",
        word_count=250,
        references_company_specifics=["Series A in 2025", "shipped agent framework"],
        voice_similarity_score=0.72,
        created_at=datetime(2026, 4, 23, 12, 0, 0),
    )

    assert letter.draft_version == 1
    assert letter.voice_similarity_score == 0.72


def test_screening_answer_valid():
    answer = ScreeningAnswer(
        question="Why this company?",
        answer="Because ...",
        word_count=100,
        drafted_by=ScreeningAnswerOrigin.PROACTIVE,
    )

    assert answer.drafted_by == ScreeningAnswerOrigin.PROACTIVE
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k "cover_letter or screening_answer"
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement writing schemas**

Create `backend/src/apply/schemas/writing.py`:

```python
from datetime import datetime

from pydantic import BaseModel, Field

from apply.schemas.enums import ScreeningAnswerOrigin


class CoverLetter(BaseModel):
    id: str
    application_id: str
    draft_version: int = Field(ge=1)
    body_markdown: str
    word_count: int = Field(ge=0)
    references_company_specifics: list[str]
    voice_similarity_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime


class ScreeningAnswer(BaseModel):
    question: str
    answer: str
    word_count: int = Field(ge=0)
    drafted_by: ScreeningAnswerOrigin
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k "cover_letter or screening_answer"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/schemas/writing.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add CoverLetter and ScreeningAnswer"
```

---

### Task 12: Application + PipelineRun schemas

**Files:**
- Create: `backend/src/apply/schemas/application.py`
- Modify: `backend/tests/test_schemas.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_schemas.py`:

```python
from datetime import datetime

from apply.schemas.application import (
    Application,
    CostBreakdown,
    HitlDecision,
    Outcome,
    PipelineRun,
)
from apply.schemas.enums import (
    ApplicationStatus,
    HitlCheckpoint,
    HitlDecisionType,
    PipelineRunState,
)


def test_cost_breakdown_totals():
    breakdown = CostBreakdown(
        per_agent_usd={"intake": 0.001, "company_researcher": 0.05, "fit_analyst": 0.02},
    )
    assert abs(breakdown.total_usd - 0.071) < 1e-6


def test_pipeline_run_valid():
    run = PipelineRun(
        id="run-1",
        application_id="app-1",
        state=PipelineRunState.AWAITING_FIT_APPROVAL,
        cost_accumulated_usd=0.05,
        created_at=datetime(2026, 4, 23),
        updated_at=datetime(2026, 4, 23),
    )
    assert run.state == PipelineRunState.AWAITING_FIT_APPROVAL


def test_hitl_decision_valid():
    decision = HitlDecision(
        checkpoint=HitlCheckpoint.FIT,
        decision=HitlDecisionType.APPROVE,
        user_edits=None,
        notes=None,
        timestamp=datetime(2026, 4, 23),
    )
    assert decision.checkpoint == HitlCheckpoint.FIT
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_schemas.py -v -k "cost_breakdown or pipeline_run or hitl_decision"
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement application schemas**

Create `backend/src/apply/schemas/application.py`:

```python
from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from apply.schemas.company import CompanyResearch
from apply.schemas.enums import (
    ApplicationStatus,
    HitlCheckpoint,
    HitlDecisionType,
    PipelineRunState,
)
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing
from apply.schemas.writing import CoverLetter, ScreeningAnswer


class CostBreakdown(BaseModel):
    per_agent_usd: dict[str, float] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def total_usd(self) -> float:
        return sum(self.per_agent_usd.values())


class Outcome(BaseModel):
    status: ApplicationStatus
    response_received_at: datetime | None = None
    notes: str | None = None
    next_step: str | None = None


class HitlDecision(BaseModel):
    checkpoint: HitlCheckpoint
    decision: HitlDecisionType
    user_edits: str | None = None
    notes: str | None = None
    timestamp: datetime


class PipelineRun(BaseModel):
    id: str
    application_id: str
    state: PipelineRunState
    cost_accumulated_usd: float = 0.0
    created_at: datetime
    updated_at: datetime


class Application(BaseModel):
    id: str
    user_id: str
    job_listing: JobListing
    company_research: CompanyResearch | None = None
    fit_analysis: FitAnalysis | None = None
    cover_letter: CoverLetter | None = None
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    status: ApplicationStatus
    hitl_decisions: list[HitlDecision] = Field(default_factory=list)
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    submitted_at: datetime | None = None
    outcome: Outcome | None = None
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v
```

Expected: ALL schema tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/schemas/application.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add Application, PipelineRun, HitlDecision, CostBreakdown"
```

---

### Section B: Database (Tasks 13-16)

### Task 13: SQLAlchemy async engine + session

**Files:**
- Create: `backend/src/apply/db/__init__.py`
- Create: `backend/src/apply/db/session.py`

- [ ] **Step 1: Create db package**

Create `backend/src/apply/db/__init__.py` (empty).

- [ ] **Step 2: Implement session factory**

Create `backend/src/apply/db/session.py`:

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apply.config import get_settings


def _make_engine() -> tuple[async_sessionmaker[AsyncSession], object]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=(settings.apply_env == "dev"),
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return session_factory, engine


_session_factory, _engine = _make_engine()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


def get_engine():
    return _engine
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/db/__init__.py backend/src/apply/db/session.py
git commit -m "feat(db): add async SQLAlchemy session factory"
```

---

### Task 14: SQLAlchemy ORM models

**Files:**
- Create: `backend/src/apply/db/models.py`

- [ ] **Step 1: Implement ORM models**

Create `backend/src/apply/db/models.py`:

```python
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from apply.schemas.enums import ApplicationStatus, PipelineRunState


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    version: Mapped[int] = mapped_column()
    pdf_path: Mapped[str] = mapped_column(String)
    markdown_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    status: Mapped[ApplicationStatus] = mapped_column(String)
    job_listing_json: Mapped[dict] = mapped_column(JSON)
    company_research_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fit_analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cover_letter_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    screening_answers_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    hitl_decisions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cost_breakdown_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outcome_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list["PipelineRun"]] = relationship(back_populates="application")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    application_id: Mapped[str] = mapped_column(String, ForeignKey("applications.id"))
    state: Mapped[PipelineRunState] = mapped_column(String)
    cost_accumulated_usd: Mapped[float] = mapped_column(Float, default=0.0)
    current_artifacts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    application: Mapped["Application"] = relationship(back_populates="runs")
```

- [ ] **Step 2: Verify imports**

```bash
cd backend && uv run python -c "from apply.db.models import Base, User, Resume, Application, PipelineRun; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/db/models.py
git commit -m "feat(db): add SQLAlchemy ORM models for users, applications, runs"
```

---

### Task 15: Alembic migrations setup

**Files:**
- Create: `backend/src/apply/db/alembic.ini`
- Create: `backend/src/apply/db/migrations/env.py`
- Create: `backend/src/apply/db/migrations/script.py.mako`
- Create: `backend/src/apply/db/migrations/versions/.gitkeep`

- [ ] **Step 1: Create alembic.ini**

Create `backend/src/apply/db/alembic.ini`:

```ini
[alembic]
script_location = %(here)s/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create migrations/env.py**

Create `backend/src/apply/db/migrations/env.py`:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from apply.config import get_settings
from apply.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Create script template**

Create `backend/src/apply/db/migrations/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: Create versions directory**

```bash
mkdir -p backend/src/apply/db/migrations/versions
touch backend/src/apply/db/migrations/versions/.gitkeep
```

- [ ] **Step 5: Generate initial migration**

Make sure Postgres is running (`docker compose up -d`).

```bash
cd backend && uv run alembic -c src/apply/db/alembic.ini revision --autogenerate -m "initial schema"
```

Expected: a new file appears under `backend/src/apply/db/migrations/versions/`.

- [ ] **Step 6: Apply the migration**

```bash
cd backend && uv run alembic -c src/apply/db/alembic.ini upgrade head
```

Expected: output ends with `INFO [alembic.runtime.migration] Running upgrade  -> <rev>, initial schema`.

- [ ] **Step 7: Verify tables exist**

```bash
docker exec apply-postgres psql -U apply -d apply -c "\dt"
```

Expected: lists `users`, `resumes`, `applications`, `pipeline_runs`, `alembic_version`.

- [ ] **Step 8: Commit**

```bash
git add backend/src/apply/db/alembic.ini backend/src/apply/db/migrations/
git commit -m "feat(db): add Alembic migrations with initial schema"
```

---

### Section C: State machine (Tasks 16-17)

### Task 16: PipelineRun state machine

**Files:**
- Create: `backend/src/apply/orchestrator/__init__.py`
- Create: `backend/src/apply/orchestrator/state_machine.py`
- Create: `backend/tests/test_state_machine.py`

- [ ] **Step 1: Write failing test**

Create `backend/src/apply/orchestrator/__init__.py` (empty).

Create `backend/tests/test_state_machine.py`:

```python
import pytest

from apply.orchestrator.state_machine import (
    InvalidTransitionError,
    advance_state,
    can_transition,
    is_awaiting_user,
    next_state_after_approval,
)
from apply.schemas.enums import PipelineRunState


def test_happy_path_transitions_are_valid():
    path = [
        PipelineRunState.INTAKE_RUNNING,
        PipelineRunState.RESEARCHING,
        PipelineRunState.AWAITING_FIT_APPROVAL,
        PipelineRunState.DRAFTING,
        PipelineRunState.AWAITING_CONTENT_APPROVAL,
        PipelineRunState.FILLING_FORM,
        PipelineRunState.AWAITING_SUBMIT_APPROVAL,
        PipelineRunState.SUBMITTING,
        PipelineRunState.COMPLETED,
    ]
    for a, b in zip(path, path[1:]):
        assert can_transition(a, b), f"{a} -> {b} should be allowed"


def test_invalid_transition_rejected():
    assert not can_transition(
        PipelineRunState.INTAKE_RUNNING, PipelineRunState.COMPLETED
    )


def test_advance_raises_on_invalid():
    with pytest.raises(InvalidTransitionError):
        advance_state(PipelineRunState.INTAKE_RUNNING, PipelineRunState.COMPLETED)


def test_is_awaiting_user_detects_checkpoints():
    assert is_awaiting_user(PipelineRunState.AWAITING_FIT_APPROVAL)
    assert is_awaiting_user(PipelineRunState.AWAITING_CONTENT_APPROVAL)
    assert is_awaiting_user(PipelineRunState.AWAITING_SUBMIT_APPROVAL)
    assert not is_awaiting_user(PipelineRunState.RESEARCHING)
    assert not is_awaiting_user(PipelineRunState.COMPLETED)


def test_next_state_after_approval():
    assert (
        next_state_after_approval(PipelineRunState.AWAITING_FIT_APPROVAL)
        == PipelineRunState.DRAFTING
    )
    assert (
        next_state_after_approval(PipelineRunState.AWAITING_CONTENT_APPROVAL)
        == PipelineRunState.FILLING_FORM
    )
    assert (
        next_state_after_approval(PipelineRunState.AWAITING_SUBMIT_APPROVAL)
        == PipelineRunState.SUBMITTING
    )


def test_abandoned_is_terminal():
    # ABANDONED should not transition further
    assert not can_transition(
        PipelineRunState.ABANDONED, PipelineRunState.COMPLETED
    )


def test_any_state_can_transition_to_errored():
    # ERRORED is a permissible sink from any active state
    assert can_transition(PipelineRunState.INTAKE_RUNNING, PipelineRunState.ERRORED)
    assert can_transition(PipelineRunState.DRAFTING, PipelineRunState.ERRORED)
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_state_machine.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement state machine**

Create `backend/src/apply/orchestrator/state_machine.py`:

```python
from apply.schemas.enums import PipelineRunState

S = PipelineRunState

# Allowed forward transitions. Keys are sources; values are allowed targets.
_ALLOWED: dict[PipelineRunState, set[PipelineRunState]] = {
    S.INTAKE_RUNNING: {S.RESEARCHING, S.ERRORED},
    S.RESEARCHING: {S.AWAITING_FIT_APPROVAL, S.ERRORED},
    S.AWAITING_FIT_APPROVAL: {S.DRAFTING, S.ABANDONED, S.ERRORED},
    S.DRAFTING: {S.AWAITING_CONTENT_APPROVAL, S.ERRORED},
    S.AWAITING_CONTENT_APPROVAL: {S.DRAFTING, S.FILLING_FORM, S.ABANDONED, S.ERRORED},
    S.FILLING_FORM: {S.AWAITING_SUBMIT_APPROVAL, S.ERRORED},
    S.AWAITING_SUBMIT_APPROVAL: {S.SUBMITTING, S.ABANDONED, S.ERRORED},
    S.SUBMITTING: {S.COMPLETED, S.ERRORED},
    S.COMPLETED: set(),
    S.ABANDONED: set(),
    S.ERRORED: set(),
}

_AWAITING_USER: set[PipelineRunState] = {
    S.AWAITING_FIT_APPROVAL,
    S.AWAITING_CONTENT_APPROVAL,
    S.AWAITING_SUBMIT_APPROVAL,
}

_APPROVAL_NEXT: dict[PipelineRunState, PipelineRunState] = {
    S.AWAITING_FIT_APPROVAL: S.DRAFTING,
    S.AWAITING_CONTENT_APPROVAL: S.FILLING_FORM,
    S.AWAITING_SUBMIT_APPROVAL: S.SUBMITTING,
}


class InvalidTransitionError(ValueError):
    pass


def can_transition(src: PipelineRunState, dst: PipelineRunState) -> bool:
    return dst in _ALLOWED.get(src, set())


def advance_state(src: PipelineRunState, dst: PipelineRunState) -> PipelineRunState:
    if not can_transition(src, dst):
        raise InvalidTransitionError(f"{src} -> {dst} is not allowed")
    return dst


def is_awaiting_user(state: PipelineRunState) -> bool:
    return state in _AWAITING_USER


def next_state_after_approval(state: PipelineRunState) -> PipelineRunState:
    if state not in _APPROVAL_NEXT:
        raise InvalidTransitionError(f"{state} is not an approval checkpoint")
    return _APPROVAL_NEXT[state]
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_state_machine.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/orchestrator/ backend/tests/test_state_machine.py
git commit -m "feat(orchestrator): add pipeline state machine with allowed transitions"
```

---

### Section D: Stub agents (Tasks 17-23)

### Task 17: Intake agent stub

**Files:**
- Create: `backend/src/apply/agents/__init__.py`
- Create: `backend/src/apply/agents/intake.py`
- Create: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Create agents package**

Create `backend/src/apply/agents/__init__.py` (empty).

- [ ] **Step 2: Write failing test**

Create `backend/tests/test_agents_stub.py`:

```python
import pytest

from apply.agents.intake import intake_stub


@pytest.mark.asyncio
async def test_intake_stub_returns_valid_job_listing():
    listing = await intake_stub(url="https://workatastartup.com/jobs/123")

    assert listing.company_name
    assert listing.role_title
    assert str(listing.url) == "https://workatastartup.com/jobs/123"
    assert listing.requirements  # non-empty
```

- [ ] **Step 3: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k intake
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement intake stub**

Create `backend/src/apply/agents/intake.py`:

```python
import uuid

from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing


async def intake_stub(url: str) -> JobListing:
    """Phase 1 stub: returns a fixed fake JobListing regardless of URL."""
    return JobListing(
        id=f"job-{uuid.uuid4().hex[:8]}",
        source=JobSource.YC_WAAS,
        url=url,  # type: ignore[arg-type]
        application_url=url,  # type: ignore[arg-type]
        company_name="Acme AI",
        role_title="Founding Engineer",
        location="San Francisco, CA",
        remote_type=RemoteType.HYBRID,
        description_markdown=(
            "We're building agents that talk to enterprise software. "
            "Looking for someone who loves Python, multi-agent systems, "
            "and shipping fast."
        ),
        requirements=[
            "5+ years Python",
            "Experience with LLMs and agent frameworks",
            "Comfort with async systems",
        ],
        nice_to_haves=[
            "Published open-source work on agents",
            "Experience with MCP or Claude Agent SDK",
        ],
        compensation_range="$180k-$240k + equity",
        raw_html_path="/tmp/apply/stub-jd.html",
    )
```

- [ ] **Step 5: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k intake
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/agents/ backend/tests/test_agents_stub.py
git commit -m "feat(agents): add intake stub returning fixed JobListing"
```

---

### Task 18: Company Researcher stub

**Files:**
- Create: `backend/src/apply/agents/company_researcher.py`
- Modify: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_agents_stub.py`:

```python
from apply.agents.company_researcher import company_researcher_stub


@pytest.mark.asyncio
async def test_company_researcher_stub_returns_valid_research():
    research = await company_researcher_stub(company_name="Acme AI")

    assert research.company_name == "Acme AI"
    assert research.founders  # non-empty
    assert research.recent_news  # non-empty
    assert 0.0 <= research.signal_score <= 1.0
    assert research.sources
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k company_researcher
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement stub**

Create `backend/src/apply/agents/company_researcher.py`:

```python
from apply.schemas.company import (
    BlogPost,
    CompanyResearch,
    Founder,
    NewsItem,
    Round,
    Source,
)


async def company_researcher_stub(company_name: str) -> CompanyResearch:
    """Phase 1 stub: returns fixed fake research."""
    return CompanyResearch(
        company_name=company_name,
        funding_stage="Series A",
        last_round=Round(stage="Series A", amount_usd=12_000_000, date_iso="2025-11-15"),
        team_size="20-50",
        founders=[
            Founder(
                name="Jordan Smith",
                background="ex-Anthropic ML engineer, Stanford CS",
                linkedin_url="https://www.linkedin.com/in/jordan-smith",
            ),
            Founder(
                name="Priya Patel",
                background="ex-Google product lead",
                linkedin_url="https://www.linkedin.com/in/priya-patel",
            ),
        ],
        recent_news=[
            NewsItem(
                title=f"{company_name} raises $12M Series A",
                url="https://techcrunch.com/acme-series-a",
                date_iso="2025-11-15",
                summary=f"{company_name} announced its Series A round led by Foundry.",
            ),
        ],
        recent_blog_posts=[
            BlogPost(
                title="How we think about building agent products",
                url="https://acme.ai/blog/agent-thinking",
                summary="A philosophy piece on long-running agents.",
            ),
        ],
        tech_stack_hints=["Python", "LangGraph", "Postgres", "FastAPI"],
        signal_score=0.78,
        sources=[
            Source(
                url="https://acme.ai",
                title="Acme homepage",
                trust_score=0.9,
            ),
            Source(
                url="https://techcrunch.com/acme-series-a",
                title="TechCrunch Series A announcement",
                trust_score=0.85,
            ),
        ],
    )
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k company_researcher
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/company_researcher.py backend/tests/test_agents_stub.py
git commit -m "feat(agents): add company researcher stub"
```

---

### Task 19: Fit Analyst stub

**Files:**
- Create: `backend/src/apply/agents/fit_analyst.py`
- Modify: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_agents_stub.py`:

```python
from apply.agents.fit_analyst import fit_analyst_stub
from apply.schemas.enums import FitVerdict, RecommendedAction


@pytest.mark.asyncio
async def test_fit_analyst_stub_returns_valid_analysis():
    analysis = await fit_analyst_stub(
        job_listing_id="job-x",
        resume_markdown="Senior Python engineer",
    )

    assert 0 <= analysis.overall_score <= 100
    assert isinstance(analysis.verdict, FitVerdict)
    assert analysis.recommended_action in [
        RecommendedAction.PROCEED,
        RecommendedAction.PROCEED_WITH_CAUTION,
        RecommendedAction.SKIP,
    ]
    assert analysis.reasoning
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k fit_analyst
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement stub**

Create `backend/src/apply/agents/fit_analyst.py`:

```python
from apply.schemas.enums import FitStrength, FitVerdict, RecommendedAction
from apply.schemas.fit import FitAnalysis, FitPoint


async def fit_analyst_stub(job_listing_id: str, resume_markdown: str) -> FitAnalysis:
    """Phase 1 stub: returns a hand-crafted MODERATE fit."""
    return FitAnalysis(
        overall_score=72,
        verdict=FitVerdict.MODERATE,
        matches=[
            FitPoint(
                dimension="Python proficiency",
                evidence_resume="5 years of Python as primary language",
                evidence_jd="5+ years Python",
                strength=FitStrength.STRONG,
            ),
            FitPoint(
                dimension="Async systems",
                evidence_resume="Built async data pipelines",
                evidence_jd="Comfort with async systems",
                strength=FitStrength.STRONG,
            ),
        ],
        stretches=[
            FitPoint(
                dimension="LLM agent frameworks",
                evidence_resume="Shipped one RAG prototype",
                evidence_jd="Experience with LLMs and agent frameworks",
                strength=FitStrength.MODERATE,
            ),
        ],
        gaps=[
            FitPoint(
                dimension="MCP / Claude Agent SDK",
                evidence_resume=None,
                evidence_jd="Experience with MCP or Claude Agent SDK",
                strength=FitStrength.WEAK,
            ),
        ],
        reasoning=(
            "Candidate has strong Python + async foundations. Weak on the "
            "specific agent-SDK requirements, but the project being built "
            "would directly address this gap — worth proceeding with a "
            "cover letter that frames the gap as the motivation."
        ),
        recommended_action=RecommendedAction.PROCEED,
    )
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k fit_analyst
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/fit_analyst.py backend/tests/test_agents_stub.py
git commit -m "feat(agents): add fit analyst stub"
```

---

### Task 20: Cover Letter Writer stub

**Files:**
- Create: `backend/src/apply/agents/cover_letter_writer.py`
- Modify: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_agents_stub.py`:

```python
from apply.agents.cover_letter_writer import cover_letter_writer_stub


@pytest.mark.asyncio
async def test_cover_letter_writer_stub():
    letter = await cover_letter_writer_stub(
        application_id="app-1",
        company_name="Acme AI",
    )

    assert letter.application_id == "app-1"
    assert letter.draft_version == 1
    assert letter.body_markdown
    assert letter.word_count > 0
    assert len(letter.references_company_specifics) > 0
    assert 0.0 <= letter.voice_similarity_score <= 1.0
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k cover_letter_writer
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement stub**

Create `backend/src/apply/agents/cover_letter_writer.py`:

```python
import uuid
from datetime import datetime

from apply.schemas.writing import CoverLetter


async def cover_letter_writer_stub(application_id: str, company_name: str) -> CoverLetter:
    """Phase 1 stub: returns a believable fake cover letter."""
    body = (
        f"Dear {company_name} team,\n\n"
        f"I read your recent Series A announcement and the blog post on "
        f"long-running agents with a lot of interest. The framing of "
        f"treating agents as products rather than features resonates with "
        f"work I've been doing independently.\n\n"
        f"Over the last five years I've been a Python engineer focused on "
        f"async systems and, more recently, multi-agent orchestration. "
        f"I'm currently building an applications copilot that uses Pydantic "
        f"AI and Claude Agent SDK — the same stack your job description "
        f"implies. I'd love to talk.\n\n"
        f"Thanks for your time,\nSanyam"
    )
    return CoverLetter(
        id=f"cl-{uuid.uuid4().hex[:8]}",
        application_id=application_id,
        draft_version=1,
        body_markdown=body,
        word_count=len(body.split()),
        references_company_specifics=[
            "Series A announcement",
            "long-running agents blog post",
            "agent-product framing",
        ],
        voice_similarity_score=0.71,
        created_at=datetime.utcnow(),
    )
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k cover_letter_writer
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/cover_letter_writer.py backend/tests/test_agents_stub.py
git commit -m "feat(agents): add cover letter writer stub"
```

---

### Task 21: Screening Question Answerer stub

**Files:**
- Create: `backend/src/apply/agents/screening_answerer.py`
- Modify: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_agents_stub.py`:

```python
from apply.agents.screening_answerer import screening_answerer_stub
from apply.schemas.enums import ScreeningAnswerOrigin


@pytest.mark.asyncio
async def test_screening_answerer_stub():
    answer = await screening_answerer_stub(
        question="Why do you want to work at Acme AI?",
        origin=ScreeningAnswerOrigin.PROACTIVE,
    )

    assert answer.question == "Why do you want to work at Acme AI?"
    assert answer.answer
    assert answer.word_count > 0
    assert answer.drafted_by == ScreeningAnswerOrigin.PROACTIVE
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k screening_answerer
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement stub**

Create `backend/src/apply/agents/screening_answerer.py`:

```python
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.writing import ScreeningAnswer


async def screening_answerer_stub(
    question: str,
    origin: ScreeningAnswerOrigin,
) -> ScreeningAnswer:
    """Phase 1 stub: returns a generic-but-plausible answer."""
    answer = (
        "I'm drawn to this role because it sits at the intersection of "
        "applied research and shipping product — both of which I've been "
        "practicing in my recent work on multi-agent systems."
    )
    return ScreeningAnswer(
        question=question,
        answer=answer,
        word_count=len(answer.split()),
        drafted_by=origin,
    )
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k screening_answerer
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/screening_answerer.py backend/tests/test_agents_stub.py
git commit -m "feat(agents): add screening question answerer stub"
```

---

### Task 22: Form-Fill agent stub

**Files:**
- Create: `backend/src/apply/agents/form_fill.py`
- Modify: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_agents_stub.py`:

```python
from apply.agents.form_fill import FormFillResult, form_fill_stub


@pytest.mark.asyncio
async def test_form_fill_stub():
    result = await form_fill_stub(
        application_url="https://workatastartup.com/jobs/123/apply",
        cover_letter_body="Dear team, ...",
    )

    assert isinstance(result, FormFillResult)
    assert result.fields_filled  # non-empty
    assert result.unknown_fields is not None  # may be empty list
    assert result.screenshot_path
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k form_fill
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement stub**

Create `backend/src/apply/agents/form_fill.py`:

```python
from pydantic import BaseModel


class FilledField(BaseModel):
    name: str
    value: str
    field_type: str  # "text" | "textarea" | "file" | "select"


class UnknownField(BaseModel):
    name: str
    field_type: str
    best_guess: str | None = None
    reason_flagged: str


class FormFillResult(BaseModel):
    fields_filled: list[FilledField]
    unknown_fields: list[UnknownField]
    screenshot_path: str
    submission_url: str | None = None
    success: bool


async def form_fill_stub(
    application_url: str,
    cover_letter_body: str,
) -> FormFillResult:
    """Phase 1 stub: pretends to fill a YC WaaS application form."""
    return FormFillResult(
        fields_filled=[
            FilledField(name="full_name", value="Sanyam Upadhyay", field_type="text"),
            FilledField(name="email", value="you@example.com", field_type="text"),
            FilledField(name="linkedin", value="https://linkedin.com/in/...", field_type="text"),
            FilledField(name="resume", value="resume-v3.pdf", field_type="file"),
            FilledField(name="cover_letter", value=cover_letter_body, field_type="textarea"),
        ],
        unknown_fields=[
            UnknownField(
                name="salary_expectation",
                field_type="text",
                best_guess="$180k-$220k",
                reason_flagged="salary range varies by role seniority",
            ),
        ],
        screenshot_path="/tmp/apply/stub-screenshot.png",
        submission_url=None,  # not yet submitted
        success=True,
    )
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k form_fill
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/form_fill.py backend/tests/test_agents_stub.py
git commit -m "feat(agents): add form-fill stub"
```

---

### Task 23: Memory Curator stub

**Files:**
- Create: `backend/src/apply/agents/memory_curator.py`
- Modify: `backend/tests/test_agents_stub.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_agents_stub.py`:

```python
from apply.agents.memory_curator import memory_curator_stub


@pytest.mark.asyncio
async def test_memory_curator_stub():
    result = await memory_curator_stub(application_id="app-1")

    assert result["application_id"] == "app-1"
    assert result["indexed"] is True
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k memory_curator
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement stub**

Create `backend/src/apply/agents/memory_curator.py`:

```python
async def memory_curator_stub(application_id: str) -> dict:
    """Phase 1 stub: pretends to index artifacts."""
    return {"application_id": application_id, "indexed": True}
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_agents_stub.py -v -k memory_curator
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/memory_curator.py backend/tests/test_agents_stub.py
git commit -m "feat(agents): add memory curator stub"
```

---

### Section E: Orchestrator (Tasks 24-26)

### Task 24: In-memory pipeline runner

**Files:**
- Create: `backend/src/apply/orchestrator/graph.py`
- Create: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_orchestrator.py`:

```python
import pytest

from apply.orchestrator.graph import (
    PipelineContext,
    run_to_next_checkpoint,
)
from apply.schemas.enums import PipelineRunState


@pytest.mark.asyncio
async def test_run_from_start_stops_at_fit_checkpoint():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.INTAKE_RUNNING,
    )

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.AWAITING_FIT_APPROVAL
    assert ctx.artifacts.get("job_listing") is not None
    assert ctx.artifacts.get("company_research") is not None
    assert ctx.artifacts.get("fit_analysis") is not None


@pytest.mark.asyncio
async def test_run_from_fit_approval_stops_at_content_checkpoint():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.DRAFTING,
    )

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.AWAITING_CONTENT_APPROVAL
    assert ctx.artifacts.get("cover_letter") is not None


@pytest.mark.asyncio
async def test_run_from_content_approval_stops_at_submit_checkpoint():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.FILLING_FORM,
    )
    # Seed the upstream artifacts needed by form_fill
    ctx.artifacts["cover_letter"] = {"body_markdown": "Dear team, ..."}

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.AWAITING_SUBMIT_APPROVAL
    assert ctx.artifacts.get("form_fill_result") is not None


@pytest.mark.asyncio
async def test_run_from_submitting_reaches_completed():
    ctx = PipelineContext(
        run_id="run-1",
        application_id="app-1",
        jd_url="https://workatastartup.com/jobs/1",
        state=PipelineRunState.SUBMITTING,
    )

    await run_to_next_checkpoint(ctx)

    assert ctx.state == PipelineRunState.COMPLETED
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_orchestrator.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement orchestrator**

Create `backend/src/apply/orchestrator/graph.py`:

```python
from dataclasses import dataclass, field
from typing import Any

from apply.agents.company_researcher import company_researcher_stub
from apply.agents.cover_letter_writer import cover_letter_writer_stub
from apply.agents.fit_analyst import fit_analyst_stub
from apply.agents.form_fill import form_fill_stub
from apply.agents.intake import intake_stub
from apply.agents.memory_curator import memory_curator_stub
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


async def run_to_next_checkpoint(ctx: PipelineContext) -> None:
    """Advance the pipeline until the next HITL gate or a terminal state.

    Each agent writes its artifact to `ctx.artifacts` and the state machine
    is advanced between agents. On reaching an AWAITING_* state or a
    terminal state, this function returns; the caller persists and waits.
    """
    while True:
        if ctx.state == PipelineRunState.INTAKE_RUNNING:
            listing = await intake_stub(url=ctx.jd_url)
            ctx.artifacts["job_listing"] = listing.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.001
            ctx.state = advance_state(ctx.state, PipelineRunState.RESEARCHING)
            continue

        if ctx.state == PipelineRunState.RESEARCHING:
            listing = ctx.artifacts["job_listing"]
            research = await company_researcher_stub(company_name=listing["company_name"])
            fit = await fit_analyst_stub(
                job_listing_id=listing["id"],
                resume_markdown="[stub resume]",
            )
            ctx.artifacts["company_research"] = research.model_dump(mode="json")
            ctx.artifacts["fit_analysis"] = fit.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.05
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_FIT_APPROVAL)
            return  # HITL #1

        if ctx.state == PipelineRunState.DRAFTING:
            listing = ctx.artifacts["job_listing"]
            letter = await cover_letter_writer_stub(
                application_id=ctx.application_id,
                company_name=listing["company_name"],
            )
            ctx.artifacts["cover_letter"] = letter.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.03
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_CONTENT_APPROVAL)
            return  # HITL #2

        if ctx.state == PipelineRunState.FILLING_FORM:
            listing = ctx.artifacts.get("job_listing", {})
            application_url = listing.get("application_url", ctx.jd_url)
            letter = ctx.artifacts.get("cover_letter", {})
            result = await form_fill_stub(
                application_url=application_url,
                cover_letter_body=letter.get("body_markdown", ""),
            )
            ctx.artifacts["form_fill_result"] = result.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.08
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_SUBMIT_APPROVAL)
            return  # HITL #3

        if ctx.state == PipelineRunState.SUBMITTING:
            # Stub: pretend we submitted successfully.
            ctx.artifacts["submission_confirmation"] = {"url": "https://stub.example/confirm"}
            await memory_curator_stub(application_id=ctx.application_id)
            ctx.state = advance_state(ctx.state, PipelineRunState.COMPLETED)
            return  # terminal

        # Any other state: no-op (caller shouldn't drive us here)
        return
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_orchestrator.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py backend/tests/test_orchestrator.py
git commit -m "feat(orchestrator): add pipeline runner with HITL checkpoint pauses"
```

---

### Task 25: Run repository (persistence adapter)

**Files:**
- Create: `backend/src/apply/orchestrator/run_repository.py`
- Create: `backend/tests/conftest.py`
- Modify: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Create test fixtures for a clean DB per test**

Create `backend/tests/conftest.py`:

```python
import asyncio
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apply.config import get_settings
from apply.db.models import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    # Ensure a clean schema for this test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()
```

- [ ] **Step 2: Write failing test**

Append to `backend/tests/test_orchestrator.py`:

```python
from datetime import datetime

from apply.orchestrator.run_repository import RunRepository
from apply.schemas.enums import ApplicationStatus, PipelineRunState


@pytest.mark.asyncio
async def test_repository_persists_and_loads_run(db_session):
    repo = RunRepository(db_session)

    # First: need an application to attach the run to
    app_id = await repo.create_application_row(
        user_id="user-1",
        job_listing_json={"id": "job-1", "company_name": "Acme"},
        status=ApplicationStatus.DRAFTING,
    )

    run_id = await repo.create_run(
        application_id=app_id,
        initial_state=PipelineRunState.INTAKE_RUNNING,
    )

    loaded = await repo.load_run(run_id)
    assert loaded.state == PipelineRunState.INTAKE_RUNNING
    assert loaded.application_id == app_id

    await repo.update_run(
        run_id=run_id,
        state=PipelineRunState.AWAITING_FIT_APPROVAL,
        cost_accumulated_usd=0.05,
        artifacts={"fit_analysis": {"overall_score": 72}},
    )

    reloaded = await repo.load_run(run_id)
    assert reloaded.state == PipelineRunState.AWAITING_FIT_APPROVAL
    assert reloaded.cost_accumulated_usd == 0.05
    assert reloaded.artifacts["fit_analysis"]["overall_score"] == 72
```

- [ ] **Step 3: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_orchestrator.py::test_repository_persists_and_loads_run -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement repository**

Create `backend/src/apply/orchestrator/run_repository.py`:

```python
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.db.models import Application as ApplicationRow
from apply.db.models import PipelineRun as PipelineRunRow
from apply.schemas.enums import ApplicationStatus, PipelineRunState


@dataclass
class LoadedRun:
    id: str
    application_id: str
    state: PipelineRunState
    cost_accumulated_usd: float
    artifacts: dict[str, Any]


class RunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_application_row(
        self,
        user_id: str,
        job_listing_json: dict[str, Any],
        status: ApplicationStatus,
    ) -> str:
        app_id = f"app-{uuid.uuid4().hex[:8]}"
        row = ApplicationRow(
            id=app_id,
            user_id=user_id,
            status=status,
            job_listing_json=job_listing_json,
        )
        self.session.add(row)
        await self.session.flush()
        return app_id

    async def create_run(
        self,
        application_id: str,
        initial_state: PipelineRunState,
    ) -> str:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        row = PipelineRunRow(
            id=run_id,
            application_id=application_id,
            state=initial_state,
            cost_accumulated_usd=0.0,
            current_artifacts_json={},
        )
        self.session.add(row)
        await self.session.commit()
        return run_id

    async def load_run(self, run_id: str) -> LoadedRun:
        stmt = select(PipelineRunRow).where(PipelineRunRow.id == run_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        return LoadedRun(
            id=row.id,
            application_id=row.application_id,
            state=PipelineRunState(row.state),
            cost_accumulated_usd=row.cost_accumulated_usd,
            artifacts=row.current_artifacts_json or {},
        )

    async def update_run(
        self,
        run_id: str,
        state: PipelineRunState,
        cost_accumulated_usd: float,
        artifacts: dict[str, Any],
    ) -> None:
        stmt = select(PipelineRunRow).where(PipelineRunRow.id == run_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.state = state
        row.cost_accumulated_usd = cost_accumulated_usd
        row.current_artifacts_json = artifacts
        await self.session.commit()
```

- [ ] **Step 5: Run test**

```bash
cd backend && uv run pytest tests/test_orchestrator.py::test_repository_persists_and_loads_run -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/orchestrator/run_repository.py backend/tests/conftest.py backend/tests/test_orchestrator.py
git commit -m "feat(orchestrator): add run repository for state persistence"
```

---

### Task 26: Event bus for SSE streaming

**Files:**
- Create: `backend/src/apply/orchestrator/events.py`
- Modify: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_orchestrator.py`:

```python
import asyncio

from apply.orchestrator.events import EventBus


@pytest.mark.asyncio
async def test_event_bus_delivers_events_to_subscribers():
    bus = EventBus()
    received: list[dict] = []

    async def collect():
        async for ev in bus.subscribe("run-1"):
            received.append(ev)
            if ev.get("final"):
                return

    consumer = asyncio.create_task(collect())
    await asyncio.sleep(0)  # let subscriber start

    await bus.publish("run-1", {"type": "agent_start", "name": "intake"})
    await bus.publish("run-1", {"type": "agent_done", "name": "intake"})
    await bus.publish("run-1", {"type": "checkpoint_reached", "final": True})

    await asyncio.wait_for(consumer, timeout=1.0)

    assert len(received) == 3
    assert received[0]["name"] == "intake"
    assert received[-1]["final"] is True


@pytest.mark.asyncio
async def test_event_bus_scopes_by_run_id():
    bus = EventBus()
    received_a: list[dict] = []

    async def collect():
        async for ev in bus.subscribe("run-A"):
            received_a.append(ev)
            if ev.get("final"):
                return

    consumer = asyncio.create_task(collect())
    await asyncio.sleep(0)

    await bus.publish("run-B", {"type": "noise"})  # should NOT be delivered
    await bus.publish("run-A", {"type": "hit", "final": True})

    await asyncio.wait_for(consumer, timeout=1.0)

    assert len(received_a) == 1
    assert received_a[0]["type"] == "hit"
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_orchestrator.py -v -k event_bus
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement event bus**

Create `backend/src/apply/orchestrator/events.py`:

```python
import asyncio
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    """In-memory pub/sub keyed by run_id. V1 only (single-process).

    V2+ can swap for Redis pub/sub without changing this interface.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(run_id, []))
        for q in queues:
            await q.put(event)

    async def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._subscribers.setdefault(run_id, []).append(queue)
        try:
            while True:
                ev = await queue.get()
                yield ev
        finally:
            async with self._lock:
                subs = self._subscribers.get(run_id, [])
                if queue in subs:
                    subs.remove(queue)
                if not subs:
                    self._subscribers.pop(run_id, None)


# Singleton instance used by app.
_bus = EventBus()


def get_event_bus() -> EventBus:
    return _bus
```

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_orchestrator.py -v -k event_bus
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/orchestrator/events.py backend/tests/test_orchestrator.py
git commit -m "feat(orchestrator): add in-memory event bus for SSE streaming"
```

---

### Section F: API (Tasks 27-31)

### Task 27: POST /applications starts a run

**Files:**
- Create: `backend/src/apply/api/routes_applications.py`
- Modify: `backend/src/apply/api/main.py`
- Create: `backend/tests/test_api_applications.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_api_applications.py`:

```python
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
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v
```

Expected: FAIL with 404 or AttributeError (route doesn't exist).

- [ ] **Step 3: Implement route**

Create `backend/src/apply/api/routes_applications.py`:

```python
import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from apply.agents.intake import intake_stub
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


@router.post("", response_model=CreateApplicationResponse, status_code=201)
async def create_application(
    req: CreateApplicationRequest,
    session: AsyncSession = Depends(get_session),
) -> CreateApplicationResponse:
    # Preview-intake so we have a JobListing to attach to the row.
    listing = await intake_stub(url=str(req.jd_url))

    repo = RunRepository(session)
    app_id = await repo.create_application_row(
        user_id="user-local",
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
    )
    ctx.artifacts["job_listing"] = listing.model_dump(mode="json")

    # Kick off background pipeline. Do NOT await — return response to client.
    asyncio.create_task(_drive_pipeline(run_id, ctx, repo_session=session))

    return CreateApplicationResponse(
        run_id=run_id,
        application_id=app_id,
        state=ctx.state.value,
    )


async def _drive_pipeline(run_id: str, ctx: PipelineContext, repo_session: AsyncSession) -> None:
    """Run pipeline to next HITL gate in the background and persist.

    Emits SSE events for the frontend to consume.
    """
    bus = get_event_bus()
    await bus.publish(run_id, {"type": "run_started", "state": ctx.state.value})
    try:
        await run_to_next_checkpoint(ctx)
    except Exception as e:
        await bus.publish(run_id, {"type": "error", "message": str(e)})
        return
    # Persist new state
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

- [ ] **Step 4: Register route in `main.py`**

Modify `backend/src/apply/api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apply.api.routes_applications import router as applications_router
from apply.api.routes_health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Apply", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(applications_router)

    return app


app = create_app()
```

- [ ] **Step 5: Run test**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/api/routes_applications.py backend/src/apply/api/main.py backend/tests/test_api_applications.py
git commit -m "feat(api): POST /applications starts a pipeline run"
```

---

### Task 28: GET /runs/{id} returns current state

**Files:**
- Create: `backend/src/apply/api/routes_runs.py`
- Modify: `backend/src/apply/api/main.py`
- Modify: `backend/tests/test_api_applications.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_api_applications.py`:

```python
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
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_api_applications.py::test_get_run_returns_state_and_artifacts -v
```

Expected: FAIL (404).

- [ ] **Step 3: Implement route**

Create `backend/src/apply/api/routes_runs.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apply.db.session import get_session
from apply.orchestrator.run_repository import RunRepository

router = APIRouter(prefix="/runs", tags=["runs"])


class RunResponse(BaseModel):
    run_id: str
    application_id: str
    state: str
    cost_accumulated_usd: float
    artifacts: dict


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> RunResponse:
    repo = RunRepository(session)
    try:
        run = await repo.load_run(run_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"run not found: {e}") from e

    return RunResponse(
        run_id=run.id,
        application_id=run.application_id,
        state=run.state.value,
        cost_accumulated_usd=run.cost_accumulated_usd,
        artifacts=run.artifacts,
    )
```

- [ ] **Step 4: Register route in `main.py`**

Modify `backend/src/apply/api/main.py` to add the runs router:

```python
from apply.api.routes_runs import router as runs_router
# ...
app.include_router(runs_router)
```

Full updated file:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apply.api.routes_applications import router as applications_router
from apply.api.routes_health import router as health_router
from apply.api.routes_runs import router as runs_router


def create_app() -> FastAPI:
    app = FastAPI(title="Apply", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(applications_router)
    app.include_router(runs_router)

    return app


app = create_app()
```

- [ ] **Step 5: Run test**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/api/routes_runs.py backend/src/apply/api/main.py backend/tests/test_api_applications.py
git commit -m "feat(api): GET /runs/{id} returns state and artifacts"
```

---

### Task 29: SSE /runs/{id}/events streaming

**Files:**
- Create: `backend/src/apply/api/sse.py`
- Modify: `backend/src/apply/api/routes_runs.py`
- Create: `backend/tests/test_api_sse.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_api_sse.py`:

```python
import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from apply.api.main import create_app
from apply.orchestrator.events import get_event_bus


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_sse_stream_delivers_events(app):
    transport = ASGITransport(app=app)
    bus = get_event_bus()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async def publish_later():
            await asyncio.sleep(0.05)
            await bus.publish("test-run", {"type": "agent_start", "name": "intake"})
            await asyncio.sleep(0.05)
            await bus.publish("test-run", {"type": "checkpoint_reached", "final": True})

        publisher = asyncio.create_task(publish_later())

        collected: list[str] = []
        async with client.stream("GET", "/runs/test-run/events") as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    collected.append(line)
                if "final" in line:
                    break

        await publisher

    assert len(collected) >= 2
    assert any("intake" in l for l in collected)
    assert any("checkpoint_reached" in l for l in collected)
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_api_sse.py -v
```

Expected: FAIL (404 on SSE route).

- [ ] **Step 3: Implement SSE helper**

Create `backend/src/apply/api/sse.py`:

```python
import json
from collections.abc import AsyncIterator

from apply.orchestrator.events import get_event_bus


async def sse_stream(run_id: str) -> AsyncIterator[dict[str, str]]:
    """Produce SSE-formatted events for a run."""
    bus = get_event_bus()
    async for event in bus.subscribe(run_id):
        yield {"event": event.get("type", "message"), "data": json.dumps(event)}
```

- [ ] **Step 4: Add SSE endpoint**

Modify `backend/src/apply/api/routes_runs.py` to add the streaming endpoint:

```python
from sse_starlette.sse import EventSourceResponse

from apply.api.sse import sse_stream


@router.get("/{run_id}/events")
async def run_events(run_id: str) -> EventSourceResponse:
    return EventSourceResponse(sse_stream(run_id))
```

Full updated file:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from apply.api.sse import sse_stream
from apply.db.session import get_session
from apply.orchestrator.run_repository import RunRepository

router = APIRouter(prefix="/runs", tags=["runs"])


class RunResponse(BaseModel):
    run_id: str
    application_id: str
    state: str
    cost_accumulated_usd: float
    artifacts: dict


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> RunResponse:
    repo = RunRepository(session)
    try:
        run = await repo.load_run(run_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"run not found: {e}") from e

    return RunResponse(
        run_id=run.id,
        application_id=run.application_id,
        state=run.state.value,
        cost_accumulated_usd=run.cost_accumulated_usd,
        artifacts=run.artifacts,
    )


@router.get("/{run_id}/events")
async def run_events(run_id: str) -> EventSourceResponse:
    return EventSourceResponse(sse_stream(run_id))
```

- [ ] **Step 5: Run test**

```bash
cd backend && uv run pytest tests/test_api_sse.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/api/sse.py backend/src/apply/api/routes_runs.py backend/tests/test_api_sse.py
git commit -m "feat(api): SSE stream at /runs/{id}/events"
```

---

### Task 30: POST /runs/{id}/approve advances state

**Files:**
- Modify: `backend/src/apply/api/routes_runs.py`
- Modify: `backend/tests/test_api_applications.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_api_applications.py`:

```python
@pytest.mark.asyncio
async def test_approve_advances_state(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/applications",
            json={"jd_url": "https://workatastartup.com/jobs/789"},
        )
        run_id = create.json()["run_id"]

        # Wait for pipeline to reach HITL #1
        for _ in range(20):
            await asyncio.sleep(0.05)
            check = await client.get(f"/runs/{run_id}")
            if check.json()["state"] == "AWAITING_FIT_APPROVAL":
                break
        else:
            pytest.fail("pipeline did not reach AWAITING_FIT_APPROVAL")

        approve = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "FIT", "decision": "APPROVE"},
        )
        assert approve.status_code == 200

        # Wait for pipeline to reach HITL #2
        for _ in range(20):
            await asyncio.sleep(0.05)
            check = await client.get(f"/runs/{run_id}")
            if check.json()["state"] == "AWAITING_CONTENT_APPROVAL":
                break
        else:
            pytest.fail("pipeline did not reach AWAITING_CONTENT_APPROVAL")
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/test_api_applications.py::test_approve_advances_state -v
```

Expected: FAIL (404 on approve route).

- [ ] **Step 3: Implement approve endpoint**

Modify `backend/src/apply/api/routes_runs.py` — add import and endpoint:

```python
import asyncio

from apply.orchestrator.events import get_event_bus
from apply.orchestrator.graph import PipelineContext, run_to_next_checkpoint
from apply.orchestrator.state_machine import (
    InvalidTransitionError,
    is_awaiting_user,
    next_state_after_approval,
)
from apply.schemas.enums import HitlCheckpoint, HitlDecisionType


class ApproveRequest(BaseModel):
    checkpoint: HitlCheckpoint
    decision: HitlDecisionType
    user_edits: str | None = None
    notes: str | None = None


class ApproveResponse(BaseModel):
    run_id: str
    new_state: str


@router.post("/{run_id}/approve", response_model=ApproveResponse)
async def approve_run(
    run_id: str,
    req: ApproveRequest,
    session: AsyncSession = Depends(get_session),
) -> ApproveResponse:
    repo = RunRepository(session)
    run = await repo.load_run(run_id)

    if not is_awaiting_user(run.state):
        raise HTTPException(
            status_code=409,
            detail=f"run is not awaiting approval (state={run.state.value})",
        )

    if req.decision != HitlDecisionType.APPROVE:
        # SKIP / CANCEL / EDIT flows extended in later phases
        raise HTTPException(
            status_code=400,
            detail=f"decision {req.decision.value} not handled in phase 1 skeleton",
        )

    try:
        new_state = next_state_after_approval(run.state)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    await repo.update_run(
        run_id=run_id,
        state=new_state,
        cost_accumulated_usd=run.cost_accumulated_usd,
        artifacts=run.artifacts,
    )

    # Drive the pipeline to the next checkpoint in the background.
    ctx = PipelineContext(
        run_id=run_id,
        application_id=run.application_id,
        jd_url=run.artifacts.get("job_listing", {}).get("url", ""),
        state=new_state,
        artifacts=run.artifacts,
        cost_accumulated_usd=run.cost_accumulated_usd,
    )
    asyncio.create_task(_continue_pipeline(run_id, ctx))

    return ApproveResponse(run_id=run_id, new_state=new_state.value)


async def _continue_pipeline(run_id: str, ctx: PipelineContext) -> None:
    from apply.db.session import get_session as session_dep

    bus = get_event_bus()
    await bus.publish(run_id, {"type": "run_resumed", "state": ctx.state.value})
    try:
        await run_to_next_checkpoint(ctx)
    except Exception as e:
        await bus.publish(run_id, {"type": "error", "message": str(e)})
        return

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

- [ ] **Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/api/routes_runs.py backend/tests/test_api_applications.py
git commit -m "feat(api): POST /runs/{id}/approve advances to next state"
```

---

### Task 31: End-to-end pipeline integration test

**Files:**
- Create: `backend/tests/test_e2e_skeleton.py`

- [ ] **Step 1: Write integration test**

Create `backend/tests/test_e2e_skeleton.py`:

```python
import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from apply.api.main import create_app


@pytest.fixture
def app():
    return create_app()


async def _wait_for_state(client, run_id: str, target: str, timeout: float = 3.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        r = await client.get(f"/runs/{run_id}")
        if r.json()["state"] == target:
            return
        await asyncio.sleep(0.05)
    raise AssertionError(f"state {target} not reached within {timeout}s")


@pytest.mark.asyncio
async def test_full_stub_pipeline_paste_to_completed(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. paste URL
        create = await client.post(
            "/applications",
            json={"jd_url": "https://workatastartup.com/jobs/e2e"},
        )
        assert create.status_code == 201
        run_id = create.json()["run_id"]

        # 2. reach HITL #1
        await _wait_for_state(client, run_id, "AWAITING_FIT_APPROVAL")

        # 3. approve fit gate
        r = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "FIT", "decision": "APPROVE"},
        )
        assert r.status_code == 200

        # 4. reach HITL #2
        await _wait_for_state(client, run_id, "AWAITING_CONTENT_APPROVAL")

        # 5. approve content
        r = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "CONTENT", "decision": "APPROVE"},
        )
        assert r.status_code == 200

        # 6. reach HITL #3
        await _wait_for_state(client, run_id, "AWAITING_SUBMIT_APPROVAL")

        # 7. approve submission
        r = await client.post(
            f"/runs/{run_id}/approve",
            json={"checkpoint": "SUBMIT", "decision": "APPROVE"},
        )
        assert r.status_code == 200

        # 8. reach terminal state
        await _wait_for_state(client, run_id, "COMPLETED")

        # 9. verify artifacts exist
        final = await client.get(f"/runs/{run_id}")
        artifacts = final.json()["artifacts"]
        assert "job_listing" in artifacts
        assert "company_research" in artifacts
        assert "fit_analysis" in artifacts
        assert "cover_letter" in artifacts
        assert "form_fill_result" in artifacts
```

- [ ] **Step 2: Run test**

```bash
cd backend && uv run pytest tests/test_e2e_skeleton.py -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_e2e_skeleton.py
git commit -m "test(e2e): full stub pipeline paste-to-completed integration test"
```

---

### Section G: Observability (Tasks 32-33)

### Task 32: Langfuse setup (optional in V1, wired for later)

**Files:**
- Create: `backend/src/apply/observability/__init__.py`
- Create: `backend/src/apply/observability/langfuse_setup.py`

- [ ] **Step 1: Create observability package**

Create `backend/src/apply/observability/__init__.py` (empty).

- [ ] **Step 2: Implement langfuse setup**

Create `backend/src/apply/observability/langfuse_setup.py`:

```python
from typing import Any

from apply.config import get_settings


class _NoopClient:
    """Drop-in no-op when Langfuse keys are not configured."""

    def trace(self, *args: Any, **kwargs: Any) -> Any:
        return _NoopSpan()

    def span(self, *args: Any, **kwargs: Any) -> Any:
        return _NoopSpan()

    def flush(self) -> None:
        pass


class _NoopSpan:
    def __enter__(self) -> "_NoopSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def update(self, *args: Any, **kwargs: Any) -> None:
        pass

    def end(self) -> None:
        pass


_client: Any | None = None


def get_langfuse() -> Any:
    """Return a Langfuse client or a no-op if not configured."""
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        _client = _NoopClient()
        return _client

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except ImportError:
        _client = _NoopClient()

    return _client
```

- [ ] **Step 3: Verify import**

```bash
cd backend && uv run python -c "from apply.observability.langfuse_setup import get_langfuse; print(type(get_langfuse()).__name__)"
```

Expected output: `_NoopClient` (because Langfuse keys aren't in `.env` yet).

- [ ] **Step 4: Commit**

```bash
git add backend/src/apply/observability/
git commit -m "feat(observability): Langfuse client with no-op fallback"
```

---

### Task 33: Wire trace calls into orchestrator

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`

- [ ] **Step 1: Add span wrapping around each agent call**

Modify `backend/src/apply/orchestrator/graph.py`. Insert at the top of the `run_to_next_checkpoint` function body:

```python
from apply.observability.langfuse_setup import get_langfuse

# ... at the top of the function:
lf = get_langfuse()
trace = lf.trace(name="pipeline_run", id=ctx.run_id)
```

And wrap each agent call. Example around intake:

```python
if ctx.state == PipelineRunState.INTAKE_RUNNING:
    with trace.span(name="intake"):
        listing = await intake_stub(url=ctx.jd_url)
    ctx.artifacts["job_listing"] = listing.model_dump(mode="json")
    ...
```

Full updated function:

```python
async def run_to_next_checkpoint(ctx: PipelineContext) -> None:
    lf = get_langfuse()
    trace = lf.trace(name="pipeline_run", id=ctx.run_id)

    while True:
        if ctx.state == PipelineRunState.INTAKE_RUNNING:
            with trace.span(name="intake"):
                listing = await intake_stub(url=ctx.jd_url)
            ctx.artifacts["job_listing"] = listing.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.001
            ctx.state = advance_state(ctx.state, PipelineRunState.RESEARCHING)
            continue

        if ctx.state == PipelineRunState.RESEARCHING:
            listing = ctx.artifacts["job_listing"]
            with trace.span(name="company_researcher"):
                research = await company_researcher_stub(company_name=listing["company_name"])
            with trace.span(name="fit_analyst"):
                fit = await fit_analyst_stub(
                    job_listing_id=listing["id"],
                    resume_markdown="[stub resume]",
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

- [ ] **Step 2: Run full test suite to verify no regression**

```bash
cd backend && uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py
git commit -m "feat(observability): wrap agent calls in Langfuse spans"
```

---

### Task 34: CLI entry point

**Files:**
- Create: `backend/src/apply/cli.py`

- [ ] **Step 1: Implement CLI**

Create `backend/src/apply/cli.py`:

```python
import sys

import uvicorn

from apply.config import get_settings


def cmd_dev() -> None:
    settings = get_settings()
    uvicorn.run(
        "apply.api.main:app",
        host="0.0.0.0",
        port=settings.apply_port,
        reload=True,
    )


def cmd_migrate() -> None:
    import subprocess

    result = subprocess.run(
        ["alembic", "-c", "src/apply/db/alembic.ini", "upgrade", "head"],
        check=False,
    )
    sys.exit(result.returncode)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: apply <dev|migrate>", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1]
    if cmd == "dev":
        cmd_dev()
    elif cmd == "migrate":
        cmd_migrate()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI wiring**

```bash
cd backend && uv run apply 2>&1 | head -1
```

Expected output: `usage: apply <dev|migrate>`

- [ ] **Step 3: Verify `apply dev` starts the server**

```bash
cd backend && uv run apply dev &
sleep 2
curl -s http://localhost:8000/health
kill %1
```

Expected: curl returns `{"status":"ok","version":"0.1.0"}`; server stops.

- [ ] **Step 4: Commit**

```bash
git add backend/src/apply/cli.py
git commit -m "feat(cli): add apply dev and apply migrate commands"
```

---

### Section H: Frontend (Tasks 35-40)

### Task 35: Frontend API client and SSE subscriber

**Files:**
- Modify: `src/lib/api.ts`
- Create: `src/lib/sse.ts`
- Modify: `src/lib/types.ts`

- [ ] **Step 1: Extend types**

Modify `src/lib/types.ts`:

```typescript
export type HealthResponse = {
  status: string;
  version: string;
};

export type CreateApplicationResponse = {
  run_id: string;
  application_id: string;
  state: string;
};

export type RunResponse = {
  run_id: string;
  application_id: string;
  state: string;
  cost_accumulated_usd: number;
  artifacts: Record<string, unknown>;
};

export type ApproveRequest = {
  checkpoint: "FIT" | "CONTENT" | "SUBMIT";
  decision: "APPROVE" | "EDIT" | "REGENERATE" | "SKIP" | "CANCEL";
  user_edits?: string;
  notes?: string;
};

export type PipelineEvent = {
  type: string;
  [key: string]: unknown;
};
```

- [ ] **Step 2: Extend API client**

Modify `src/lib/api.ts`:

```typescript
import type {
  ApproveRequest,
  CreateApplicationResponse,
  HealthResponse,
  RunResponse,
} from "#/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch("/health");
}

export async function createApplication(
  jdUrl: string,
): Promise<CreateApplicationResponse> {
  return apiFetch("/applications", {
    method: "POST",
    body: JSON.stringify({ jd_url: jdUrl }),
  });
}

export async function getRun(runId: string): Promise<RunResponse> {
  return apiFetch(`/runs/${runId}`);
}

export async function approveRun(
  runId: string,
  body: ApproveRequest,
): Promise<{ run_id: string; new_state: string }> {
  return apiFetch(`/runs/${runId}/approve`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function sseUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/events`;
}
```

- [ ] **Step 3: Implement SSE subscriber hook**

Create `src/lib/sse.ts`:

```typescript
import { useEffect, useState } from "react";
import { sseUrl } from "#/lib/api";
import type { PipelineEvent } from "#/lib/types";

export function useRunEvents(runId: string | null): PipelineEvent[] {
  const [events, setEvents] = useState<PipelineEvent[]>([]);

  useEffect(() => {
    if (!runId) return;

    const src = new EventSource(sseUrl(runId));
    const onMessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data) as PipelineEvent;
        setEvents((prev) => [...prev, data]);
      } catch {
        // ignore malformed event
      }
    };

    src.addEventListener("message", onMessage);
    // Also listen for named event types emitted by sse-starlette
    const namedTypes = [
      "run_started",
      "run_resumed",
      "agent_start",
      "agent_done",
      "checkpoint_reached",
      "error",
    ];
    namedTypes.forEach((t) => src.addEventListener(t, onMessage as EventListener));

    return () => {
      src.close();
    };
  }, [runId]);

  return events;
}
```

- [ ] **Step 4: Commit**

```bash
git add src/lib/api.ts src/lib/sse.ts src/lib/types.ts
git commit -m "feat(frontend): API client + SSE hook for pipeline events"
```

---

### Task 36: /applications/new — paste JD URL

**Files:**
- Create: `src/routes/applications.new.tsx`

- [ ] **Step 1: Implement paste-URL page**

Create `src/routes/applications.new.tsx`:

```tsx
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { createApplication } from "#/lib/api";

export const Route = createFileRoute("/applications/new")({
  component: NewApplicationPage,
});

function NewApplicationPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await createApplication(url);
      navigate({ to: "/applications/$id", params: { id: res.run_id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "unknown error");
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-4">New application</h1>
      <p className="text-sm text-gray-600 mb-6">
        Paste a job posting URL. The agent team will research, draft, and prepare the application for your approval.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://workatastartup.com/jobs/123"
          className="w-full px-3 py-2 border rounded-md"
          disabled={submitting}
        />
        <button
          type="submit"
          disabled={submitting || !url}
          className="px-4 py-2 bg-black text-white rounded-md disabled:opacity-50"
        >
          {submitting ? "Starting..." : "Start application"}
        </button>
      </form>
      {error && <p className="mt-4 text-red-600 text-sm">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/routes/applications.new.tsx
git commit -m "feat(frontend): paste-URL page at /applications/new"
```

---

### Task 37: HITL approval components

**Files:**
- Create: `src/components/HitlFitGate.tsx`
- Create: `src/components/HitlContentApproval.tsx`
- Create: `src/components/HitlSubmissionGate.tsx`

- [ ] **Step 1: Fit Gate component**

Create `src/components/HitlFitGate.tsx`:

```tsx
type Props = {
  fitAnalysis: {
    overall_score: number;
    verdict: string;
    matches: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
    stretches: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
    gaps: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
    reasoning: string;
    recommended_action: string;
  };
  companyResearch?: { company_name: string; signal_score: number };
  onApprove: () => void;
  onSkip: () => void;
  submitting?: boolean;
};

export function HitlFitGate({ fitAnalysis, companyResearch, onApprove, onSkip, submitting }: Props) {
  return (
    <div className="border rounded-lg p-6 bg-white">
      <h2 className="text-xl font-semibold mb-2">Fit review</h2>
      {companyResearch && (
        <p className="text-sm text-gray-600 mb-4">
          {companyResearch.company_name} — research signal score: {(companyResearch.signal_score * 100).toFixed(0)}%
        </p>
      )}

      <div className="flex items-baseline gap-4 mb-4">
        <span className="text-4xl font-bold">{fitAnalysis.overall_score}</span>
        <span className="text-sm text-gray-500">/ 100 — {fitAnalysis.verdict}</span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <FitColumn title="Matches" items={fitAnalysis.matches} color="green" />
        <FitColumn title="Stretches" items={fitAnalysis.stretches} color="amber" />
        <FitColumn title="Gaps" items={fitAnalysis.gaps} color="red" />
      </div>

      <p className="text-sm text-gray-700 mb-4 italic">{fitAnalysis.reasoning}</p>

      <div className="flex gap-2">
        <button
          onClick={onApprove}
          disabled={submitting}
          className="px-4 py-2 bg-green-600 text-white rounded-md disabled:opacity-50"
        >
          Proceed — draft cover letter
        </button>
        <button
          onClick={onSkip}
          disabled={submitting}
          className="px-4 py-2 border rounded-md disabled:opacity-50"
        >
          Skip
        </button>
      </div>
    </div>
  );
}

function FitColumn({
  title,
  items,
  color,
}: {
  title: string;
  items: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
  color: "green" | "amber" | "red";
}) {
  const bg = { green: "bg-green-50", amber: "bg-amber-50", red: "bg-red-50" }[color];
  return (
    <div className={`${bg} p-3 rounded text-sm`}>
      <h3 className="font-semibold mb-2">{title}</h3>
      {items.length === 0 && <p className="text-xs text-gray-500">none</p>}
      <ul className="space-y-2">
        {items.map((p, i) => (
          <li key={i}>
            <div className="font-medium">{p.dimension}</div>
            <div className="text-xs text-gray-600">JD: "{p.evidence_jd}"</div>
            {p.evidence_resume && (
              <div className="text-xs text-gray-600">Resume: "{p.evidence_resume}"</div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 2: Content Approval component**

Create `src/components/HitlContentApproval.tsx`:

```tsx
import { useState } from "react";

type Props = {
  coverLetter: {
    body_markdown: string;
    word_count: number;
    voice_similarity_score: number;
    references_company_specifics: string[];
  };
  onApprove: () => void;
  onSkip: () => void;
  submitting?: boolean;
};

export function HitlContentApproval({ coverLetter, onApprove, onSkip, submitting }: Props) {
  const [body, setBody] = useState(coverLetter.body_markdown);
  const voicePct = (coverLetter.voice_similarity_score * 100).toFixed(0);
  const voiceWarning = coverLetter.voice_similarity_score < 0.6;

  return (
    <div className="border rounded-lg p-6 bg-white">
      <h2 className="text-xl font-semibold mb-2">Cover letter review</h2>
      <div className="flex gap-4 text-xs text-gray-600 mb-3">
        <span>{coverLetter.word_count} words</span>
        <span className={voiceWarning ? "text-amber-700 font-medium" : ""}>
          Voice match: {voicePct}%{voiceWarning ? " ⚠" : ""}
        </span>
      </div>

      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        className="w-full min-h-[300px] border rounded-md p-3 font-mono text-sm"
      />

      <div className="mt-4">
        <h3 className="text-sm font-semibold mb-1">Company specifics cited:</h3>
        <ul className="text-xs text-gray-600 list-disc ml-5">
          {coverLetter.references_company_specifics.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={onApprove}
          disabled={submitting}
          className="px-4 py-2 bg-green-600 text-white rounded-md disabled:opacity-50"
        >
          Approve — fill the form
        </button>
        <button
          onClick={onSkip}
          disabled={submitting}
          className="px-4 py-2 border rounded-md disabled:opacity-50"
        >
          Skip
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Submission Gate component**

Create `src/components/HitlSubmissionGate.tsx`:

```tsx
type Props = {
  formFillResult: {
    fields_filled: { name: string; value: string; field_type: string }[];
    unknown_fields: { name: string; best_guess: string | null; reason_flagged: string }[];
    screenshot_path: string;
  };
  onSubmit: () => void;
  onCancel: () => void;
  submitting?: boolean;
};

export function HitlSubmissionGate({ formFillResult, onSubmit, onCancel, submitting }: Props) {
  return (
    <div className="border rounded-lg p-6 bg-white">
      <h2 className="text-xl font-semibold mb-2">Submission review</h2>
      <p className="text-sm text-gray-600 mb-4">
        Agent screenshot: <code>{formFillResult.screenshot_path}</code>
      </p>

      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-1">Fields filled:</h3>
        <ul className="text-xs space-y-1">
          {formFillResult.fields_filled.map((f) => (
            <li key={f.name}>
              <span className="font-mono">✓ {f.name}</span>
              <span className="text-gray-500">
                {" "}
                ({f.field_type}): {f.value.slice(0, 60)}
                {f.value.length > 60 ? "…" : ""}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {formFillResult.unknown_fields.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 rounded">
          <h3 className="text-sm font-semibold mb-1">⚠ Unknown fields (confirm before submitting):</h3>
          <ul className="text-xs space-y-1">
            {formFillResult.unknown_fields.map((f) => (
              <li key={f.name}>
                <span className="font-mono">{f.name}</span>: guess{" "}
                <span className="italic">"{f.best_guess}"</span> — {f.reason_flagged}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onSubmit}
          disabled={submitting}
          className="px-4 py-2 bg-black text-white rounded-md disabled:opacity-50"
        >
          Submit application
        </button>
        <button
          onClick={onCancel}
          disabled={submitting}
          className="px-4 py-2 border rounded-md disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/HitlFitGate.tsx src/components/HitlContentApproval.tsx src/components/HitlSubmissionGate.tsx
git commit -m "feat(frontend): HITL approval components for fit, content, submission"
```

---

### Task 38: Pipeline timeline component

**Files:**
- Create: `src/components/PipelineTimeline.tsx`

- [ ] **Step 1: Implement timeline**

Create `src/components/PipelineTimeline.tsx`:

```tsx
import type { PipelineEvent } from "#/lib/types";

const STATE_LABELS: Record<string, string> = {
  INTAKE_RUNNING: "Parsing JD",
  RESEARCHING: "Researching company + fit",
  AWAITING_FIT_APPROVAL: "⏸ Awaiting your fit approval",
  DRAFTING: "Drafting cover letter",
  AWAITING_CONTENT_APPROVAL: "⏸ Awaiting your content approval",
  FILLING_FORM: "Filling application form",
  AWAITING_SUBMIT_APPROVAL: "⏸ Awaiting your submit approval",
  SUBMITTING: "Submitting application",
  COMPLETED: "✓ Completed",
  ABANDONED: "Abandoned",
  ERRORED: "⚠ Errored",
};

type Props = {
  currentState: string | null;
  events: PipelineEvent[];
};

export function PipelineTimeline({ currentState, events }: Props) {
  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <h2 className="text-sm font-semibold mb-2 text-gray-700">Pipeline timeline</h2>
      <div className="text-sm mb-3">
        Current state:{" "}
        <span className="font-mono">
          {currentState ? STATE_LABELS[currentState] ?? currentState : "—"}
        </span>
      </div>
      <details>
        <summary className="text-xs text-gray-600 cursor-pointer">Events ({events.length})</summary>
        <ul className="text-xs mt-2 space-y-1 font-mono max-h-40 overflow-auto">
          {events.map((ev, i) => (
            <li key={i} className="text-gray-700">
              {ev.type}
              {ev.state ? ` → ${ev.state}` : ""}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/PipelineTimeline.tsx
git commit -m "feat(frontend): pipeline timeline component"
```

---

### Task 39: /applications/$id — live view with HITL screens

**Files:**
- Create: `src/routes/applications.$id.tsx`

- [ ] **Step 1: Implement the run detail page**

Create `src/routes/applications.$id.tsx`:

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { HitlContentApproval } from "#/components/HitlContentApproval";
import { HitlFitGate } from "#/components/HitlFitGate";
import { HitlSubmissionGate } from "#/components/HitlSubmissionGate";
import { PipelineTimeline } from "#/components/PipelineTimeline";
import { approveRun, getRun } from "#/lib/api";
import { useRunEvents } from "#/lib/sse";
import type { RunResponse } from "#/lib/types";

export const Route = createFileRoute("/applications/$id")({
  component: RunDetailPage,
});

function RunDetailPage() {
  const { id } = Route.useParams();
  const [run, setRun] = useState<RunResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const events = useRunEvents(id);

  async function refresh() {
    try {
      const r = await getRun(id);
      setRun(r);
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 1000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    // Events can carry new state info; refresh eagerly on each
    if (events.length > 0) refresh();
  }, [events.length]);

  async function approve(checkpoint: "FIT" | "CONTENT" | "SUBMIT") {
    setSubmitting(true);
    try {
      await approveRun(id, { checkpoint, decision: "APPROVE" });
      await refresh();
    } finally {
      setSubmitting(false);
    }
  }

  if (!run) return <div className="p-8">Loading…</div>;

  const artifacts = run.artifacts as Record<string, any>;

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-4">
      <h1 className="text-2xl font-semibold">Application run</h1>
      <p className="text-xs text-gray-500">
        Run {run.run_id} • App {run.application_id} • Cost ${run.cost_accumulated_usd.toFixed(3)}
      </p>

      <PipelineTimeline currentState={run.state} events={events} />

      {run.state === "AWAITING_FIT_APPROVAL" && artifacts.fit_analysis && (
        <HitlFitGate
          fitAnalysis={artifacts.fit_analysis}
          companyResearch={artifacts.company_research}
          onApprove={() => approve("FIT")}
          onSkip={() => {/* SKIP flow in phase 2+ */}}
          submitting={submitting}
        />
      )}

      {run.state === "AWAITING_CONTENT_APPROVAL" && artifacts.cover_letter && (
        <HitlContentApproval
          coverLetter={artifacts.cover_letter}
          onApprove={() => approve("CONTENT")}
          onSkip={() => {/* SKIP flow in phase 2+ */}}
          submitting={submitting}
        />
      )}

      {run.state === "AWAITING_SUBMIT_APPROVAL" && artifacts.form_fill_result && (
        <HitlSubmissionGate
          formFillResult={artifacts.form_fill_result}
          onSubmit={() => approve("SUBMIT")}
          onCancel={() => {/* CANCEL flow in phase 2+ */}}
          submitting={submitting}
        />
      )}

      {run.state === "COMPLETED" && (
        <div className="border rounded-lg p-6 bg-green-50">
          <h2 className="text-xl font-semibold">Application submitted ✓</h2>
          <p className="text-sm mt-2">
            Confirmation: {(artifacts.submission_confirmation as any)?.url ?? "—"}
          </p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/routes/applications.$id.tsx
git commit -m "feat(frontend): run detail page with HITL screens wired to SSE"
```

---

### Task 40: /applications index and nav link

**Files:**
- Create: `src/routes/applications.index.tsx`
- Modify: `src/routes/__root.tsx`

- [ ] **Step 1: Index page**

Create `src/routes/applications.index.tsx`:

```tsx
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/applications/")({
  component: ApplicationsIndexPage,
});

function ApplicationsIndexPage() {
  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-4">Applications</h1>
      <p className="text-sm text-gray-600 mb-6">
        List view coming in Phase 5 — for now, start a new application.
      </p>
      <Link
        to="/applications/new"
        className="inline-block px-4 py-2 bg-black text-white rounded-md"
      >
        New application
      </Link>
    </div>
  );
}
```

- [ ] **Step 2: Add nav link**

Modify `src/routes/__root.tsx` — inside the shell component, add a nav link in the existing nav section:

```tsx
<Link to="/applications" className="text-sm hover:underline">
  Applications
</Link>
```

- [ ] **Step 3: Verify end-to-end in browser**

Terminal A:

```bash
cd backend && uv run apply dev
```

Terminal B:

```bash
pnpm dev
```

Manual flow:
1. Open `http://localhost:3000`
2. Click "Applications" in nav
3. Click "New application"
4. Paste `https://workatastartup.com/jobs/demo`
5. Click "Start application"
6. Verify you land on run detail page
7. Verify HITL Fit Gate appears within ~1 second
8. Click "Proceed"
9. Verify HITL Content Approval appears
10. Click "Approve"
11. Verify HITL Submission Gate appears
12. Click "Submit application"
13. Verify "Application submitted ✓" success view

Stop both terminals.

- [ ] **Step 4: Commit**

```bash
git add src/routes/applications.index.tsx src/routes/__root.tsx
git commit -m "feat(frontend): applications index page and nav link"
```

---

### Task 41: Document the walking skeleton + update LEARNINGS.md

**Files:**
- Modify: `LEARNINGS.md`
- Modify: `README.md`

- [ ] **Step 1: Add first LEARNINGS entry**

Append to `LEARNINGS.md`:

```markdown
## 2026-04-23 — Walking-skeleton-first paid off
Tags: architecture, product-decisions

Built the complete pipeline with stub agents before touching any real
LLM calls. Took about 20 hours. By the time the skeleton was running,
every hard architectural question — HITL state machine, SSE event
streaming, frontend/backend boundary, run persistence — was answered.

The payoff: when Phase 2 replaces stubs with real agents, none of those
answers have to change. Replacing one stub at a time is a much smaller
refactor than simultaneously implementing the agent AND figuring out how
approval resumes it AND how events stream to the UI.

**Takeaway:** for any project with >3 layers of integration (agents +
state machine + streaming + UI), build the skeleton first with fakes.
The cost of the skeleton is a fraction of the cost of integration bugs
discovered in week 4.

---
```

- [ ] **Step 2: Rewrite README**

Replace `README.md` with a project-focused README (the existing one is the TanStack template default):

```markdown
# Apply

Autonomous job application agent. Paste a job URL, and a 7-agent team
produces a recruiter-quality application: company brief, fit analysis,
bespoke cover letter, and an auto-filled application form — with human
approval at 3 checkpoints before anything submits.

> **Status:** Phase 0 + 1 complete. Walking skeleton runs end-to-end
> with stub agents. Phases 2-5 (real agents, MCP servers, Form-Fill via
> Claude Agent SDK + Playwright, evals, baseline comparison) are
> upcoming.

## Architecture

See `docs/superpowers/specs/2026-04-23-auto-apply-design.md` for the
full design doc.

## Local development

Prereqs: `docker`, `pnpm`, `uv`, Python 3.12+.

### 1. Start infra

```bash
docker compose up -d
```

Brings up Postgres + Langfuse.

### 2. Start backend

```bash
cd backend
uv sync
cp ../.env.example ../.env  # fill in values (or leave blank for stubs)
uv run alembic -c src/apply/db/alembic.ini upgrade head
uv run apply dev
```

Backend listens on `http://localhost:8000`.

### 3. Start frontend

```bash
pnpm install
pnpm dev
```

Frontend on `http://localhost:3000`.

### 4. End-to-end smoke

1. Visit `http://localhost:3000/applications/new`
2. Paste any URL
3. Approve at each HITL checkpoint
4. See the simulated "submitted" confirmation

## Running tests

```bash
cd backend
uv run pytest -v
```
```

- [ ] **Step 3: Commit**

```bash
git add LEARNINGS.md README.md
git commit -m "docs: first LEARNINGS entry + project README for walking skeleton"
```

---

### Task 42: Final verification — run full test suite and manual smoke

- [ ] **Step 1: Run the entire backend test suite**

```bash
cd backend && uv run pytest -v
```

Expected: all tests PASS. Count should be roughly:
- test_config.py: 2 tests
- test_schemas.py: 12+ tests
- test_state_machine.py: 6 tests
- test_agents_stub.py: 7 tests (one per agent)
- test_orchestrator.py: 6+ tests
- test_api_health.py: 1 test
- test_api_applications.py: 3 tests
- test_api_sse.py: 1 test
- test_e2e_skeleton.py: 1 test

Total: ~40 tests.

- [ ] **Step 2: Run linter**

```bash
cd backend && uv run ruff check src/ tests/
```

Expected: no issues. Fix any reported issues and commit.

- [ ] **Step 3: Manual smoke test (full stack)**

Same as Task 40 Step 3 — repeat the full UI flow end-to-end. Expected: smooth, <5s per step, all 3 HITL screens render with their respective data.

- [ ] **Step 4: Tag the milestone**

```bash
git tag v0.1.0-walking-skeleton
git log --oneline -30
```

Expected: ~42 commits, each focused.

---

## Self-review checklist

Before declaring the plan done, verify:

- [ ] **Spec coverage:** every Phase 0 + Phase 1 deliverable in the design spec has a matching task. (Real LLM calls, MCP servers, evals, etc. are explicitly out of scope for this plan.)
- [ ] **No placeholders:** every task has complete code; no "implement the rest", no "add similar tests for other agents."
- [ ] **Type consistency:** `PipelineRunState.AWAITING_FIT_APPROVAL` used consistently across schema, state machine, orchestrator, API routes, and frontend components.
- [ ] **All exact paths are absolute from the repo root or relative to `backend/` / frontend root.**
- [ ] **All commands show expected output** where output is verifiable.
- [ ] **Commits are one logical unit each** and the messages follow the existing repo style (no trailing Claude co-author trailer, per repo convention).

---

## Out of scope for this plan (handled in Phase 2-5 plans)

- Real LLM calls (Haiku, Sonnet, GPT-4.1)
- Real MCP servers (resume-mcp, memory-mcp)
- Real web search / Firecrawl / Tavily integration
- Claude Agent SDK computer-use agent
- Playwright MCP integration
- ChromaDB embeddings
- Eval harness, LLM-as-judge, baseline comparison
- Dashboard
- Onboarding flow (resume upload UI, profile form, voice corpus seeding)
- Memory Curator real implementation

Each of the above will get its own plan in its phase.
