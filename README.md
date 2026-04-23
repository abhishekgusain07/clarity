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
