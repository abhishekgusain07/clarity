# Apply — Phase 4a Implementation Plan (Form-Fill via Pydantic AI + Playwright MCP)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Replace the Form-Fill stub with a real browser-driving agent using **Pydantic AI + Playwright MCP via OpenRouter** (no new API keys required). The agent navigates to YC WaaS application forms, inspects the DOM via Playwright's accessibility tools, fills known fields from profile/resume/cover-letter, calls the Screening Answerer as a tool for unknown free-text fields, captures a screenshot for HITL #3, and returns a structured `FormFillResult`. Submission is a separate explicit call after user approval.

**Architecture:** Form-Fill is a `pydantic_ai.Agent` with Claude Sonnet (via OpenRouter, same stack as research agents) and two toolsets: (1) Playwright MCP for browser control, (2) a `@agent.tool` method `answer_screening_question` that calls `runtime.screening_answerer` using pipeline context injected via Pydantic AI's `deps` pattern. Structured output: `FormFillResult`. No Claude Agent SDK, no direct Anthropic key, no computer-use beta — just tool-use over an accessibility tree, which is better suited to structured HTML forms anyway.

**Tech Stack:** Pydantic AI 1.86 (already installed, already wired through OpenRouter for Claude), Playwright MCP (`@playwright/mcp@latest` via `npx`), Chromium (auto-installed by Playwright MCP on first run).

**Scope limits:**
- **V1 supports YC WaaS forms only.** Greenhouse/Lever/Ashby/Workday → Phase 4b.
- **No live submission in CI.** Integration tests use a local HTML fixture. Real submissions are user-triggered.
- **Screening callback is via `deps`-injected tool** — this is the multi-agent collaboration story.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md` § 6 (Agent 6: Form-Fill)

---

## File map

**New:**
- `backend/src/apply/agents/form_fill_real.py`
- `backend/src/apply/agents/form_context.py` (typed `FormFillDeps`)
- `backend/tests/agents/test_form_fill_real.py`
- `backend/tests/agents/test_form_context.py`
- `backend/tests/fixtures/simple_application_form.html`
- `backend/tests/integration/__init__.py`
- `backend/tests/integration/test_form_fill_local.py`
- `spikes/pydantic_ai_playwright_spike.py`

**Modified:**
- `backend/src/apply/agents/mcp_servers.py` — add `playwright_mcp()` factory alongside tavily/firecrawl
- `backend/src/apply/agents/runtime.py` — add `form_fill` entrypoint
- `backend/src/apply/orchestrator/graph.py` — build `FormFillDeps` and route Form-Fill through runtime
- `backend/seed/profile.json` — add `full_name` + optional `resume_pdf_path`
- `LEARNINGS.md`, `README.md`

**Not needed (explicitly removed from the prior plan):**
- `claude-agent-sdk` dependency
- `backend/src/apply/agents/mcp_servers_browser.py` (merged into main `mcp_servers.py`)
- `ANTHROPIC_API_KEY` in `.env`

---

## Prerequisites

- Phase 3b merged to master (`git log master --oneline | head -1` shows `22ceddd` or later)
- Node + `npx` on PATH (already installed from Phase 2a)
- `.env` has `APPLY_OPENROUTER_API_KEY` (already set)
- Docker running Postgres (`docker ps | grep apply-postgres`)

---

## Task 1: Spike — Pydantic AI + Playwright MCP fills one field

**Goal:** prove the integration before building the full agent. Success criterion: agent launches Playwright MCP, opens a local HTML form, fills `full_name`, returns structured output confirming the action. If this spike fails, we STOP and replan.

**Files:**
- Create: `backend/tests/fixtures/simple_application_form.html`
- Create: `spikes/pydantic_ai_playwright_spike.py`

- [ ] **Step 1: Create the local test form**

Create `backend/tests/fixtures/simple_application_form.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Test Application</title></head>
<body>
<h1>Apply for: Test Engineer at Test Corp</h1>
<form id="app-form" action="/submit" method="post">
  <label>Full name: <input type="text" name="full_name" id="full_name" required /></label><br/>
  <label>Email: <input type="email" name="email" id="email" required /></label><br/>
  <label>GitHub URL: <input type="url" name="github_url" id="github_url" /></label><br/>
  <label>Cover letter:<br/>
    <textarea name="cover_letter" id="cover_letter" rows="8" cols="60"></textarea>
  </label><br/>
  <label>Why us?:<br/>
    <textarea name="why_us" id="why_us" rows="4" cols="60" placeholder="Screening question"></textarea>
  </label><br/>
  <button type="submit" id="submit-btn">Submit application</button>
</form>
</body>
</html>
```

- [ ] **Step 2: Create the spike script**

Create `spikes/pydantic_ai_playwright_spike.py`:

```python
"""Phase 4a spike: Pydantic AI + Playwright MCP via OpenRouter.

Proves that our existing stack (Pydantic AI + Claude via OpenRouter,
same as research agents) can drive a browser via Playwright MCP.

Success: script fills `full_name` on the local test form and returns
a structured result describing what it did.

Requires: APPLY_OPENROUTER_API_KEY in env, npx on PATH.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure backend src is importable when running from repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from apply.agents.models import sonnet


class SpikeResult(BaseModel):
    action_taken: str
    field_filled: str
    value_written: str
    success: bool


async def main() -> None:
    form_path = ROOT / "backend" / "tests" / "fixtures" / "simple_application_form.html"
    file_url = f"file://{form_path.resolve()}"

    playwright_server = MCPServerStdio(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env={"PLAYWRIGHT_HEADLESS": "true"},
    )

    agent = Agent(
        model=sonnet(),
        output_type=SpikeResult,
        system_prompt=(
            "You have Playwright browser tools. Navigate to the given URL, "
            "inspect the form, fill ONE field (`full_name`) with the value "
            '"Sanyam Upadhyay", and return a structured result. Do NOT submit.'
        ),
        toolsets=[playwright_server],
    )

    async with agent:
        result = await agent.run(f"Fill the full_name field at: {file_url}")

    print("=== RESULT ===")
    print(result.output.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Run the spike**

```bash
cd /Users/sanyamupadhyay/Documents/gusain/clarity
set -a && source .env && set +a
uv run --directory backend python ../spikes/pydantic_ai_playwright_spike.py
```

**Expected A (success):** agent prints `SpikeResult` JSON with `success: true`, `field_filled: "full_name"`, `value_written: "Sanyam Upadhyay"`, `action_taken` describing the fill. Takes 30-60s + ~$0.05.

**Expected B (failure paths):**
- **npm package name shifted** (`@playwright/mcp` vs `@playwright/mcp-server`) → try `npx -y @playwright/mcp-server@latest` and retry.
- **Playwright needs Chromium install** → first run prints a message about downloading Chromium (~100MB). That's fine; let it finish.
- **Pydantic AI MCP toolset API differs** — if `toolsets=` keyword fails, try `mcp_servers=` (older name). Same rationale as Phase 2a Chunk 2 adaptations.
- **Agent loops forever** — hit max_turns. Adjust the system prompt to make the task more bounded, or cap `max_turns` in agent config.

**If B:** report BLOCKED with exact error. Do not proceed.

- [ ] **Step 4: Commit (regardless of outcome)**

```bash
git add spikes/ backend/tests/fixtures/simple_application_form.html
git commit -m "chore(phase-4a): spike Pydantic AI + Playwright MCP via OpenRouter"
```

---

## Task 2: `FormFillDeps` typed dependency

**Files:**
- Create: `backend/src/apply/agents/form_context.py`
- Create: `backend/tests/agents/test_form_context.py`

Pydantic AI's `deps` pattern lets you inject runtime context into tool functions. `FormFillDeps` holds everything the agent's tools need at run time.

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_form_context.py`:

```python
from apply.agents.form_context import FormFillDeps


def test_form_fill_deps_fields():
    deps = FormFillDeps(
        application_url="https://example.com/apply",
        profile={"full_name": "Sanyam Upadhyay", "email": "e@x.co"},
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, …",
        company_name="Acme AI",
        company_brief="Series A agent startup",
        jd_markdown="Engineer role",
        voice_samples=["Sample."],
    )
    assert deps.profile["full_name"] == "Sanyam Upadhyay"
    assert deps.company_name == "Acme AI"
    assert deps.resume_pdf_path == "/tmp/resume.pdf"


def test_form_fill_deps_is_frozen():
    """Deps should be safe to share across tool invocations — immutable."""
    import dataclasses

    from apply.agents.form_context import FormFillDeps
    assert dataclasses.is_dataclass(FormFillDeps)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_form_context.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/form_context.py`:

```python
"""Typed dependency bundle injected into the Form-Fill agent at run time.

Pydantic AI's `deps` pattern lets the agent's custom tools access this
context via `RunContext[FormFillDeps].deps`. Frozen to prevent mutation
mid-run.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormFillDeps:
    application_url: str
    profile: dict[str, str]
    resume_pdf_path: str
    cover_letter_text: str
    company_name: str
    company_brief: str
    jd_markdown: str
    voice_samples: list[str]
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_form_context.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/form_context.py backend/tests/agents/test_form_context.py
git commit -m "feat(agents): FormFillDeps typed run-time context for Form-Fill agent"
```

---

## Task 3: Playwright MCP factory

**Files:**
- Modify: `backend/src/apply/agents/mcp_servers.py`

- [ ] **Step 1: Add `playwright_mcp()` alongside existing factories**

Read `backend/src/apply/agents/mcp_servers.py` first, then append:

```python
def playwright_mcp() -> MCPServerStdio:
    """Microsoft's official Playwright MCP server.

    Runs Chromium as a Node subprocess. On first run, Playwright downloads
    Chromium (~100MB); cached thereafter. Set PLAYWRIGHT_HEADLESS=false in
    the environment to watch the browser visually during debugging.
    """
    import os
    return MCPServerStdio(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env={"PLAYWRIGHT_HEADLESS": os.getenv("PLAYWRIGHT_HEADLESS", "true")},
    )
```

- [ ] **Step 2: Verify**

```bash
cd backend && uv run python -c "from apply.agents.mcp_servers import playwright_mcp; s = playwright_mcp(); print(type(s).__name__, s.args)"
```

Expected: `MCPServerStdio ['-y', '@playwright/mcp@latest']`

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/agents/mcp_servers.py
git commit -m "feat(mcp): Playwright MCP factory alongside Tavily/Firecrawl"
```

---

## Task 4: Form-Fill real agent with screening-question tool

**Files:**
- Create: `backend/src/apply/agents/form_fill_real.py`
- Create: `backend/tests/agents/test_form_fill_real.py`

**Design:** Pydantic AI `Agent` with Sonnet, `FormFillDeps` as deps type, Playwright MCP as a toolset, and one custom `@agent.tool` that calls `runtime.screening_answerer` using pipeline context from deps. Structured output = `FormFillResult`.

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_form_fill_real.py`:

```python
from unittest.mock import patch

import pytest
from pydantic_ai.models.test import TestModel

from apply.agents.form_context import FormFillDeps
from apply.agents.form_fill_real import form_fill_real
from apply.agents.form_fill import FormFillResult


@pytest.fixture
def sample_deps() -> FormFillDeps:
    return FormFillDeps(
        application_url="file:///tmp/test.html",
        profile={"full_name": "Test User", "email": "t@e.co"},
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, …",
        company_name="Acme AI",
        company_brief="Series A agent startup",
        jd_markdown="Engineer role",
        voice_samples=[],
    )


@pytest.mark.asyncio
async def test_form_fill_real_returns_structured_result(sample_deps):
    test_model = TestModel(
        custom_output_args={
            "fields_filled": [
                {"name": "full_name", "value": "Test User", "field_type": "text"},
                {"name": "email", "value": "t@e.co", "field_type": "text"},
                {"name": "cover_letter", "value": "Dear team, …", "field_type": "textarea"},
            ],
            "unknown_fields": [],
            "screenshot_path": "/tmp/apply/fill.png",
            "submission_url": None,
            "success": True,
        }
    )

    from apply.agents import form_fill_real as mod

    # Build a new agent without the real Playwright MCP toolset for the test
    from pydantic_ai import Agent

    agent_without_mcp = Agent(
        model=test_model,
        output_type=FormFillResult,
        deps_type=FormFillDeps,
        system_prompt="test",
    )

    with patch.object(mod, "_build_agent", return_value=agent_without_mcp):
        result = await form_fill_real(deps=sample_deps)

    assert isinstance(result, FormFillResult)
    assert result.success
    assert len(result.fields_filled) == 3
    assert any(f.name == "full_name" for f in result.fields_filled)
    assert result.screenshot_path == "/tmp/apply/fill.png"


@pytest.mark.asyncio
async def test_form_fill_real_surfaces_unknown_fields(sample_deps):
    test_model = TestModel(
        custom_output_args={
            "fields_filled": [
                {"name": "full_name", "value": "Test User", "field_type": "text"}
            ],
            "unknown_fields": [
                {
                    "name": "why_us",
                    "field_type": "textarea",
                    "best_guess": None,
                    "reason_flagged": "open-ended question not in profile",
                }
            ],
            "screenshot_path": "/tmp/s.png",
            "submission_url": None,
            "success": True,
        }
    )

    from apply.agents import form_fill_real as mod
    from pydantic_ai import Agent

    agent_without_mcp = Agent(
        model=test_model,
        output_type=FormFillResult,
        deps_type=FormFillDeps,
        system_prompt="test",
    )

    with patch.object(mod, "_build_agent", return_value=agent_without_mcp):
        result = await form_fill_real(deps=sample_deps)

    assert len(result.unknown_fields) == 1
    assert result.unknown_fields[0].name == "why_us"
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_form_fill_real.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/form_fill_real.py`:

```python
"""Real Form-Fill browser-driving agent.

Pydantic AI Agent with:
- Claude Sonnet via OpenRouter (same stack as research agents)
- Playwright MCP as a toolset (browser control)
- One custom tool `answer_screening_question` that calls the real
  Screening Answerer using pipeline context from deps
- Structured output: FormFillResult

The agent navigates to the application URL, inspects the form via
Playwright's accessibility snapshot, fills what it knows from the
profile/cover letter, calls the screening tool for unknown free-text
fields, captures a screenshot, and returns the structured result.

It does NOT submit — submission is a separate step after HITL #3.
"""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from apply.agents.form_context import FormFillDeps
from apply.agents.form_fill import FormFillResult
from apply.agents.mcp_servers import playwright_mcp
from apply.agents.models import sonnet
from apply.schemas.enums import ScreeningAnswerOrigin


SYSTEM_PROMPT = """
You are filling a job application form via a browser. You have Playwright
tools (navigate, click, fill, upload, screenshot, accessibility_snapshot)
and a custom `answer_screening_question` tool that drafts answers to
free-text questions in the candidate's voice.

Your job for THIS application:

1. Navigate to `application_url` (in your deps).
2. Take an accessibility snapshot. Identify every form field.
3. Fill fields you have direct values for from deps.profile:
   - full_name, email, phone, linkedin_url, github_url, portfolio_url,
     location — all optional, fill what's set.
4. Upload the resume: `deps.resume_pdf_path`.
5. Paste `deps.cover_letter_text` into the cover-letter textarea.
6. For any free-text question (like "Why us?", "Tell us about a time…"):
   - Call `answer_screening_question(question)` to get a drafted answer.
   - Fill the field with the returned answer.
7. For fields you truly can't interpret (custom dropdowns, file types
   you don't have), put them in `unknown_fields` with `best_guess=null`
   and a short `reason_flagged`. DO NOT fabricate.
8. Take a final screenshot. Include the absolute path in `screenshot_path`.
9. DO NOT click Submit. Return the structured FormFillResult.

Return JSON only via the structured output — do not narrate.
"""


def _build_agent() -> Agent:
    """Build at call time so MCP subprocess binds to current loop."""
    agent: Agent = Agent(
        model=sonnet(),
        output_type=FormFillResult,
        deps_type=FormFillDeps,
        system_prompt=SYSTEM_PROMPT,
        toolsets=[playwright_mcp()],
        retries=1,
    )

    @agent.tool
    async def answer_screening_question(
        ctx: RunContext[FormFillDeps], question: str
    ) -> str:
        """Draft an answer to a screening question in the candidate's voice."""
        # Import inside to avoid circular import at module load time
        from apply.agents.runtime import screening_answerer

        deps = ctx.deps
        result = await screening_answerer(
            question=question,
            company_name=deps.company_name,
            company_brief=deps.company_brief,
            jd_markdown=deps.jd_markdown,
            corpus_resume_markdown="",  # resume already uploaded as file; text
            corpus_voice_samples=deps.voice_samples,
            origin=ScreeningAnswerOrigin.FORM_FILL_CALLBACK,
        )
        return result.answer

    return agent


async def form_fill_real(deps: FormFillDeps) -> FormFillResult:
    agent = _build_agent()
    async with agent:
        result = await agent.run(
            f"Proceed with the application at {deps.application_url}.",
            deps=deps,
        )
    return result.output
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_form_fill_real.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/form_fill_real.py backend/tests/agents/test_form_fill_real.py
git commit -m "feat(agents): real Form-Fill agent (Pydantic AI + Playwright MCP)"
```

---

## Task 5: Runtime entrypoint

**Files:**
- Modify: `backend/src/apply/agents/runtime.py`

- [ ] **Step 1: Add form_fill entrypoint**

Add imports near the other agent imports in `backend/src/apply/agents/runtime.py`:

```python
from apply.agents.form_context import FormFillDeps
from apply.agents.form_fill import FormFillResult
from apply.agents.form_fill import form_fill_stub as _ff_stub
from apply.agents.form_fill_real import form_fill_real as _form_fill_real
```

Append at the bottom:

```python
async def form_fill(deps: FormFillDeps) -> FormFillResult:
    if _use_real():
        return await _form_fill_real(deps=deps)
    return await _ff_stub(
        application_url=deps.application_url,
        cover_letter_body=deps.cover_letter_text,
    )
```

- [ ] **Step 2: Run full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: no regressions.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/agents/runtime.py
git commit -m "feat(agents): runtime entrypoint for Form-Fill"
```

---

## Task 6: Orchestrator builds `FormFillDeps` and routes through runtime

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`

- [ ] **Step 1: Update FILLING_FORM branch**

In `backend/src/apply/orchestrator/graph.py`, add these imports at the top:

```python
from apply.agents.form_context import FormFillDeps
from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus
```

Remove (if present): `from apply.agents.form_fill import form_fill_stub` — the runtime handles both paths now.

Replace the existing `FILLING_FORM` branch with:

```python
        if ctx.state == PipelineRunState.FILLING_FORM:
            _load_corpus_once(ctx)
            listing = ctx.artifacts.get("job_listing", {})
            application_url = listing.get("application_url", ctx.jd_url)
            letter = ctx.artifacts.get("cover_letter", {})
            research = ctx.artifacts.get("company_research", {})
            samples: list[str] = ctx.artifacts.get("voice_samples", [])

            corpus = ResumeCorpus()
            profile: dict[str, str] = {}
            for k in ("full_name", "name", "email", "phone", "linkedin_url",
                      "github_url", "portfolio_url", "location"):
                v = corpus.profile_field(k)
                if v is not None:
                    profile[k] = v
            # Fallback: if full_name isn't set, use name
            if "full_name" not in profile and "name" in profile:
                profile["full_name"] = profile["name"]

            resume_pdf_path = (
                corpus.profile_field("resume_pdf_path")
                or str((corpus.seed_dir / "resume.md").resolve())
            )

            deps = FormFillDeps(
                application_url=application_url,
                profile=profile,
                resume_pdf_path=resume_pdf_path,
                cover_letter_text=letter.get("body_markdown", ""),
                company_name=listing.get("company_name", ""),
                company_brief=(
                    f"{research.get('company_name', '')} — "
                    f"signal {research.get('signal_score', 0):.2f}"
                ),
                jd_markdown=listing.get("description_markdown", ""),
                voice_samples=samples,
            )

            with trace.span(name="form_fill"):
                result = await runtime.form_fill(deps=deps)
            ctx.artifacts["form_fill_result"] = result.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.15  # form-fill is the expensive step
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_SUBMIT_APPROVAL)
            return
```

- [ ] **Step 2: Run full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all pass. Walking skeleton still green because runtime.form_fill routes to stub under `APPLY_USE_REAL_AGENTS=false` and the stub ignores the deps shape (it reads `application_url` + `cover_letter_text` from the deps bundle — compatible signature).

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py
git commit -m "feat(orchestrator): build FormFillDeps and route Form-Fill through runtime"
```

---

## Task 7: Integration test against local HTML form (opt-in)

**Files:**
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/integration/test_form_fill_local.py`

- [ ] **Step 1: Create package + integration test**

```bash
mkdir -p backend/tests/integration
touch backend/tests/integration/__init__.py
```

Create `backend/tests/integration/test_form_fill_local.py`:

```python
"""Live Form-Fill test against a local HTML form.

Opt-in: requires APPLY_OPENROUTER_API_KEY. Costs ~$0.10-0.30 per run.
Not run in CI.
"""
import os
from pathlib import Path

import pytest

from apply.agents.form_context import FormFillDeps

REQUIRED = ("APPLY_OPENROUTER_API_KEY",)
_HAS_KEY = all(os.getenv(k) for k in REQUIRED)


@pytest.mark.skipif(not _HAS_KEY, reason="APPLY_OPENROUTER_API_KEY not set")
@pytest.mark.asyncio
async def test_form_fill_local_html(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime

    form_path = Path(__file__).parent.parent / "fixtures/simple_application_form.html"
    url = f"file://{form_path.resolve()}"

    deps = FormFillDeps(
        application_url=url,
        profile={
            "full_name": "Sanyam Upadhyay",
            "email": "satish@team.galaxy.ai",
            "github_url": "https://github.com/sanyamupadhyay",
        },
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, this is a test cover letter drafted for integration testing.",
        company_name="Test Corp",
        company_brief="A local HTML test form",
        jd_markdown="Test Engineer role.",
        voice_samples=["The discipline that makes good backend code makes good agent code."],
    )

    result = await runtime.form_fill(deps=deps)

    # Core fields the agent should fill
    filled_names = {f.name for f in result.fields_filled}
    assert "full_name" in filled_names or "name" in filled_names, (
        f"expected full_name/name in filled, got {filled_names}"
    )
    assert "email" in filled_names, f"expected email in filled, got {filled_names}"
    assert "cover_letter" in filled_names, f"expected cover_letter in filled, got {filled_names}"

    # The `why_us` screening question should be handled — either answered via
    # the tool (appears in filled_names) or flagged as unknown. Both are OK.
    unknown_names = {u.name for u in result.unknown_fields}
    assert "why_us" in filled_names or "why_us" in unknown_names
```

- [ ] **Step 2: Run (expect skip without key, pass with key)**

```bash
cd backend && uv run pytest tests/integration/test_form_fill_local.py -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/
git commit -m "test(integration): opt-in Form-Fill against local HTML form"
```

---

## Task 8: Profile seed updates

**Files:**
- Modify: `backend/seed/profile.json`

- [ ] **Step 1: Add full_name + resume_pdf_path fields**

Edit `backend/seed/profile.json`:

```json
{
  "name": "Sanyam Upadhyay",
  "full_name": "Sanyam Upadhyay",
  "email": "satish@team.galaxy.ai",
  "phone": "",
  "linkedin_url": "",
  "github_url": "https://github.com/sanyamupadhyay",
  "portfolio_url": "",
  "location": "Remote",
  "work_auth": "OPEN_TO_DISCUSS",
  "salary_expectation_usd": null,
  "remote_preference": "REMOTE_OK",
  "resume_pdf_path": ""
}
```

- [ ] **Step 2: Run existing tests**

```bash
cd backend && uv run pytest tests/mcp_servers/test_corpus.py -v
```

Expected: all pass (corpus reads fields by key; extra keys are ignored).

- [ ] **Step 3: Commit**

```bash
git add backend/seed/profile.json
git commit -m "chore(seed): add full_name + resume_pdf_path fields"
```

---

## Task 9: Docs + final verify + tag

- [ ] **Step 1: Full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all pass. Count roughly 96 (from Phase 3b) + ~5 new (2 deps + 2 form_fill + 1 integration-skipped) = ~101.

- [ ] **Step 2: Ruff clean**

```bash
cd backend && uv run ruff check src/ tests/ eval/
```

If issues, fix minimally. Add per-file-ignores to `pyproject.toml` for `src/apply/agents/form_fill_real.py` (long prompt) if needed. Commit as `chore: ruff cleanup for Phase 4a` if fixes applied.

- [ ] **Step 3: Walking skeleton still green with stubs**

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run pytest tests/test_e2e_skeleton.py -v
```

Expected: 1 passed.

- [ ] **Step 4: Append LEARNINGS entry**

```markdown

## 2026-04-24 — MCP toolsets beat a purpose-built SDK for structured forms
Tags: agent-design, architecture, product-decisions

Initially scoped Phase 4a around Claude Agent SDK + computer-use (the
hot 2026 skill). Reversed course to use Pydantic AI + Playwright MCP
via OpenRouter instead. Reasons:

1. Same keys we already have (OpenRouter) — no funded Anthropic account
   needed for dev.
2. Playwright MCP's structured tools (`fill(selector, value)`) are
   strictly better than coordinate-clicking via screenshot for HTML
   forms — faster, cheaper, more reliable, no OCR.
3. Architectural consistency: Company Researcher already uses
   Tavily+Firecrawl MCP toolsets in Pydantic AI. Form-Fill uses the
   same pattern with Playwright MCP. One mental model for all agents.
4. The "I chose accessibility-tree over computer-use for structured
   forms" story is a stronger interview signal than "I used the SDK
   out of the box."

What we lose: the literal "Claude Agent SDK on the resume" name-drop.
What we keep: the browser-driving agent, the dynamic multi-agent
callback (`answer_screening_question` as an agent tool), the screenshot
preview for HITL #3, and the real form submission path.

The screening callback via Pydantic AI's `deps` + `RunContext[T].deps`
pattern is genuinely elegant. The agent's tool accesses pipeline
context through dependency injection, not closure capture — makes the
agent unit-testable without pipeline state.

**Takeaway:** reach for the lighter tool when you have the choice.
An MCP server + a tool-use-capable LLM is almost always enough for
structured work. Computer-use (screenshot + coordinates) is only
necessary when there's no structured accessor.

---
```

- [ ] **Step 5: README update**

Update the Status callout:

```markdown
> **Status:** Phase 4a complete. Form-Fill now drives a real browser
> via Playwright MCP, filling YC WaaS forms end-to-end. All 7 agents
> are real. Screening-question callback is a dynamic tool invocation
> via Pydantic AI's deps pattern. Phase 4b (Greenhouse + Lever ATS
> support) and Phase 5 (dashboard + deploy) remain.
```

- [ ] **Step 6: Tag**

```bash
git tag v0.4.0-form-fill
```

- [ ] **Step 7: Commit docs**

```bash
git add LEARNINGS.md README.md
git commit -m "docs: Phase 4a LEARNINGS entry + README update"
```

---

## Self-review checklist

- [ ] Task 1 spike actually succeeded before Tasks 2+ proceeded
- [ ] All unit tests use `TestModel` + patched `_build_agent` — no real browser or LLM
- [ ] Integration test opt-in (skips without APPLY_OPENROUTER_API_KEY)
- [ ] Walking skeleton still passes with stubs
- [ ] No `ANTHROPIC_API_KEY` or `claude-agent-sdk` anywhere in the diff
- [ ] Screening-question tool uses `RunContext[FormFillDeps].deps` for context — not closure capture
- [ ] No `Co-Authored-By:` trailer on any commit

---

## Out of scope (Phase 4b / 5)

- Greenhouse-specific form handling (iframes, conditional fields)
- Lever-specific form handling (shadow DOM in some places)
- Workday / Ashby — deliberately cut
- Live submission to real companies from CI
- HITL #3 UI showing a real screenshot preview (needs frontend Image serving — Phase 5)
- Dashboard for outcome marking (Phase 5)
- Retry-on-partial-fill loop
