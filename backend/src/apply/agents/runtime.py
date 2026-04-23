"""Runtime switch: routes agent calls to real or stub implementations
based on the `APPLY_USE_REAL_AGENTS` flag.

The orchestrator always calls functions from this module. Whether they
execute stubs or real LLM-backed agents is a config decision, not a
code-path decision.
"""
from apply.agents.company_researcher import company_researcher_stub as _cr_stub
from apply.agents.company_researcher_real import (
    company_researcher_real as _company_researcher_real,
)
from apply.agents.fit_analyst import fit_analyst_stub as _fa_stub
from apply.agents.fit_analyst_real import fit_analyst_real as _fit_analyst_real
from apply.agents.intake import intake_stub as _intake_stub
from apply.agents.intake_real import intake_real as _intake_real
from apply.config import get_settings
from apply.schemas.company import CompanyResearch
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing


def _use_real() -> bool:
    return get_settings().apply_use_real_agents


async def intake(url: str, jd_text: str, raw_html_path: str) -> JobListing:
    if _use_real():
        return await _intake_real(url=url, jd_text=jd_text, raw_html_path=raw_html_path)
    return await _intake_stub(url=url)


async def company_researcher(company_name: str) -> CompanyResearch:
    if _use_real():
        return await _company_researcher_real(company_name=company_name)
    return await _cr_stub(company_name=company_name)


async def fit_analyst(
    resume_markdown: str,
    jd_markdown: str,
    company_brief: str,
) -> FitAnalysis:
    if _use_real():
        return await _fit_analyst_real(
            resume_markdown=resume_markdown,
            jd_markdown=jd_markdown,
            company_brief=company_brief,
        )
    # Stub signature differs — adapt
    return await _fa_stub(job_listing_id="job-stub", resume_markdown=resume_markdown)
