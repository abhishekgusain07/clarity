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
