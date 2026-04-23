from unittest.mock import AsyncMock

import pytest

from apply.schemas.enums import JobSource, RemoteType
from apply.schemas.job import JobListing
from eval.runners.intake_bench import (
    IntakeBenchResult,
    score_intake_result,
)


def _fake_listing(**overrides):
    base = dict(
        id="job-bench",
        source=JobSource.YC_WAAS,
        url="https://www.workatastartup.com/jobs/1",
        application_url="https://www.workatastartup.com/jobs/1",
        company_name="Acme AI",
        role_title="Founding Engineer",
        location="San Francisco, CA",
        remote_type=RemoteType.HYBRID,
        description_markdown="…",
        requirements=["5+ yrs Python", "LLM experience", "Async systems"],
        nice_to_haves=["LangGraph"],
        raw_html_path="/tmp/bench.html",
    )
    base.update(overrides)
    return JobListing(**base)


def test_score_intake_result_all_fields_match():
    expected = {
        "source": "YC_WAAS",
        "company_name": "Acme AI",
        "role_title": "Founding Engineer",
        "location": "San Francisco, CA",
        "remote_type": "HYBRID",
        "min_requirements_count": 3,
        "min_nice_to_haves_count": 1,
    }
    listing = _fake_listing()

    result = score_intake_result(expected=expected, listing=listing)

    assert result.passed
    assert result.field_recall == 1.0
    assert result.field_hits >= 5


def test_score_intake_result_wrong_source():
    expected = {
        "source": "GREENHOUSE",
        "company_name": "Acme AI",
        "role_title": "Founding Engineer",
        "location": "San Francisco, CA",
        "remote_type": "HYBRID",
        "min_requirements_count": 3,
        "min_nice_to_haves_count": 1,
    }
    listing = _fake_listing()  # source=YC_WAAS

    result = score_intake_result(expected=expected, listing=listing)

    assert not result.passed
    assert result.field_recall < 1.0
    assert "source" in result.failed_fields


def test_score_intake_result_insufficient_requirements():
    expected = {
        "source": "YC_WAAS",
        "company_name": "Acme AI",
        "role_title": "Founding Engineer",
        "location": "San Francisco, CA",
        "remote_type": "HYBRID",
        "min_requirements_count": 5,  # agent only extracted 3
        "min_nice_to_haves_count": 0,
    }
    listing = _fake_listing()

    result = score_intake_result(expected=expected, listing=listing)

    assert not result.passed
    assert "requirements" in result.failed_fields


def test_fill_at_run_time_placeholder_skips_exact_match():
    expected = {
        "source": "YC_WAAS",
        "company_name": "FILL_AT_RUN_TIME",  # placeholder
        "role_title": "Founding Engineer",
        "location": "FILL_AT_RUN_TIME",
        "remote_type": "FILL_AT_RUN_TIME",
        "min_requirements_count": 3,
        "min_nice_to_haves_count": 0,
    }
    listing = _fake_listing()

    result = score_intake_result(expected=expected, listing=listing)

    # Placeholders don't count against or for the score
    assert result.passed
    # company_name / location / remote_type skipped; source + role + counts checked
    assert result.field_hits == 4  # source, role_title, req_count, nth_count
