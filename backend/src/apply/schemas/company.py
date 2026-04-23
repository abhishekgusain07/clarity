from pydantic import BaseModel, Field, HttpUrl


class Round(BaseModel):
    stage: str
    amount_usd: int | None = None
    date_iso: str | None = None


class Founder(BaseModel):
    name: str
    background: str | None = None
    linkedin_url: HttpUrl | None = None


class NewsItem(BaseModel):
    title: str
    url: HttpUrl
    date_iso: str | None = None
    summary: str | None = None


class BlogPost(BaseModel):
    title: str
    url: HttpUrl
    summary: str | None = None


class Source(BaseModel):
    url: HttpUrl
    title: str
    trust_score: float = Field(ge=0.0, le=1.0)


class CompanyResearch(BaseModel):
    company_name: str
    funding_stage: str | None = None
    last_round: Round | None = None
    team_size: str | None = None
    founders: list[Founder]
    recent_news: list[NewsItem]
    recent_blog_posts: list[BlogPost]
    tech_stack_hints: list[str]
    signal_score: float = Field(ge=0.0, le=1.0)
    sources: list[Source]
