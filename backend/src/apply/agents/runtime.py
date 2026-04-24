"""Runtime switch: routes agent calls to real or stub implementations
based on the `APPLY_USE_REAL_AGENTS` flag.
"""
from apply.agents.company_researcher import company_researcher_stub as _cr_stub
from apply.agents.company_researcher_real import (
    company_researcher_real as _company_researcher_real,
)
from apply.agents.cover_letter_writer import cover_letter_writer_stub as _cl_stub
from apply.agents.cover_letter_writer_real import (
    cover_letter_writer_real as _cover_letter_real,
)
from apply.agents.fit_analyst import fit_analyst_stub as _fa_stub
from apply.agents.fit_analyst_real import fit_analyst_real as _fit_analyst_real
from apply.agents.form_context import FormFillDeps
from apply.agents.form_fill import FormFillResult
from apply.agents.form_fill import form_fill_stub as _ff_stub
from apply.agents.form_fill_real import form_fill_real as _form_fill_real
from apply.agents.intake import intake_stub as _intake_stub
from apply.agents.intake_real import intake_real as _intake_real
from apply.agents.memory_curator import memory_curator_stub as _mc_stub
from apply.agents.memory_curator_real import memory_curator_real as _memory_curator_real
from apply.agents.screening_answerer import screening_answerer_stub as _sa_stub
from apply.agents.screening_answerer_real import (
    screening_answerer_real as _screening_answerer_real,
)
from apply.config import get_settings
from apply.schemas.company import CompanyResearch
from apply.schemas.enums import ScreeningAnswerOrigin
from apply.schemas.fit import FitAnalysis
from apply.schemas.job import JobListing
from apply.schemas.writing import CoverLetter, ScreeningAnswer


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


async def cover_letter_writer(
    application_id: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
) -> CoverLetter:
    if _use_real():
        return await _cover_letter_real(
            application_id=application_id,
            company_name=company_name,
            company_brief=company_brief,
            jd_markdown=jd_markdown,
            corpus_resume_markdown=corpus_resume_markdown,
            corpus_voice_samples=corpus_voice_samples,
        )
    return await _cl_stub(application_id=application_id, company_name=company_name)


async def screening_answerer(
    question: str,
    company_name: str,
    company_brief: str,
    jd_markdown: str,
    corpus_resume_markdown: str,
    corpus_voice_samples: list[str],
    origin: ScreeningAnswerOrigin,
) -> ScreeningAnswer:
    if _use_real():
        return await _screening_answerer_real(
            question=question,
            company_name=company_name,
            company_brief=company_brief,
            jd_markdown=jd_markdown,
            corpus_resume_markdown=corpus_resume_markdown,
            corpus_voice_samples=corpus_voice_samples,
            origin=origin,
        )
    return await _sa_stub(question=question, origin=origin)


async def memory_curator(
    application_id: str,
    status: str = "SUBMITTED",
    company_name: str | None = None,
    jd_url: str | None = None,
    cover_letter_text: str | None = None,
) -> dict:
    if _use_real():
        return await _memory_curator_real(
            application_id=application_id,
            status=status,
            company_name=company_name,
            jd_url=jd_url,
            cover_letter_text=cover_letter_text,
        )
    return await _mc_stub(application_id=application_id)


async def form_fill(deps: FormFillDeps) -> FormFillResult:
    if _use_real():
        return await _form_fill_real(deps=deps)
    return await _ff_stub(
        application_url=deps.application_url,
        cover_letter_body=deps.cover_letter_text,
    )
