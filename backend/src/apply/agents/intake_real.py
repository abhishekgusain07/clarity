"""Real Intake agent — parses a JD URL + text into a typed JobListing.

Uses Claude Haiku for cheap, deterministic structured extraction.
The caller is responsible for having already fetched the JD text
(Firecrawl, Tavily, or user paste); this agent does not scrape.
"""
import uuid

from pydantic_ai import Agent

from apply.agents.models import haiku
from apply.schemas.job import JobListing

SYSTEM_PROMPT = """
You are a job listing parser. Given a JD URL and its plaintext/markdown
content, extract a typed JobListing.

Guidance:
- `source`: infer from the URL hostname:
  * workatastartup.com → YC_WAAS
  * wellfound.com or angel.co → WELLFOUND
  * jobs.lever.co → LEVER
  * boards.greenhouse.io → GREENHOUSE
  * jobs.ashbyhq.com → ASHBY
  * myworkdayjobs.com → WORKDAY
  * otherwise → COMPANY_PAGE or OTHER
- `application_url`: if the JD contains an "Apply" button with a distinct
  URL, use it. Otherwise reuse the listing URL.
- `remote_type`: classify into REMOTE | HYBRID | ONSITE based on the
  location/work-style copy.
- `requirements`: hard requirements only. Short items (< 80 chars each).
- `nice_to_haves`: bonus/optional items.
- `compensation_range`: quote the text verbatim if present, else null.
- `description_markdown`: copy the JD content near-verbatim as Markdown.

Be precise. Do not invent facts. If a field is absent, leave it null.
"""


_agent = Agent(
    model=haiku(),
    output_type=JobListing,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
)


async def intake_real(url: str, jd_text: str, raw_html_path: str) -> JobListing:
    """Parse a JD URL + text into a typed JobListing via Claude Haiku."""
    user_prompt = (
        f"Listing URL: {url}\n"
        f"Generate id: job-{uuid.uuid4().hex[:8]}\n"
        f"Save raw HTML at: {raw_html_path}\n\n"
        f"JD content:\n---\n{jd_text}\n---"
    )
    result = await _agent.run(user_prompt)
    return result.output
