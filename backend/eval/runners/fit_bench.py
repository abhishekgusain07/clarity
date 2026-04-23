"""Fit Analyst bench runner.

Scores FitAnalysis outputs against expert-labeled fit pairs.

Metrics:
- per-pair score_delta (predicted - expert)
- within_tolerance: |delta| <= 15 points
- verdict_match, action_match
- aggregate Pearson correlation across all pairs
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scipy.stats import pearsonr

from apply.schemas.fit import FitAnalysis


@dataclass
class FitBenchResult:
    resume_id: str
    jd_id: str
    expert_score: int
    predicted_score: int
    score_delta: int
    within_tolerance: bool
    verdict_match: bool
    action_match: bool
    expected_verdict: str
    predicted_verdict: str
    expected_action: str
    predicted_action: str


@dataclass
class FitCorrelationStats:
    n: int
    pearson_r: float | None
    pearson_p: float | None
    mean_abs_delta: float | None
    pct_within_tolerance: float | None


def score_fit_pair(expected: dict[str, Any], analysis: FitAnalysis) -> FitBenchResult:
    predicted_score = analysis.overall_score
    expert_score = int(expected["expert_score"])
    delta = predicted_score - expert_score
    return FitBenchResult(
        resume_id=expected.get("resume_id", ""),
        jd_id=expected.get("jd_id", ""),
        expert_score=expert_score,
        predicted_score=predicted_score,
        score_delta=delta,
        within_tolerance=abs(delta) <= 15,
        verdict_match=analysis.verdict.value == expected["expected_verdict"],
        action_match=analysis.recommended_action.value == expected["expected_action"],
        expected_verdict=expected["expected_verdict"],
        predicted_verdict=analysis.verdict.value,
        expected_action=expected["expected_action"],
        predicted_action=analysis.recommended_action.value,
    )


def compute_fit_correlation(
    expert_scores: list[int],
    predicted_scores: list[int],
) -> FitCorrelationStats:
    n = len(expert_scores)
    if n < 3:
        return FitCorrelationStats(
            n=n, pearson_r=None, pearson_p=None, mean_abs_delta=None, pct_within_tolerance=None,
        )
    r, p = pearsonr(expert_scores, predicted_scores)
    deltas = [abs(e - p) for e, p in zip(expert_scores, predicted_scores, strict=True)]
    return FitCorrelationStats(
        n=n,
        pearson_r=float(r),
        pearson_p=float(p),
        mean_abs_delta=sum(deltas) / len(deltas),
        pct_within_tolerance=sum(1 for d in deltas if d <= 15) / len(deltas),
    )


async def run_fit_bench(
    jds_path: Path,
    resumes_path: Path,
    fit_pairs_path: Path,
    fit_fn,
    company_brief_fn,
) -> tuple[list[FitBenchResult], FitCorrelationStats]:
    """Run the fit bench.

    fit_fn: async callable(resume_markdown, jd_markdown, company_brief) -> FitAnalysis
    company_brief_fn: async callable(jd_id, company_name) -> str (one-line brief)
    """
    jds = {item["id"]: item for item in json.loads(jds_path.read_text())["items"]}
    resumes = {item["id"]: item for item in json.loads(resumes_path.read_text())["items"]}
    pairs = json.loads(fit_pairs_path.read_text())["items"]

    results: list[FitBenchResult] = []
    for pair in pairs:
        resume = resumes[pair["resume_id"]]
        jd = jds[pair["jd_id"]]
        expected_company = jd.get("expected_fields", {}).get("company_name") or "the company"
        brief = await company_brief_fn(jd_id=pair["jd_id"], company_name=expected_company)

        analysis = await fit_fn(
            resume_markdown=resume["markdown"],
            jd_markdown=f"Role: {jd['expected_fields'].get('role_title', 'Unknown')}\nSource: {jd['expected_fields'].get('source', 'UNKNOWN')}\n(live JD text was fetched at run time)",
            company_brief=brief,
        )
        pair_with_ids = {**pair, "resume_id": pair["resume_id"], "jd_id": pair["jd_id"]}
        r = score_fit_pair(expected=pair_with_ids, analysis=analysis)
        results.append(r)

    stats = compute_fit_correlation(
        expert_scores=[r.expert_score for r in results],
        predicted_scores=[r.predicted_score for r in results],
    )
    return results, stats
