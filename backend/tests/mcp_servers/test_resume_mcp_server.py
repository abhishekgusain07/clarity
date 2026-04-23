import asyncio
import inspect
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


def _collect_tool_names(server) -> set[str]:
    """Pull the registered tool names out of a FastMCP server, across versions.

    FastMCP 3.x exposes `list_tools()` as an async coroutine returning
    `FunctionTool` objects with a `.name` attribute. Older versions may
    expose a sync iterable or an internal `_tools` mapping. The intent
    is the same regardless: get the names of the registered tools.
    """
    # Preferred: list_tools() — async in FastMCP 3.x
    if hasattr(server, "list_tools"):
        result = server.list_tools()
        if inspect.iscoroutine(result):
            result = asyncio.new_event_loop().run_until_complete(result)
        return {getattr(t, "name", None) or getattr(t, "__name__", "") for t in result}
    # Fallback: internal tool manager
    if hasattr(server, "_tool_manager") and hasattr(server._tool_manager, "_tools"):
        return set(server._tool_manager._tools.keys())
    # Last-resort fallback: scan internal _tools dict
    return set(getattr(server, "_tools", {}).keys())


def test_build_server_returns_server_with_four_tools(corpus):
    server = build_server(corpus=corpus)
    assert server is not None

    tool_names = _collect_tool_names(server)

    assert {"get_resume_markdown", "get_profile_field", "list_voice_samples",
            "find_voice_samples"} <= tool_names
