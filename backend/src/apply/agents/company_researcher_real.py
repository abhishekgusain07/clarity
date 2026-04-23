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
        toolsets=[tavily_mcp(), firecrawl_mcp()],
        retries=2,
    )


async def company_researcher_real(company_name: str) -> CompanyResearch:
    """Research a company using Tavily + Firecrawl MCP, return structured output."""
    agent = _build_agent()
    user_prompt = f"Research the company: {company_name}"
    async with agent:
        result = await agent.run(user_prompt)
    return result.output
