from apply.schemas.enums import FitStrength, FitVerdict, RecommendedAction
from apply.schemas.fit import FitAnalysis, FitPoint


async def fit_analyst_stub(job_listing_id: str, resume_markdown: str) -> FitAnalysis:
    """Phase 1 stub: returns a hand-crafted MODERATE fit."""
    return FitAnalysis(
        overall_score=72,
        verdict=FitVerdict.MODERATE,
        matches=[
            FitPoint(
                dimension="Python proficiency",
                evidence_resume="5 years of Python as primary language",
                evidence_jd="5+ years Python",
                strength=FitStrength.STRONG,
            ),
            FitPoint(
                dimension="Async systems",
                evidence_resume="Built async data pipelines",
                evidence_jd="Comfort with async systems",
                strength=FitStrength.STRONG,
            ),
        ],
        stretches=[
            FitPoint(
                dimension="LLM agent frameworks",
                evidence_resume="Shipped one RAG prototype",
                evidence_jd="Experience with LLMs and agent frameworks",
                strength=FitStrength.MODERATE,
            ),
        ],
        gaps=[
            FitPoint(
                dimension="MCP / Claude Agent SDK",
                evidence_resume=None,
                evidence_jd="Experience with MCP or Claude Agent SDK",
                strength=FitStrength.WEAK,
            ),
        ],
        reasoning=(
            "Candidate has strong Python + async foundations. Weak on the "
            "specific agent-SDK requirements, but the project being built "
            "would directly address this gap — worth proceeding with a "
            "cover letter that frames the gap as the motivation."
        ),
        recommended_action=RecommendedAction.PROCEED,
    )
