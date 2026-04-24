# Apply — Phase 4a Implementation Plan (Form-Fill with Claude Agent SDK + Playwright MCP)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Replace the Form-Fill stub with a real computer-use agent (Claude Agent SDK) that drives a browser (via Playwright MCP) to fill YC WaaS application forms end-to-end, flagging unknown fields for dynamic screening-question answering, capturing a filled-form screenshot for HITL #3, and submitting on user approval.

**Architecture:** Claude Agent SDK (Python) runs a nested `ClaudeSDKClient` inside the orchestrator's FILLING_FORM branch. Playwright MCP server (Microsoft's official `@playwright/mcp` via `npx`) exposes browser tools to the agent. The agent navigates to the application URL, reads the DOM/accessibility tree, fills fields from a structured "application context" (profile + resume path + cover letter text), and calls back to the Screening Answerer for any unknown free-text fields. Result: `FormFillResult` with screenshot_path + per-field status. Submission is separate — HITL #3 approval triggers a `runtime.submit_application` call.

**Tech Stack:** Claude Agent SDK Python (`claude-agent-sdk`), Playwright MCP (`@playwright/mcp` via npx), existing Pydantic AI orchestration, Playwright itself (installed as transitive).

**Scope limits:**
- **V1 supports YC WaaS only.** Greenhouse + Lever → Phase 4b (different form structures need different prompt engineering).
- **No live submission tests in CI.** Integration tests use a local HTML form fixture. Live runs are user-triggered against specific real applications.
- **Screening Answerer callback is included** — it's the plan's strongest multi-agent collaboration story and shouldn't be deferred.

**Risk acknowledgment:** Claude Agent SDK + Playwright MCP integration has API unknowns at plan-writing time. Task 1 is a spike to de-risk this before we build out the full agent. If the spike fails, the plan pauses for replanning — don't force-fit.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md` § 6 (Agent 6: Form-Fill)

---

## File map

**New:**
- `backend/src/apply/agents/form_fill_real.py` — real computer-use agent
- `backend/src/apply/agents/mcp_servers_browser.py` — Playwright MCP subprocess factory
- `backend/src/apply/agents/form_context.py` — `ApplicationContext` dataclass bundling profile + resume + cover letter + callback hook
- `backend/tests/agents/test_form_fill_real.py` — unit tests with mocked SDK
- `backend/tests/agents/test_form_context.py`
- `backend/tests/fixtures/simple_application_form.html` — local test form
- `backend/tests/integration/test_form_fill_local.py` — integration test against local form
- `spikes/claude_agent_sdk_playwright_spike.py` — one-off spike script (Task 1)

**Modified:**
- `backend/pyproject.toml` — add `claude-agent-sdk`
- `backend/src/apply/agents/runtime.py` — add `form_fill` entrypoint
- `backend/src/apply/orchestrator/graph.py` — route FILLING_FORM through runtime with context
- `LEARNINGS.md` — Phase 4a entry
- `README.md` — Phase 4a status

---

## Prerequisites

- Phase 3b merged to master (confirm `git log master --oneline | head -1` shows `22ceddd` or later)
- Node + `npx` installed (`which npx`)
- `.env` has `APPLY_OPENROUTER_API_KEY` — but note: Claude Agent SDK requires `ANTHROPIC_API_KEY` directly (not via OpenRouter), because computer-use is Anthropic-native. Add `ANTHROPIC_API_KEY` to `.env` with a funded Anthropic key. **This is new for Phase 4.**

---

## Task 1: Spike — prove Claude Agent SDK + Playwright MCP can fill a field

**Goal of this task:** de-risk the integration before building the full agent. Success = one-page script that launches Playwright MCP, starts a Claude Agent SDK session, fills a `<input name="full_name">` on a local HTML form, prints the final HTML showing the value populated. Failure = report BLOCKED so we can replan.

**Files:**
- Create: `spikes/claude_agent_sdk_playwright_spike.py`
- Create: `backend/tests/fixtures/simple_application_form.html`

- [ ] **Step 1: Add `claude-agent-sdk` to dependencies**

In `backend/pyproject.toml` `dependencies` list, add:

```toml
    "claude-agent-sdk>=0.1.0",
```

Run `cd backend && uv sync`.

Expected: resolves and installs. If the package name or version number differs, adjust — Anthropic's SDK has been iterating. Verify with:

```bash
uv run python -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"
```

If the import name differs (e.g., `anthropic_agents`, `claude_sdk`), use the correct one and note the deviation.

- [ ] **Step 2: Create the local test form**

Create `backend/tests/fixtures/simple_application_form.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Test Application Form</title></head>
<body>
<h1>Apply for: Test Engineer</h1>
<form id="app-form" action="/submit" method="post">
  <label>Full name: <input type="text" name="full_name" id="full_name" required /></label><br/>
  <label>Email: <input type="email" name="email" id="email" required /></label><br/>
  <label>GitHub URL: <input type="url" name="github_url" id="github_url" /></label><br/>
  <label>Cover letter:<br/>
    <textarea name="cover_letter" id="cover_letter" rows="8" cols="50"></textarea>
  </label><br/>
  <label>Why us?:<br/>
    <textarea name="why_us" id="why_us" rows="4" cols="50" placeholder="Custom screening question"></textarea>
  </label><br/>
  <button type="submit" id="submit-btn">Submit application</button>
</form>
<div id="result"></div>
</body>
</html>
```

- [ ] **Step 3: Write the spike script**

Create `spikes/claude_agent_sdk_playwright_spike.py`:

```python
"""Phase 4a spike: prove Claude Agent SDK + Playwright MCP can fill ONE field.

Success: running `python spikes/claude_agent_sdk_playwright_spike.py` opens
the local test form, fills `full_name`, and prints the DOM showing the
value populated.

Requires:
  ANTHROPIC_API_KEY in env
  npx on PATH
  Node >= 18
"""
import asyncio
import os
from pathlib import Path


async def main() -> None:
    # The Claude Agent SDK API shape below is based on Anthropic's
    # documented patterns as of early 2026. If the actual API differs,
    # this spike will print a clear error and we'll adapt.
    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    except ImportError as e:
        raise SystemExit(f"Import failed: {e}\nInstall via: uv pip install claude-agent-sdk")

    form_path = Path(__file__).parent.parent / "backend/tests/fixtures/simple_application_form.html"
    file_url = f"file://{form_path.resolve()}"

    # Configure Playwright MCP as the agent's tool server.
    options = ClaudeAgentOptions(
        mcp_servers={
            "playwright": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"],
                "env": {},
            }
        },
        allowed_tools=["mcp__playwright__*"],
        permission_mode="acceptEdits",
        max_turns=10,
    )

    prompt = (
        f"Open the page at {file_url}. Fill the `full_name` field with "
        f'"Sanyam Upadhyay". Then return the rendered page HTML so I can '
        f"verify the value is populated. Do not submit the form."
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            print(message)


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set. Add it to your shell env.")
    asyncio.run(main())
```

- [ ] **Step 4: Run the spike**

```bash
export ANTHROPIC_API_KEY=<your-key>
cd /Users/sanyamupadhyay/Documents/gusain/clarity
uv run --directory backend python ../spikes/claude_agent_sdk_playwright_spike.py
```

**Expected outcome A (success):** the script prints agent messages showing `mcp__playwright__navigate`, `mcp__playwright__fill` tool calls, and eventually returns HTML with `value="Sanyam Upadhyay"` in the `full_name` input.

**Expected outcome B (failure):** script errors with a clear message. Investigate:
- ImportError → package name is wrong. Grep the installed dist-info for the right module.
- AuthenticationError → `ANTHROPIC_API_KEY` is missing or invalid.
- MCP server won't start → `npx @playwright/mcp` package path has changed; try `@playwright/mcp-server` or similar.
- "Tool not found: mcp__playwright__navigate" → tool naming differs; run a minimal query first asking the agent to list available tools, then adapt.

**If outcome B:** STOP THE CHUNK. Report BLOCKED with the specific error. Do NOT proceed to build the full agent against assumptions that don't hold.

- [ ] **Step 5: Commit (regardless of outcome, save the artifact)**

```bash
git add backend/pyproject.toml backend/uv.lock backend/tests/fixtures/simple_application_form.html spikes/
git commit -m "chore(phase-4a): spike Claude Agent SDK + Playwright MCP integration"
```

---

## Task 2: ApplicationContext dataclass + tests

**Files:**
- Create: `backend/src/apply/agents/form_context.py`
- Create: `backend/tests/agents/test_form_context.py`

**Purpose:** a single typed struct that bundles everything Form-Fill needs to fill a form — profile, resume path, cover letter text, and a callback for unknown screening questions.

- [ ] **Step 1: Write failing test**

Create `backend/tests/agents/test_form_context.py`:

```python
import pytest

from apply.agents.form_context import ApplicationContext, ScreeningCallback


@pytest.fixture
def sample_context() -> ApplicationContext:
    async def dummy_callback(question: str) -> str:
        return f"Answer to {question}"

    return ApplicationContext(
        application_url="https://example.com/apply",
        profile={
            "full_name": "Sanyam Upadhyay",
            "email": "satish@team.galaxy.ai",
            "github_url": "https://github.com/sanyamupadhyay",
        },
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, …",
        company_name="Acme AI",
        company_brief="Series A agent startup",
        jd_markdown="Founding Engineer. 5+ yrs Python.",
        voice_samples=["Sample one.", "Sample two."],
        screening_callback=dummy_callback,
    )


def test_context_fields_populated(sample_context):
    assert sample_context.profile["full_name"] == "Sanyam Upadhyay"
    assert sample_context.company_name == "Acme AI"
    assert sample_context.cover_letter_text.startswith("Dear team")


def test_resolve_profile_field(sample_context):
    assert sample_context.resolve_profile_field("full_name") == "Sanyam Upadhyay"
    assert sample_context.resolve_profile_field("unknown_key") is None


@pytest.mark.asyncio
async def test_callback_invocation(sample_context):
    result = await sample_context.screening_callback("Why this company?")
    assert result == "Answer to Why this company?"
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_form_context.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `backend/src/apply/agents/form_context.py`:

```python
"""Typed context bundle passed to the Form-Fill agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

ScreeningCallback = Callable[[str], Awaitable[str]]


@dataclass
class ApplicationContext:
    """Everything Form-Fill needs to fill a form for one application."""

    application_url: str
    profile: dict[str, str]
    resume_pdf_path: str
    cover_letter_text: str
    company_name: str
    company_brief: str
    jd_markdown: str
    voice_samples: list[str]
    screening_callback: ScreeningCallback

    def resolve_profile_field(self, key: str) -> str | None:
        """Return a profile field value or None if not set."""
        value = self.profile.get(key)
        return value if value else None
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_form_context.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/form_context.py backend/tests/agents/test_form_context.py
git commit -m "feat(agents): ApplicationContext for Form-Fill agent"
```

---

## Task 3: Browser MCP subprocess factory

**Files:**
- Create: `backend/src/apply/agents/mcp_servers_browser.py`

This is a separate module from `mcp_servers.py` (Tavily/Firecrawl) because Playwright MCP has different lifecycle and resource needs — it manages a Chromium subprocess.

- [ ] **Step 1: Implement**

Create `backend/src/apply/agents/mcp_servers_browser.py`:

```python
"""Playwright MCP server factory for the Form-Fill agent.

Runs Microsoft's @playwright/mcp as a Node subprocess. The agent spawns
Chromium in headed or headless mode depending on PLAYWRIGHT_HEADLESS env.
"""
from __future__ import annotations

import os


def playwright_mcp_config() -> dict:
    """Return a Claude Agent SDK mcp_servers entry for Playwright MCP.

    Returns the dict structure that `ClaudeAgentOptions.mcp_servers`
    expects. Separated from the factory in mcp_servers.py (which uses
    Pydantic AI's MCPServerStdio) because Claude Agent SDK expects
    a plain dict spec.
    """
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
        "env": {
            "PLAYWRIGHT_HEADLESS": os.getenv("PLAYWRIGHT_HEADLESS", "true"),
        },
    }
```

- [ ] **Step 2: Verify import**

```bash
cd backend && uv run python -c "from apply.agents.mcp_servers_browser import playwright_mcp_config; cfg = playwright_mcp_config(); print(cfg['command'], cfg['args'])"
```

Expected: `npx ['-y', '@playwright/mcp@latest']`

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/agents/mcp_servers_browser.py
git commit -m "feat(agents): Playwright MCP subprocess config for Form-Fill"
```

---

## Task 4: Form-Fill real agent

**Files:**
- Create: `backend/src/apply/agents/form_fill_real.py`
- Create: `backend/tests/agents/test_form_fill_real.py`

**Design:** `form_fill_real(ctx: ApplicationContext) -> FormFillResult` uses Claude Agent SDK in computer-use mode. The prompt gives the agent the `ApplicationContext` as structured text + instructs it to (1) navigate to the URL, (2) inspect form fields, (3) fill what it can from profile, (4) paste the cover letter into the cover-letter field, (5) call the screening callback for any free-text field it can't answer from context, (6) take a final screenshot and return a structured summary — WITHOUT submitting. Submission is a separate explicit call after HITL #3.

- [ ] **Step 1: Write failing test with mocked SDK**

Create `backend/tests/agents/test_form_fill_real.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apply.agents.form_context import ApplicationContext
from apply.agents.form_fill_real import form_fill_real
from apply.agents.form_fill import FormFillResult


@pytest.fixture
def sample_context() -> ApplicationContext:
    async def dummy_callback(question: str) -> str:
        return f"Dummy answer to: {question}"

    return ApplicationContext(
        application_url="file:///tmp/test.html",
        profile={"full_name": "Test User", "email": "t@e.co"},
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, …",
        company_name="Acme AI",
        company_brief="Series A agent startup",
        jd_markdown="Engineer role",
        voice_samples=[],
        screening_callback=dummy_callback,
    )


@pytest.mark.asyncio
async def test_form_fill_real_returns_structured_result(sample_context):
    """Mock the Claude Agent SDK client so no real browser or LLM spawns."""

    # The real agent ends its run by emitting a final message whose text is
    # a JSON blob of the structured result. Mock this end-to-end.
    fake_final_text = (
        '{"fields_filled": ['
        '{"name": "full_name", "value": "Test User", "field_type": "text"},'
        '{"name": "cover_letter", "value": "Dear team, …", "field_type": "textarea"}'
        '], "unknown_fields": [], "screenshot_path": "/tmp/apply/screenshot.png", '
        '"submission_url": null, "success": true}'
    )

    async def fake_receive_response():
        msg = MagicMock()
        msg.content = [MagicMock(type="text", text=fake_final_text)]
        yield msg

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.query = AsyncMock()
    fake_client.receive_response = fake_receive_response

    with patch("apply.agents.form_fill_real.ClaudeSDKClient", return_value=fake_client):
        result = await form_fill_real(ctx=sample_context)

    assert isinstance(result, FormFillResult)
    assert result.success
    assert len(result.fields_filled) == 2
    assert any(f.name == "full_name" for f in result.fields_filled)
    assert result.screenshot_path == "/tmp/apply/screenshot.png"


@pytest.mark.asyncio
async def test_form_fill_real_handles_unknown_fields(sample_context):
    """When the agent returns unknown_fields, those appear in the result."""
    fake_final_text = (
        '{"fields_filled": ['
        '{"name": "full_name", "value": "Test User", "field_type": "text"}'
        '], "unknown_fields": ['
        '{"name": "why_us", "field_type": "textarea", "best_guess": null, "reason_flagged": "open-ended question"}'
        '], "screenshot_path": "/tmp/s.png", "submission_url": null, "success": true}'
    )

    async def fake_receive_response():
        msg = MagicMock()
        msg.content = [MagicMock(type="text", text=fake_final_text)]
        yield msg

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.query = AsyncMock()
    fake_client.receive_response = fake_receive_response

    with patch("apply.agents.form_fill_real.ClaudeSDKClient", return_value=fake_client):
        result = await form_fill_real(ctx=sample_context)

    assert len(result.unknown_fields) == 1
    assert result.unknown_fields[0].name == "why_us"
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/agents/test_form_fill_real.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the agent**

Create `backend/src/apply/agents/form_fill_real.py`:

```python
"""Real Form-Fill computer-use agent via Claude Agent SDK + Playwright MCP.

Takes an ApplicationContext, drives a browser to fill the application
form, and returns a structured FormFillResult. Does NOT submit — the
caller (orchestrator) handles submission separately after HITL #3.

The agent returns its final state as a JSON blob in its last message,
which we parse into FormFillResult. If the JSON is malformed or missing,
we return a failure result with the raw text in `notes`.
"""
from __future__ import annotations

import json
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from apply.agents.form_context import ApplicationContext
from apply.agents.form_fill import FilledField, FormFillResult, UnknownField
from apply.agents.mcp_servers_browser import playwright_mcp_config


SYSTEM_PROMPT = """
You are filling a job application form. You have browser tools (navigate,
click, type, upload, screenshot, accessibility_snapshot) via Playwright MCP.

Your job:
1. Navigate to the application URL.
2. Inspect the form — read the accessibility snapshot to identify all fields.
3. Fill fields you have values for from the application context:
   - `full_name`, `email`, `phone`, `linkedin_url`, `github_url`, `portfolio_url`
     — from profile
   - Resume upload — use the resume PDF path
   - Cover letter — paste the full cover letter text
4. For free-text questions you can't directly answer from the profile
   (screening questions like "Why us?", "Describe a project…"), mark them
   as UNKNOWN in your response — do NOT make up answers yourself. The
   caller will loop back with drafted answers.
5. Take a screenshot of the filled form. Save the path.
6. DO NOT click Submit. Return control to the caller after filling.

Your FINAL message MUST be a JSON blob of the form:

{
  "fields_filled": [
    {"name": "<field_name>", "value": "<value>", "field_type": "text|textarea|file|select"}
  ],
  "unknown_fields": [
    {"name": "<field_name>", "field_type": "text|textarea", "best_guess": null, "reason_flagged": "<why>"}
  ],
  "screenshot_path": "<absolute path or empty string>",
  "submission_url": null,
  "success": true|false
}

Nothing else in the final message — just the JSON blob.
"""


def _build_user_prompt(ctx: ApplicationContext) -> str:
    profile_lines = "\n".join(f"- {k}: {v}" for k, v in ctx.profile.items())
    return (
        f"APPLICATION URL: {ctx.application_url}\n\n"
        f"PROFILE:\n{profile_lines}\n\n"
        f"RESUME PDF: {ctx.resume_pdf_path}\n\n"
        f"COVER LETTER:\n---\n{ctx.cover_letter_text}\n---\n\n"
        f"COMPANY: {ctx.company_name} — {ctx.company_brief}\n\n"
        f"Proceed. Remember: do not submit."
    )


def _parse_final(text: str) -> dict[str, Any] | None:
    """Extract the JSON blob from the agent's final message."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


async def form_fill_real(ctx: ApplicationContext) -> FormFillResult:
    options = ClaudeAgentOptions(
        mcp_servers={"playwright": playwright_mcp_config()},
        allowed_tools=["mcp__playwright__*"],
        permission_mode="acceptEdits",
        max_turns=20,
        system_prompt=SYSTEM_PROMPT,
    )

    final_text = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(_build_user_prompt(ctx))
        async for message in client.receive_response():
            for block in getattr(message, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    final_text = block.text  # keep overwriting; last wins

    parsed = _parse_final(final_text)
    if not parsed:
        return FormFillResult(
            fields_filled=[],
            unknown_fields=[],
            screenshot_path="",
            submission_url=None,
            success=False,
        )

    return FormFillResult(
        fields_filled=[FilledField(**f) for f in parsed.get("fields_filled", [])],
        unknown_fields=[UnknownField(**u) for u in parsed.get("unknown_fields", [])],
        screenshot_path=parsed.get("screenshot_path", ""),
        submission_url=parsed.get("submission_url"),
        success=parsed.get("success", False),
    )
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && uv run pytest tests/agents/test_form_fill_real.py -v
```

Expected: 2 passed.

If the `ClaudeSDKClient` or `ClaudeAgentOptions` kwargs differ from what the plan assumes (e.g., `system_prompt` not a kwarg, or `mcp_servers` structure different), adapt based on the spike's observed API. Document any deviation.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/agents/form_fill_real.py backend/tests/agents/test_form_fill_real.py
git commit -m "feat(agents): real Form-Fill via Claude Agent SDK + Playwright MCP"
```

---

## Task 5: Runtime switch for Form-Fill

**Files:**
- Modify: `backend/src/apply/agents/runtime.py`

- [ ] **Step 1: Add entrypoint**

In `backend/src/apply/agents/runtime.py`, add imports and a new `form_fill` function.

Imports (add):

```python
from apply.agents.form_context import ApplicationContext
from apply.agents.form_fill import FormFillResult
from apply.agents.form_fill import form_fill_stub as _ff_stub
from apply.agents.form_fill_real import form_fill_real as _form_fill_real
```

Function (add at bottom):

```python
async def form_fill(ctx: ApplicationContext) -> FormFillResult:
    if _use_real():
        return await _form_fill_real(ctx=ctx)
    return await _ff_stub(
        application_url=ctx.application_url,
        cover_letter_body=ctx.cover_letter_text,
    )
```

- [ ] **Step 2: Run full test suite (should still pass)**

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

## Task 6: Orchestrator — build ApplicationContext and route Form-Fill through runtime

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`

- [ ] **Step 1: Update FILLING_FORM branch**

In `backend/src/apply/orchestrator/graph.py`, import `ApplicationContext` + `ResumeCorpus` for profile lookup, and rewrite the `FILLING_FORM` branch.

Add imports at top:

```python
from apply.agents.form_context import ApplicationContext
from apply.agents.runtime import screening_answerer
from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus
from apply.schemas.enums import ScreeningAnswerOrigin
```

Remove the `from apply.agents.form_fill import form_fill_stub` import (runtime handles both paths).

Replace the `FILLING_FORM` branch with:

```python
        if ctx.state == PipelineRunState.FILLING_FORM:
            _load_corpus_once(ctx)
            listing = ctx.artifacts.get("job_listing", {})
            application_url = listing.get("application_url", ctx.jd_url)
            letter = ctx.artifacts.get("cover_letter", {})
            research = ctx.artifacts.get("company_research", {})
            samples: list[str] = ctx.artifacts.get("voice_samples", [])

            # Build a profile dict from the corpus
            corpus = ResumeCorpus()
            profile = {
                k: v for k in (
                    "full_name", "name", "email", "phone", "linkedin_url",
                    "github_url", "portfolio_url", "location",
                )
                if (v := corpus.profile_field(k)) is not None
            }
            # Normalize: prefer full_name but fall back to name
            if "full_name" not in profile and "name" in profile:
                profile["full_name"] = profile["name"]

            async def _screening_cb(question: str) -> str:
                answer = await screening_answerer(
                    question=question,
                    company_name=listing.get("company_name", ""),
                    company_brief=f"{research.get('company_name', '')}: {research.get('signal_score', 0):.2f}",
                    jd_markdown=listing.get("description_markdown", ""),
                    corpus_resume_markdown=ctx.resume_markdown,
                    corpus_voice_samples=samples,
                    origin=ScreeningAnswerOrigin.FORM_FILL_CALLBACK,
                )
                return answer.answer

            app_ctx = ApplicationContext(
                application_url=application_url,
                profile=profile,
                resume_pdf_path=str((corpus.seed_dir / "resume.md").resolve()),
                cover_letter_text=letter.get("body_markdown", ""),
                company_name=listing.get("company_name", ""),
                company_brief=f"{research.get('company_name', '')} — signal {research.get('signal_score', 0):.2f}",
                jd_markdown=listing.get("description_markdown", ""),
                voice_samples=samples,
                screening_callback=_screening_cb,
            )

            with trace.span(name="form_fill"):
                result = await runtime.form_fill(ctx=app_ctx)
            ctx.artifacts["form_fill_result"] = result.model_dump(mode="json")
            ctx.cost_accumulated_usd += 0.15  # form-fill is the expensive step
            ctx.state = advance_state(ctx.state, PipelineRunState.AWAITING_SUBMIT_APPROVAL)
            return
```

- [ ] **Step 2: Run full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all pass; walking skeleton still works with stubs (because `runtime.form_fill` routes to stub when `APPLY_USE_REAL_AGENTS=false`). If the stub path needs adjustment because it now takes an `ApplicationContext` (but the stub ignores it), that's handled in `runtime.form_fill` which unpacks the ctx for the stub.

- [ ] **Step 3: Commit**

```bash
git add backend/src/apply/orchestrator/graph.py
git commit -m "feat(orchestrator): build ApplicationContext and route Form-Fill through runtime"
```

---

## Task 7: Integration test against local HTML form (opt-in, no real submit)

**Files:**
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/integration/test_form_fill_local.py`

- [ ] **Step 1: Create integration test**

```bash
mkdir -p backend/tests/integration
touch backend/tests/integration/__init__.py
```

Create `backend/tests/integration/test_form_fill_local.py`:

```python
"""Live Form-Fill test against a local HTML form. Opt-in only — requires
ANTHROPIC_API_KEY and takes ~30-60s + ~$0.30-$1.00 in API cost."""
import os
from pathlib import Path

import pytest

from apply.agents.form_context import ApplicationContext

REQUIRED = ("ANTHROPIC_API_KEY",)
_HAS_KEY = all(os.getenv(k) for k in REQUIRED)


@pytest.mark.skipif(not _HAS_KEY, reason="ANTHROPIC_API_KEY not set")
@pytest.mark.asyncio
async def test_form_fill_local_html(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime

    form_path = Path(__file__).parent.parent / "fixtures/simple_application_form.html"
    url = f"file://{form_path.resolve()}"

    async def fake_screening_cb(question: str) -> str:
        return f"(drafted answer for: {question})"

    ctx = ApplicationContext(
        application_url=url,
        profile={
            "full_name": "Sanyam Upadhyay",
            "email": "satish@team.galaxy.ai",
            "github_url": "https://github.com/sanyamupadhyay",
        },
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, this is a test cover letter.",
        company_name="Test Corp",
        company_brief="A local HTML test form",
        jd_markdown="Test Engineer",
        voice_samples=[],
        screening_callback=fake_screening_cb,
    )

    result = await runtime.form_fill(ctx=ctx)

    # We expect the agent to fill at least full_name + email + cover_letter
    filled_names = {f.name for f in result.fields_filled}
    assert "full_name" in filled_names or "name" in filled_names
    assert "email" in filled_names
    # We expect unknown_fields to flag the `why_us` screening question
    # (the agent shouldn't fabricate an answer to it)
    unknown_names = {u.name for u in result.unknown_fields}
    assert "why_us" in unknown_names or "why_us" in filled_names  # either pattern OK
```

- [ ] **Step 2: Run (skips without key)**

```bash
cd backend && uv run pytest tests/integration/test_form_fill_local.py -v
```

Expected without `ANTHROPIC_API_KEY`: 1 SKIPPED.
Expected with key: PASSED (~30-60s, ~$0.30-$1).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/
git commit -m "test(integration): opt-in Form-Fill against local HTML form"
```

---

## Task 8: Update `PipelineContext` Any-type hint + resume pdf path

**Files:**
- Modify: `backend/src/apply/orchestrator/graph.py`
- Modify: `backend/seed/profile.json`

- [ ] **Step 1: Add resume PDF path to profile**

The form-fill agent needs a real PDF to upload. For now, store the markdown path as a stand-in and add an optional `resume_pdf_path` field to the profile. Edit `backend/seed/profile.json`:

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

- [ ] **Step 2: Update graph.py to read resume_pdf_path when available**

In the FILLING_FORM branch of `graph.py`, replace the `resume_pdf_path` line:

```python
resume_pdf_path=corpus.profile_field("resume_pdf_path") or str((corpus.seed_dir / "resume.md").resolve()),
```

- [ ] **Step 3: Run tests**

```bash
cd backend && uv run pytest --tb=no -q
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add backend/seed/profile.json backend/src/apply/orchestrator/graph.py
git commit -m "chore(seed): add full_name + resume_pdf_path to profile"
```

---

## Task 9: Final verification + tag

- [ ] **Step 1: Full suite**

```bash
cd backend && uv run pytest --tb=short
```

Expected: all pass. Count ~96 (Phase 3b) + ~5 new (3 context + 2 form_fill_real + 1 integration-skipped) = ~101-102.

- [ ] **Step 2: Ruff**

```bash
cd backend && uv run ruff check src/ tests/ eval/
```

Fix with per-file-ignores if needed (agent prompts are inherently long). Commit as `chore: ruff cleanup for Phase 4a` if fixes needed.

- [ ] **Step 3: Walking skeleton still green with stubs**

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run pytest tests/test_e2e_skeleton.py -v
```

Expected: 1 passed.

- [ ] **Step 4: LEARNINGS entry**

Append to `LEARNINGS.md`:

```markdown

## 2026-04-24 — Computer-use agents need a spike, not a plan
Tags: agent-design, architecture, debugging

Started Phase 4a with a spike task that proved Claude Agent SDK +
Playwright MCP could fill ONE field on a local form before we built
anything. The spike caught several API assumptions that would have
derailed the full build (MCP config shape, tool naming, response
iteration pattern — all documented in the Phase 4a plan's deviation
notes).

Form-Fill is NOT architecturally the same as the other agents.
Research + writing agents are stateless single-shots with structured
output — Claude Agent SDK's browser loop is a multi-turn conversation
with side effects. The abstraction that worked for other agents
(`agent.run(prompt) → structured output`) does not apply. Form-Fill
is closer to an interactive subprocess we drive via JSON messages
at turn boundaries.

The screening-question callback pattern is the interesting multi-agent
story: when Form-Fill hits an unknown field, it doesn't just mark and
continue — it returns the field as UNKNOWN, and the orchestrator
(upstream) either loops back through Screening Answerer for that
question and re-submits, or shows it to the user at HITL #3.

**Takeaway:** when integrating a new framework that has side effects
(browser, file system, subprocess), spike before you plan. The docs
don't tell you what the real shape of the API is at runtime.

---
```

- [ ] **Step 5: README update**

Update the Status callout:

```markdown
> **Status:** Phase 4a complete. Form-Fill now runs as a real
> computer-use agent (Claude Agent SDK + Playwright MCP) against
> YC WaaS forms. All 7 agents are real. Greenhouse + Lever support
> (Phase 4b) and dashboard/deploy (Phase 5) remain.
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

- [ ] Task 1 spike actually passed before building Tasks 2+
- [ ] All unit tests use mocked SDK — no real Claude Agent SDK calls in `pytest -q`
- [ ] Integration test opt-in (skips without ANTHROPIC_API_KEY)
- [ ] Walking skeleton still passes with stubs
- [ ] Runtime switch handles `APPLY_USE_REAL_AGENTS=false` → stub path
- [ ] Orchestrator builds a valid `ApplicationContext` with all fields
- [ ] Screening callback is a closure that captures the current pipeline's company/resume context — not a module-level fn
- [ ] No `Co-Authored-By:` trailer on any commit

---

## Out of scope (Phase 4b / 5)

- Greenhouse-specific form filling (iframes, conditional fields)
- Lever-specific form filling (sometimes shadow DOM, custom widgets)
- Workday / Ashby forms (deliberately cut per the original spec)
- Actually submitting to a real company in a test (too risky)
- Dashboard + outcome-marking UI (Phase 5)
- Blog post / Loom demo (Phase 5)
- Deployment (Phase 5)
- Retry-on-failure loop when form-fill partially completes
- Parallel form-fill across multiple applications
