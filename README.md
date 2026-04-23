# Apply

Autonomous job application agent. Paste a job URL, and a 7-agent team
produces a recruiter-quality application: company brief, fit analysis,
bespoke cover letter, and an auto-filled application form — with human
approval at 3 checkpoints before anything submits.

> **Status:** Phase 2a complete. Real Intake, Company Researcher, and
> Fit Analyst agents are wired behind the `APPLY_USE_REAL_AGENTS` flag.
> Walking skeleton still runs with stubs by default. Phase 2b (eval
> harness + baseline comparison) is next.

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


## Running with real agents

Set `APPLY_USE_REAL_AGENTS=true` in `.env` and ensure these keys are set:

- `APPLY_OPENROUTER_API_KEY` — routes Claude Haiku + Sonnet through OpenRouter
- `TAVILY_API_KEY` — web search (free tier: 1000/mo)
- `FIRECRAWL_API_KEY` — scraping (free tier: 500/mo)

Also needs `npx` in PATH — the Tavily and Firecrawl MCP servers run as
Node subprocesses.

With keys set, the live integration test runs:

```bash
cd backend && uv run pytest tests/test_integration_real_agents.py -v
```

## Under the hood: LLM routing

Claude is not called via the Anthropic SDK. All LLM traffic is routed
through OpenRouter's OpenAI-compatible endpoint at
`https://openrouter.ai/api/v1` with two attribution headers:

- `HTTP-Referer` — identifies our app in OpenRouter's leaderboards
- `X-Title` — human-readable app name

Both are driven by `APPLY_HTTP_REFERER` and `APPLY_X_TITLE` so the
binding lives in config, not code. `APPLY_OPENROUTER_API_KEY` is the
only secret; rotating it is a one-line `.env` change.

## Running tests

```bash
cd backend
uv run pytest -v
```
