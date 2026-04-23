import pytest
from pydantic_ai.models.test import TestModel

from apply.agents import fit_analyst_real as fit_analyst_mod
from apply.agents.fit_analyst_real import fit_analyst_real
from apply.schemas.fit import FitAnalysis


@pytest.mark.asyncio
async def test_fit_analyst_real_returns_valid_analysis():
    test_model = TestModel(
        custom_output_args={
            "overall_score": 74,
            "verdict": "MODERATE",
            "matches": [
                {
                    "dimension": "Python",
                    "evidence_resume": "5 years Python as primary",
                    "evidence_jd": "5+ years Python required",
                    "strength": "strong",
                }
            ],
            "stretches": [],
            "gaps": [],
            "reasoning": "Strong language match, plausible stretch on MCP familiarity.",
            "recommended_action": "PROCEED",
        }
    )

    resume_md = "Senior Python engineer with 5 years of async systems experience."
    jd_md = "Founding Engineer. 5+ years Python. Experience with LLMs preferred."
    company_brief = "Acme AI — Series A, building long-running agents."

    with fit_analyst_mod._agent.override(model=test_model):
        result = await fit_analyst_real(
            resume_markdown=resume_md,
            jd_markdown=jd_md,
            company_brief=company_brief,
        )

    assert isinstance(result, FitAnalysis)
    assert 0 <= result.overall_score <= 100
    assert result.verdict in {"STRONG", "MODERATE", "STRETCH", "WEAK"}
    assert result.recommended_action in {"PROCEED", "PROCEED_WITH_CAUTION", "SKIP"}
    assert result.reasoning
