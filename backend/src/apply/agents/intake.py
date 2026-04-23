import uuid

from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing


async def intake_stub(url: str) -> JobListing:
    """Phase 1 stub: returns a fixed fake JobListing regardless of URL."""
    return JobListing(
        id=f"job-{uuid.uuid4().hex[:8]}",
        source=JobSource.YC_WAAS,
        url=url,  # type: ignore[arg-type]
        application_url=url,  # type: ignore[arg-type]
        company_name="Acme AI",
        role_title="Founding Engineer",
        location="San Francisco, CA",
        remote_type=RemoteType.HYBRID,
        description_markdown=(
            "We're building agents that talk to enterprise software. "
            "Looking for someone who loves Python, multi-agent systems, "
            "and shipping fast."
        ),
        requirements=[
            "5+ years Python",
            "Experience with LLMs and agent frameworks",
            "Comfort with async systems",
        ],
        nice_to_haves=[
            "Published open-source work on agents",
            "Experience with MCP or Claude Agent SDK",
        ],
        compensation_range="$180k-$240k + equity",
        raw_html_path="/tmp/apply/stub-jd.html",
    )
