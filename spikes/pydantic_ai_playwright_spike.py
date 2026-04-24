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
        args=[
            "-y",
            "@playwright/mcp@latest",
            "--headless",
            # Playwright MCP blocks file:// navigation by default; our local
            # fixture needs this escape hatch. Real runs go to http(s) URLs.
            "--allow-unrestricted-file-access",
        ],
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
