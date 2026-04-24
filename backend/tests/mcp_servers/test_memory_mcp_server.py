import asyncio
import inspect
from unittest.mock import MagicMock

from apply.mcp_servers.memory_mcp.server import build_server


def _collect_tool_names(server) -> set[str]:
    """Pull the registered tool names out of a FastMCP server, across versions.

    FastMCP 3.x exposes `list_tools()` as an async coroutine returning
    `FunctionTool` objects with a `.name` attribute. Older versions may
    expose a sync iterable or an internal `_tools` mapping. The intent
    is the same regardless: get the names of the registered tools.
    """
    if hasattr(server, "list_tools"):
        result = server.list_tools()
        if inspect.iscoroutine(result):
            result = asyncio.new_event_loop().run_until_complete(result)
        return {getattr(t, "name", None) or getattr(t, "__name__", "") for t in result}
    if hasattr(server, "_tool_manager") and hasattr(server._tool_manager, "_tools"):
        return set(server._tool_manager._tools.keys())
    return set(getattr(server, "_tools", {}).keys())


def test_build_server_registers_three_tools():
    # Use a MagicMock store — we're only verifying tools register
    store = MagicMock()
    server = build_server(store=store)

    tool_names = _collect_tool_names(server)

    assert {"already_applied", "similar_applications", "what_landed_replies"} <= tool_names
