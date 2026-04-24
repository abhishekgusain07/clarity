"""Cover letter bench: generates S (full pipeline) and B1 (Claude-one-shot) on the
goldenset, judges both, returns a comparison table.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from apply.agents.cover_letter_baseline import generate_baseline_b1
from apply.agents.cover_letter_judge import JudgeScores, judge_cover_letter
from apply.agents.runtime import cover_letter_writer
from apply.schemas.writing import CoverLetter


@dataclass
class CoverLetterBenchRow:
    jd_id: str
    company_name: str
    s_scores: JudgeScores
    b1_scores: JudgeScores
    s_body: str
    b1_body: str


@dataclass
class CoverLetterBenchSummary:
    rows: list[CoverLetterBenchRow] = field(default_factory=list)

    def mean_delta(self, dim: str) -> float:
        if not self.rows:
            return 0.0
        deltas = [getattr(r.s_scores, dim) - getattr(r.b1_scores, dim) for r in self.rows]
        return sum(deltas) / len(deltas)


async def run_cover_letter_bench(
    jds_path: Path,
    resumes_path: Path,
    voice_samples: list[str],
    jd_fetch_fn,
    company_research_fn,
) -> CoverLetterBenchSummary:
    jds = json.loads(jds_path.read_text())["items"]
    resumes = json.loads(resumes_path.read_text())["items"]
    resume_md = resumes[0]["markdown"]  # use first resume for all pairs

    summary = CoverLetterBenchSummary()

    for jd in jds:
        expected_company = jd.get("expected_fields", {}).get("company_name") or "the company"
        if expected_company == "FILL_AT_RUN_TIME":
            continue

        jd_text = await jd_fetch_fn(jd["url"])
        if not jd_text:
            continue

        research_summary = await company_research_fn(company_name=expected_company)

        # Full Apply pipeline cover letter
        s_letter = await cover_letter_writer(
            application_id=f"bench-s-{jd['id']}",
            company_name=expected_company,
            company_brief=research_summary,
            jd_markdown=jd_text,
            corpus_resume_markdown=resume_md,
            corpus_voice_samples=voice_samples,
        )

        # B1 baseline
        b1_body = await generate_baseline_b1(resume_markdown=resume_md, jd_markdown=jd_text)
        b1_letter = CoverLetter(
            id=f"bench-b1-{jd['id']}",
            application_id=f"bench-b1-{jd['id']}",
            draft_version=1,
            body_markdown=b1_body,
            word_count=len(b1_body.split()),
            references_company_specifics=[],
            voice_similarity_score=0.5,
            created_at=s_letter.created_at,
        )

        # Judge both
        s_scores = await judge_cover_letter(
            letter=s_letter,
            company_research_summary=research_summary,
            voice_samples=voice_samples,
        )
        b1_scores = await judge_cover_letter(
            letter=b1_letter,
            company_research_summary=research_summary,
            voice_samples=voice_samples,
        )

        summary.rows.append(
            CoverLetterBenchRow(
                jd_id=jd["id"],
                company_name=expected_company,
                s_scores=s_scores,
                b1_scores=b1_scores,
                s_body=s_letter.body_markdown,
                b1_body=b1_body,
            )
        )

    return summary
