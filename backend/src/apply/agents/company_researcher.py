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
