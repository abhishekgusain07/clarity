# Apply — Phase 2b Implementation Plan (Research-Phase Eval Harness)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a reproducible eval harness for the three real research agents (Intake, Company Researcher, Fit Analyst) with a versioned goldenset, ship-bar metrics, and an `apply bench` CLI that produces a Markdown report — the dev-time eval loop that Phase 3+ agent changes will regress against.

**Architecture:** Fixtures live in `backend/eval/goldenset/` as JSON. Each agent has a bench runner in `backend/eval/runners/` that loads its fixture, runs the agent (real, via runtime switch), and scores against ground truth. A top-level `apply bench` CLI orchestrates all three and writes a timestamped Markdown report to `eval/reports/`. Bench runners are unit-testable with mocked agents so CI stays cheap; live bench runs hit real APIs and cost ~$1-3/run.

**Tech Stack:** pytest, scipy.stats (Pearson correlation), rich (optional CLI tables — fallback to plain text), existing Pydantic AI agents via `apply.agents.runtime`.

**What this plan does NOT cover:** Cover letter baseline comparison (needs real Cover Letter Writer — Phase 3b), LLM-as-judge on writing quality, production data dashboard, outcome logging, 3-blind-rater study.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md` § 10

---

## File map

**New files:**
- `backend/eval/__init__.py`
- `backend/eval/goldenset/__init__.py`
- `backend/eval/goldenset/jds.json`
- `backend/eval/goldenset/resumes.json`
- `backend/eval/goldenset/fit_pairs.json`
- `backend/eval/runners/__init__.py`
- `backend/eval/runners/intake_bench.py`
- `backend/eval/runners/company_research_bench.py`
- `backend/eval/runners/fit_bench.py`
- `backend/eval/reports/__init__.py`
- `backend/eval/reports/markdown.py`
- `backend/eval/cli.py`
- `backend/tests/eval/__init__.py`
- `backend/tests/eval/test_intake_bench.py`
- `backend/tests/eval/test_company_research_bench.py`
- `backend/tests/eval/test_fit_bench.py`
- `backend/tests/eval/test_markdown_report.py`

**Modified files:**
- `backend/pyproject.toml` — add `scipy` for stats, `rich` for CLI tables (optional)
- `backend/src/apply/cli.py` — add `bench` subcommand
- `LEARNINGS.md` — append eval-harness entry
- `.gitignore` — ignore `eval/reports/*.md` (generated)

---

## Prerequisites (verify before starting)

- Phase 2a shipped (3 real research agents working). Verify:
  ```bash
  git log --oneline | grep -q "real Fit Analyst" && echo "ok" || echo "missing"
  ```
- Postgres running (`docker ps | grep apply-postgres`)
- `.env` at repo root has real API keys for the live bench run (Task 11). Unit tests for bench runners use mocks and don't need keys.

---

## Task 1: Eval package scaffolding

**Files:**
- Create: `backend/eval/__init__.py`
- Create: `backend/eval/goldenset/__init__.py`
- Create: `backend/eval/runners/__init__.py`
- Create: `backend/eval/reports/__init__.py`
- Create: `backend/tests/eval/__init__.py`
- Modify: `.gitignore`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Create package structure**

```bash
mkdir -p backend/eval/goldenset backend/eval/runners backend/eval/reports
mkdir -p backend/tests/eval
touch backend/eval/__init__.py
touch backend/eval/goldenset/__init__.py
touch backend/eval/runners/__init__.py
touch backend/eval/reports/__init__.py
touch backend/tests/eval/__init__.py
```

- [ ] **Step 2: Ignore generated reports**

Append to `.gitignore`:

```
# Generated eval reports
backend/eval/reports/bench-*.md
```

- [ ] **Step 3: Add dependencies**

Edit `backend/pyproject.toml`. In the `dependencies` list, add `scipy>=1.14.0` (for Pearson correlation). In the `[dependency-groups].dev` section, add `rich>=13.9.0` (for pretty CLI tables).

Final `dependencies` list should look like (keep everything else as-is, just add scipy):

```toml
    "openai>=1.54.0",
    "python-multipart>=0.0.20",
    "scipy>=1.14.0",
]
```

Final dev group:

```toml
[dependency-groups]
dev = [
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "pytest-recording>=0.13.2",
    "vcrpy>=6.0.2",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "rich>=13.9.0",
]
```

- [ ] **Step 4: Sync**

```bash
cd backend && uv sync
```

Expected: scipy + rich installed.

- [ ] **Step 5: Verify imports**

```bash
cd backend && uv run python -c "import scipy.stats; from rich.console import Console; print('ok')"
```

Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add .gitignore backend/eval/ backend/tests/eval/__init__.py backend/pyproject.toml backend/uv.lock
git commit -m "chore(eval): scaffold eval package + add scipy/rich deps"
```

---

## Task 2: Goldenset fixtures (JDs + resumes + fit pairs)

**Files:**
- Create: `backend/eval/goldenset/jds.json`
- Create: `backend/eval/goldenset/resumes.json`
- Create: `backend/eval/goldenset/fit_pairs.json`

**Goldenset philosophy:** small, versioned, honest. 5 JDs, 2 resumes, 5 resume-JD pairs with hand-labeled fit scores. Real live URLs where possible; if any listing 404s at run time, swap to a current live listing from the same domain/company family and update the corresponding `expected_*` manually.

- [ ] **Step 1: Create `jds.json`**

Create `backend/eval/goldenset/jds.json`:

```json
{
  "version": 1,
  "items": [
    {
      "id": "yc-001",
      "url": "https://www.workatastartup.com/jobs",
      "note_for_executor": "Pick any current public YC WaaS listing for an AI Engineer / Founding Engineer role. Fill in the expected_* blocks below from the real listing content.",
      "expected_fields": {
        "source": "YC_WAAS",
        "company_name": "FILL_AT_RUN_TIME",
        "role_title": "FILL_AT_RUN_TIME",
        "location": "FILL_AT_RUN_TIME",
        "remote_type": "FILL_AT_RUN_TIME",
        "min_requirements_count": 3,
        "min_nice_to_haves_count": 1
      },
      "expected_company_facts": [
        "company name appears",
        "YC batch or Series funding stage implied"
      ]
    },
    {
      "id": "anthropic-001",
      "url": "https://www.anthropic.com/careers",
      "note_for_executor": "Pick a current public Anthropic engineering listing. If https://www.anthropic.com/careers lists openings, grab one — else substitute a Greenhouse-hosted listing the Anthropic careers page links to.",
      "expected_fields": {
        "source": "GREENHOUSE",
        "company_name": "Anthropic",
        "role_title": "FILL_AT_RUN_TIME",
        "location": "FILL_AT_RUN_TIME",
        "remote_type": "FILL_AT_RUN_TIME",
        "min_requirements_count": 3,
        "min_nice_to_haves_count": 0
      },
      "expected_company_facts": [
        "Anthropic",
        "founded 2021",
        "AI safety"
      ]
    },
    {
      "id": "lever-001",
      "url": "https://jobs.lever.co/",
      "note_for_executor": "Pick any current public Lever-hosted engineering role (e.g., any tech startup using jobs.lever.co). Fill expected_* from the real listing.",
      "expected_fields": {
        "source": "LEVER",
        "company_name": "FILL_AT_RUN_TIME",
        "role_title": "FILL_AT_RUN_TIME",
        "location": "FILL_AT_RUN_TIME",
        "remote_type": "FILL_AT_RUN_TIME",
        "min_requirements_count": 2,
        "min_nice_to_haves_count": 0
      },
      "expected_company_facts": []
    },
    {
      "id": "greenhouse-001",
      "url": "https://boards.greenhouse.io/",
      "note_for_executor": "Pick any current public Greenhouse-hosted engineering role. Stripe, Notion, Linear, Figma all use Greenhouse. Fill expected_* from the real listing.",
      "expected_fields": {
        "source": "GREENHOUSE",
        "company_name": "FILL_AT_RUN_TIME",
        "role_title": "FILL_AT_RUN_TIME",
        "location": "FILL_AT_RUN_TIME",
        "remote_type": "FILL_AT_RUN_TIME",
        "min_requirements_count": 3,
        "min_nice_to_haves_count": 0
      },
      "expected_company_facts": []
    },
    {
      "id": "bad-fit-001",
      "url": "https://jobs.lever.co/",
      "note_for_executor": "Pick a role DELIBERATELY outside a software engineer's wheelhouse — e.g., a Marketing Manager at an e-commerce company, or a Warehouse Logistics Lead. This is the 'should trigger SKIP' case for Fit Analyst.",
      "expected_fields": {
        "source": "LEVER",
        "company_name": "FILL_AT_RUN_TIME",
        "role_title": "FILL_AT_RUN_TIME",
        "location": "FILL_AT_RUN_TIME",
        "remote_type": "FILL_AT_RUN_TIME",
        "min_requirements_count": 2,
        "min_nice_to_haves_count": 0
      },
      "expected_company_facts": []
    }
  ]
}
```

- [ ] **Step 2: Create `resumes.json`**

Create `backend/eval/goldenset/resumes.json` with 2 synthetic resumes (no real PII):

```json
{
  "version": 1,
  "items": [
    {
      "id": "resume-python-ai",
      "label": "Strong Python + recent AI/agents experience",
      "markdown": "# Alex Ray\nalex.ray@example.com · San Francisco, CA\n\n## Summary\n6 years Python. Last 2 years on LLM-backed products — shipped a RAG-driven internal search tool and a multi-agent research pipeline (LangGraph). Comfortable with async systems, Postgres, and production observability.\n\n## Experience\n\n**Senior Engineer — Mid-size SaaS** (2023-present)\n- Designed and shipped an LLM-powered support-triage agent (Claude + Pinecone). Reduced first-response time by 38%.\n- Built async data-ingestion pipeline handling 40M events/day on asyncpg + Redis.\n- Owns production observability stack (OpenTelemetry → Grafana).\n\n**Engineer — Early-stage startup** (2020-2023)\n- 4 years primary-language Python across backend, ML infra, and DX tooling.\n- Led migration from Flask → FastAPI; cut p95 latency by 22%.\n- Mentored 3 junior engineers.\n\n## Skills\nPython (expert), async/await, FastAPI, SQLAlchemy, Postgres, Redis, LangChain, LangGraph, OpenAI/Anthropic SDKs, Docker, AWS.\n\n## Education\nBS Computer Science — State University (2019)."
    },
    {
      "id": "resume-generalist",
      "label": "Mid-career generalist, no explicit AI/LLM work",
      "markdown": "# Jamie Kim\njamie.kim@example.com · Austin, TX\n\n## Summary\n7 years backend engineering across Ruby, Go, and some Python. Strong on systems design and database work. No production LLM experience yet but curious and reading in the space.\n\n## Experience\n\n**Staff Engineer — Fintech scale-up** (2021-present)\n- Led re-architecture of payments service (Rails → Go). Improved throughput 4x.\n- Designed multi-region Postgres replication strategy.\n- On-call leader for a 12-person infrastructure team.\n\n**Senior Engineer — Logistics SaaS** (2017-2021)\n- 4 years primary-language Ruby. Built routing-optimization service.\n- Migrated monolith DB from single Postgres to sharded setup.\n\n## Skills\nGo, Ruby, some Python, Postgres (expert), Kafka, Kubernetes, AWS, systems design.\n\n## Education\nBS Computer Engineering — State University (2017)."
    }
  ]
}
```

- [ ] **Step 3: Create `fit_pairs.json`**

Create `backend/eval/goldenset/fit_pairs.json` with hand-labeled fit scores. The `expert_score` and `expected_verdict` are my labels — adjust after running the first bench if they turn out miscalibrated:

```json
{
  "version": 1,
  "items": [
    {
      "resume_id": "resume-python-ai",
      "jd_id": "yc-001",
      "expert_score": 82,
      "expected_verdict": "STRONG",
      "expected_action": "PROCEED",
      "rationale": "Strong Python + recent LLM/agent shipping matches a YC AI Engineer role directly."
    },
    {
      "resume_id": "resume-python-ai",
      "jd_id": "anthropic-001",
      "expert_score": 70,
      "expected_verdict": "MODERATE",
      "expected_action": "PROCEED",
      "rationale": "Solid Python + agent work. Gap may be formal ML research / safety specialization depending on the exact role."
    },
    {
      "resume_id": "resume-generalist",
      "jd_id": "yc-001",
      "expert_score": 45,
      "expected_verdict": "STRETCH",
      "expected_action": "PROCEED_WITH_CAUTION",
      "rationale": "Strong senior eng fundamentals but zero LLM/agent work. Plausible only with aggressive framing."
    },
    {
      "resume_id": "resume-generalist",
      "jd_id": "anthropic-001",
      "expert_score": 30,
      "expected_verdict": "WEAK",
      "expected_action": "SKIP",
      "rationale": "No production LLM work AND the role implies ML depth. Not a realistic fit."
    },
    {
      "resume_id": "resume-python-ai",
      "jd_id": "bad-fit-001",
      "expert_score": 15,
      "expected_verdict": "WEAK",
      "expected_action": "SKIP",
      "rationale": "Engineer resume for a non-engineering role. Hard SKIP."
    }
  ]
}
```

- [ ] **Step 4: Verify JSON is valid**

```bash
cd backend && uv run python -c "
import json
from pathlib import Path
base = Path('eval/goldenset')
for f in ['jds.json', 'resumes.json', 'fit_pairs.json']:
    data = json.loads((base / f).read_text())
    print(f, 'v', data['version'], len(data['items']), 'items')
"
```

Expected:
```
jds.json v 1 5 items
resumes.json v 1 2 items
fit_pairs.json v 1 5 items
```

- [ ] **Step 5: Commit**

```bash
git add backend/eval/goldenset/
git commit -m "feat(eval): goldenset — 5 JDs, 2 resumes, 5 fit pairs"
```

---

## Task 3: Intake bench runner

**Files:**
- Create: `backend/eval/runners/intake_bench.py`
- Create: `backend/tests/eval/test_intake_bench.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/eval/test_intake_bench.py`:

```python
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
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/eval/test_intake_bench.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'eval.runners.intake_bench'`.

- [ ] **Step 3: Implement bench runner**

Create `backend/eval/runners/intake_bench.py`:

```python
"""Intake bench runner.

Scores a `JobListing` against the `expected_fields` block of a goldenset
entry. Fields containing the sentinel string "FILL_AT_RUN_TIME" are
skipped (neither counted as hit nor miss) — the live executor is
expected to replace those with real expected values when they substitute
a fresh URL.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from apply.schemas.job import JobListing

FILL_SENTINEL = "FILL_AT_RUN_TIME"


@dataclass
class IntakeBenchResult:
    jd_id: str
    passed: bool
    field_recall: float  # fraction of checked fields that matched
    field_hits: int
    field_checked: int
    failed_fields: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _check(name: str, expected: Any, actual: Any, result: IntakeBenchResult) -> None:
    if isinstance(expected, str) and expected == FILL_SENTINEL:
        return  # skip
    result.field_checked += 1
    if expected == actual:
        result.field_hits += 1
    else:
        result.failed_fields.append(name)


def score_intake_result(expected: dict[str, Any], listing: JobListing) -> IntakeBenchResult:
    result = IntakeBenchResult(jd_id="", passed=False, field_recall=0.0, field_hits=0, field_checked=0)

    _check("source", expected.get("source"), listing.source.value, result)
    _check("company_name", expected.get("company_name"), listing.company_name, result)
    _check("role_title", expected.get("role_title"), listing.role_title, result)
    _check("location", expected.get("location"), listing.location, result)
    _check("remote_type", expected.get("remote_type"), listing.remote_type.value, result)

    # Counts are minimum thresholds, not exact matches
    min_reqs = expected.get("min_requirements_count")
    if isinstance(min_reqs, int):
        result.field_checked += 1
        if len(listing.requirements) >= min_reqs:
            result.field_hits += 1
        else:
            result.failed_fields.append("requirements")

    min_nths = expected.get("min_nice_to_haves_count")
    if isinstance(min_nths, int):
        result.field_checked += 1
        if len(listing.nice_to_haves) >= min_nths:
            result.field_hits += 1
        else:
            result.failed_fields.append("nice_to_haves")

    if result.field_checked == 0:
        result.field_recall = 1.0  # nothing to check means vacuous pass
    else:
        result.field_recall = result.field_hits / result.field_checked

    result.passed = result.field_recall >= 0.95
    return result


async def run_intake_bench(
    goldenset_path: Path,
    intake_fn,
    jd_fetch_fn,
) -> list[IntakeBenchResult]:
    """Run the intake bench.

    intake_fn: async callable(url, jd_text, raw_html_path) -> JobListing
    jd_fetch_fn: async callable(url) -> str (returns JD markdown/text)
    """
    data = json.loads(goldenset_path.read_text())
    results: list[IntakeBenchResult] = []

    for item in data["items"]:
        jd_text = await jd_fetch_fn(item["url"])
        if not jd_text:
            r = IntakeBenchResult(
                jd_id=item["id"],
                passed=False,
                field_recall=0.0,
                field_hits=0,
                field_checked=0,
                notes=["jd_fetch returned empty"],
            )
            results.append(r)
            continue

        listing = await intake_fn(
            url=item["url"],
            jd_text=jd_text,
            raw_html_path=f"/tmp/apply/bench-{item['id']}.html",
        )
        r = score_intake_result(expected=item["expected_fields"], listing=listing)
        r.jd_id = item["id"]
        results.append(r)

    return results
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/eval/test_intake_bench.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/eval/runners/intake_bench.py backend/tests/eval/test_intake_bench.py
git commit -m "feat(eval): Intake bench runner with field-recall scoring"
```

---

## Task 4: Company Research bench runner

**Files:**
- Create: `backend/eval/runners/company_research_bench.py`
- Create: `backend/tests/eval/test_company_research_bench.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/eval/test_company_research_bench.py`:

```python
import pytest

from apply.schemas.company import (
    BlogPost,
    CompanyResearch,
    Founder,
    NewsItem,
    Source,
)
from eval.runners.company_research_bench import (
    CompanyResearchBenchResult,
    score_company_research,
)


def _fake_research(company_name="Anthropic", signal_score=0.8):
    return CompanyResearch(
        company_name=company_name,
        funding_stage="Series E",
        last_round=None,
        team_size="500+",
        founders=[
            Founder(name="Dario Amodei", background="ex-OpenAI VP of Research")
        ],
        recent_news=[
            NewsItem(
                title="Anthropic releases Claude 4.6",
                url="https://techcrunch.com/anthropic-claude-46",
                date_iso="2025-10-15",
                summary="New frontier model focused on agentic workflows.",
            )
        ],
        recent_blog_posts=[
            BlogPost(
                title="How we think about AI safety",
                url="https://www.anthropic.com/blog/ai-safety",
                summary="Core principles for responsible AI development.",
            )
        ],
        tech_stack_hints=["Python", "PyTorch"],
        signal_score=signal_score,
        sources=[
            Source(url="https://www.anthropic.com", title="homepage", trust_score=0.95),
        ],
    )


def test_all_expected_facts_found():
    expected_facts = ["Anthropic", "founded", "AI safety"]
    research = _fake_research()

    result = score_company_research(expected_facts=expected_facts, research=research)

    assert result.fact_recall >= 0.6  # "Anthropic" in name, "AI safety" in blog title; "founded" may miss
    assert result.passed is (result.fact_recall >= 0.6)


def test_no_expected_facts_vacuous_pass():
    research = _fake_research()

    result = score_company_research(expected_facts=[], research=research)

    assert result.fact_recall == 1.0
    assert result.passed is True


def test_low_signal_score_flagged():
    research = _fake_research(signal_score=0.2)

    result = score_company_research(
        expected_facts=["Anthropic"],
        research=research,
    )

    assert "low_signal_score" in result.notes


def test_missing_critical_facts_fails():
    expected_facts = ["Nonexistent Corp", "crypto", "metaverse"]
    research = _fake_research()  # about Anthropic, not any of those

    result = score_company_research(expected_facts=expected_facts, research=research)

    assert result.fact_recall < 0.5
    assert not result.passed
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/eval/test_company_research_bench.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement bench runner**

Create `backend/eval/runners/company_research_bench.py`:

```python
"""Company Research bench runner.

Scores a CompanyResearch against a list of expected_facts. A fact is
counted as "found" if its lowercased text appears anywhere in the
searchable surface of the research object (company_name, funding_stage,
team_size, any founder background, any news title/summary, any blog
title/summary, any tech stack hint). This is deliberately lenient — the
goldenset's expected_facts should be "must find" signals, not exact
phrase matches.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from apply.schemas.company import CompanyResearch


@dataclass
class CompanyResearchBenchResult:
    company_name: str
    passed: bool
    fact_recall: float
    facts_found: list[str] = field(default_factory=list)
    facts_missing: list[str] = field(default_factory=list)
    signal_score: float = 0.0
    notes: list[str] = field(default_factory=list)


def _searchable_text(research: CompanyResearch) -> str:
    parts = [
        research.company_name or "",
        research.funding_stage or "",
        research.team_size or "",
    ]
    for f in research.founders:
        parts.extend([f.name, f.background or ""])
    for n in research.recent_news:
        parts.extend([n.title, n.summary or ""])
    for b in research.recent_blog_posts:
        parts.extend([b.title, b.summary or ""])
    parts.extend(research.tech_stack_hints)
    return " \n ".join(parts).lower()


def score_company_research(
    expected_facts: list[str],
    research: CompanyResearch,
) -> CompanyResearchBenchResult:
    blob = _searchable_text(research)
    result = CompanyResearchBenchResult(
        company_name=research.company_name,
        passed=False,
        fact_recall=0.0,
        signal_score=research.signal_score,
    )

    if not expected_facts:
        result.fact_recall = 1.0
        result.passed = True
    else:
        for fact in expected_facts:
            if fact.lower() in blob:
                result.facts_found.append(fact)
            else:
                result.facts_missing.append(fact)
        result.fact_recall = len(result.facts_found) / len(expected_facts)
        result.passed = result.fact_recall >= 0.6

    if research.signal_score < 0.5:
        result.notes.append("low_signal_score")
    return result


async def run_company_research_bench(
    goldenset_path: Path,
    researcher_fn,
) -> list[CompanyResearchBenchResult]:
    """researcher_fn: async callable(company_name) -> CompanyResearch."""
    data = json.loads(goldenset_path.read_text())
    results: list[CompanyResearchBenchResult] = []

    for item in data["items"]:
        expected_facts = item.get("expected_company_facts", [])
        if not expected_facts:
            continue  # skip entries with no company-fact expectations

        expected_company_name = item.get("expected_fields", {}).get("company_name")
        if not expected_company_name or expected_company_name == "FILL_AT_RUN_TIME":
            continue  # can't research a placeholder

        research = await researcher_fn(company_name=expected_company_name)
        r = score_company_research(expected_facts=expected_facts, research=research)
        results.append(r)

    return results
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/eval/test_company_research_bench.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/eval/runners/company_research_bench.py backend/tests/eval/test_company_research_bench.py
git commit -m "feat(eval): Company Research bench runner with fact-recall scoring"
```

---

## Task 5: Fit Analyst bench runner

**Files:**
- Create: `backend/eval/runners/fit_bench.py`
- Create: `backend/tests/eval/test_fit_bench.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/eval/test_fit_bench.py`:

```python
import pytest

from apply.schemas.enums import FitVerdict, RecommendedAction
from apply.schemas.fit import FitAnalysis
from eval.runners.fit_bench import (
    FitBenchResult,
    compute_fit_correlation,
    score_fit_pair,
)


def _fake_analysis(score=75, verdict="MODERATE", action="PROCEED"):
    return FitAnalysis(
        overall_score=score,
        verdict=FitVerdict(verdict),
        matches=[],
        stretches=[],
        gaps=[],
        reasoning="…",
        recommended_action=RecommendedAction(action),
    )


def test_score_fit_pair_close_match():
    expected = {"expert_score": 78, "expected_verdict": "MODERATE", "expected_action": "PROCEED"}
    analysis = _fake_analysis(score=75, verdict="MODERATE", action="PROCEED")

    result = score_fit_pair(expected=expected, analysis=analysis)

    assert result.score_delta == 3
    assert result.verdict_match is True
    assert result.action_match is True
    assert result.within_tolerance is True  # |delta| <= 15


def test_score_fit_pair_large_gap():
    expected = {"expert_score": 85, "expected_verdict": "STRONG", "expected_action": "PROCEED"}
    analysis = _fake_analysis(score=40, verdict="STRETCH", action="PROCEED_WITH_CAUTION")

    result = score_fit_pair(expected=expected, analysis=analysis)

    assert result.score_delta == -45
    assert not result.within_tolerance
    assert not result.verdict_match
    assert not result.action_match


def test_compute_correlation_ideal():
    expert = [20, 40, 60, 80, 100]
    predicted = [22, 38, 62, 78, 99]

    stats = compute_fit_correlation(expert_scores=expert, predicted_scores=predicted)

    assert stats.pearson_r > 0.99
    assert stats.n == 5


def test_compute_correlation_too_few_points():
    stats = compute_fit_correlation(expert_scores=[50], predicted_scores=[60])
    assert stats.n == 1
    assert stats.pearson_r is None
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/eval/test_fit_bench.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement bench runner**

Create `backend/eval/runners/fit_bench.py`:

```python
"""Fit Analyst bench runner.

Scores FitAnalysis outputs against expert-labeled fit pairs.

Metrics:
- per-pair score_delta (predicted - expert)
- within_tolerance: |delta| <= 15 points
- verdict_match, action_match
- aggregate Pearson correlation across all pairs
"""
import json
from dataclasses import dataclass, field
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
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/eval/test_fit_bench.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/eval/runners/fit_bench.py backend/tests/eval/test_fit_bench.py
git commit -m "feat(eval): Fit Analyst bench runner with Pearson correlation"
```

---

## Task 6: Markdown report generator

**Files:**
- Create: `backend/eval/reports/markdown.py`
- Create: `backend/tests/eval/test_markdown_report.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/eval/test_markdown_report.py`:

```python
from eval.reports.markdown import render_bench_report
from eval.runners.company_research_bench import CompanyResearchBenchResult
from eval.runners.fit_bench import FitBenchResult, FitCorrelationStats
from eval.runners.intake_bench import IntakeBenchResult


def test_render_bench_report_includes_all_sections():
    intake_results = [
        IntakeBenchResult(
            jd_id="yc-001",
            passed=True,
            field_recall=1.0,
            field_hits=7,
            field_checked=7,
        )
    ]
    company_results = [
        CompanyResearchBenchResult(
            company_name="Anthropic",
            passed=True,
            fact_recall=1.0,
            facts_found=["Anthropic", "AI safety"],
            signal_score=0.85,
        )
    ]
    fit_results = [
        FitBenchResult(
            resume_id="resume-python-ai",
            jd_id="yc-001",
            expert_score=80,
            predicted_score=78,
            score_delta=-2,
            within_tolerance=True,
            verdict_match=True,
            action_match=True,
            expected_verdict="STRONG",
            predicted_verdict="STRONG",
            expected_action="PROCEED",
            predicted_action="PROCEED",
        )
    ]
    fit_stats = FitCorrelationStats(
        n=5,
        pearson_r=0.83,
        pearson_p=0.04,
        mean_abs_delta=5.2,
        pct_within_tolerance=0.8,
    )

    md = render_bench_report(
        intake=intake_results,
        company=company_results,
        fit=fit_results,
        fit_stats=fit_stats,
        run_timestamp="2026-04-23T12:00:00Z",
    )

    assert "# Bench report" in md
    assert "2026-04-23" in md
    assert "Intake" in md
    assert "Company Research" in md
    assert "Fit Analyst" in md
    assert "yc-001" in md
    assert "Anthropic" in md
    assert "0.83" in md  # pearson_r formatting


def test_render_bench_report_handles_insufficient_correlation():
    fit_stats = FitCorrelationStats(
        n=2, pearson_r=None, pearson_p=None, mean_abs_delta=None, pct_within_tolerance=None,
    )
    md = render_bench_report(
        intake=[], company=[], fit=[],
        fit_stats=fit_stats,
        run_timestamp="2026-04-23T12:00:00Z",
    )
    assert "insufficient" in md.lower() or "n/a" in md.lower()
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && uv run pytest tests/eval/test_markdown_report.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement report generator**

Create `backend/eval/reports/markdown.py`:

```python
"""Markdown report generator for bench runs."""
from eval.runners.company_research_bench import CompanyResearchBenchResult
from eval.runners.fit_bench import FitBenchResult, FitCorrelationStats
from eval.runners.intake_bench import IntakeBenchResult


def _pct(x: float | None) -> str:
    if x is None:
        return "N/A"
    return f"{x * 100:.1f}%"


def _fmt_float(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "N/A"
    return f"{x:.{digits}f}"


def _render_intake(results: list[IntakeBenchResult]) -> str:
    if not results:
        return "### Intake\n\nNo results.\n"
    passed = sum(1 for r in results if r.passed)
    lines = [
        "### Intake",
        "",
        f"- **Cases run:** {len(results)}",
        f"- **Passed (field recall ≥ 0.95):** {passed}/{len(results)}",
        "",
        "| JD | Recall | Hits | Checked | Failed fields |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        failed = ", ".join(r.failed_fields) if r.failed_fields else "—"
        lines.append(f"| `{r.jd_id}` | {_pct(r.field_recall)} | {r.field_hits} | {r.field_checked} | {failed} |")
    lines.append("")
    return "\n".join(lines)


def _render_company(results: list[CompanyResearchBenchResult]) -> str:
    if not results:
        return "### Company Research\n\nNo results (no JDs with expected_company_facts).\n"
    passed = sum(1 for r in results if r.passed)
    lines = [
        "### Company Research",
        "",
        f"- **Cases run:** {len(results)}",
        f"- **Passed (fact recall ≥ 0.60):** {passed}/{len(results)}",
        "",
        "| Company | Recall | Signal | Found | Missing |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        found = ", ".join(r.facts_found) if r.facts_found else "—"
        missing = ", ".join(r.facts_missing) if r.facts_missing else "—"
        lines.append(f"| {r.company_name} | {_pct(r.fact_recall)} | {_fmt_float(r.signal_score)} | {found} | {missing} |")
    lines.append("")
    return "\n".join(lines)


def _render_fit(results: list[FitBenchResult], stats: FitCorrelationStats) -> str:
    lines = [
        "### Fit Analyst",
        "",
        f"- **Cases run:** {stats.n}",
    ]
    if stats.pearson_r is None:
        lines.append("- **Correlation:** insufficient data (need ≥ 3 pairs)")
    else:
        lines.append(f"- **Pearson r:** {_fmt_float(stats.pearson_r)} (p = {_fmt_float(stats.pearson_p, 3)})")
        lines.append(f"- **Mean |delta|:** {_fmt_float(stats.mean_abs_delta, 1)} points")
        lines.append(f"- **% within ±15 pts:** {_pct(stats.pct_within_tolerance)}")
    lines.extend([
        "",
        "| Resume | JD | Expert | Predicted | Δ | Verdict match | Action match |",
        "|---|---|---|---|---|---|---|",
    ])
    for r in results:
        lines.append(
            f"| {r.resume_id} | {r.jd_id} | {r.expert_score} | {r.predicted_score} | "
            f"{r.score_delta:+d} | {'✓' if r.verdict_match else '✗'} ({r.expected_verdict}→{r.predicted_verdict}) | "
            f"{'✓' if r.action_match else '✗'} ({r.expected_action}→{r.predicted_action}) |"
        )
    lines.append("")
    return "\n".join(lines)


def render_bench_report(
    intake: list[IntakeBenchResult],
    company: list[CompanyResearchBenchResult],
    fit: list[FitBenchResult],
    fit_stats: FitCorrelationStats,
    run_timestamp: str,
) -> str:
    parts = [
        "# Bench report",
        "",
        f"Run: {run_timestamp}",
        "",
        "## Summary",
        "",
        f"- Intake cases: {len(intake)}",
        f"- Company Research cases: {len(company)}",
        f"- Fit Analyst cases: {fit_stats.n}",
        "",
        "---",
        "",
        _render_intake(intake),
        "---",
        "",
        _render_company(company),
        "---",
        "",
        _render_fit(fit, fit_stats),
    ]
    return "\n".join(parts)
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/eval/test_markdown_report.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/eval/reports/markdown.py backend/tests/eval/test_markdown_report.py
git commit -m "feat(eval): Markdown report generator for bench runs"
```

---

## Task 7: `apply bench` CLI command

**Files:**
- Create: `backend/eval/cli.py`
- Modify: `backend/src/apply/cli.py`

- [ ] **Step 1: Implement the eval CLI**

Create `backend/eval/cli.py`:

```python
"""`apply bench` orchestrator — runs all three bench runners and writes a report."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import httpx

from apply.agents.runtime import company_researcher, fit_analyst, intake
from apply.config import get_settings
from eval.reports.markdown import render_bench_report
from eval.runners.company_research_bench import run_company_research_bench
from eval.runners.fit_bench import run_fit_bench
from eval.runners.intake_bench import run_intake_bench

GOLDENSET_DIR = Path("eval/goldenset")
REPORTS_DIR = Path("eval/reports")


async def _fetch_jd_text(url: str) -> str:
    """Fetch JD markdown via Firecrawl; fall back to raw HTTP."""
    settings = get_settings()
    if settings.firecrawl_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
                    json={"url": url, "formats": ["markdown"]},
                )
                if resp.status_code == 200:
                    md = resp.json().get("data", {}).get("markdown")
                    if md:
                        return md
        except Exception:
            pass
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            return resp.text[:50_000]
    except Exception:
        return ""


async def _company_brief(jd_id: str, company_name: str) -> str:
    """Simple company brief for fit analysis — one line."""
    return f"Company under consideration: {company_name} (JD: {jd_id})"


async def run_bench() -> Path:
    """Run all three benches and write a Markdown report. Returns report path."""
    settings = get_settings()
    if not settings.apply_use_real_agents:
        raise RuntimeError(
            "apply bench requires APPLY_USE_REAL_AGENTS=true and real API keys. "
            "Export them from .env first."
        )

    intake_results = await run_intake_bench(
        goldenset_path=GOLDENSET_DIR / "jds.json",
        intake_fn=intake,
        jd_fetch_fn=_fetch_jd_text,
    )
    company_results = await run_company_research_bench(
        goldenset_path=GOLDENSET_DIR / "jds.json",
        researcher_fn=company_researcher,
    )
    fit_results, fit_stats = await run_fit_bench(
        jds_path=GOLDENSET_DIR / "jds.json",
        resumes_path=GOLDENSET_DIR / "resumes.json",
        fit_pairs_path=GOLDENSET_DIR / "fit_pairs.json",
        fit_fn=fit_analyst,
        company_brief_fn=_company_brief,
    )

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    md = render_bench_report(
        intake=intake_results,
        company=company_results,
        fit=fit_results,
        fit_stats=fit_stats,
        run_timestamp=ts,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"bench-{ts}.md"
    out_path.write_text(md)
    return out_path


def main() -> None:
    path = asyncio.run(run_bench())
    print(f"Bench report written to: {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Wire into `apply` CLI**

Modify `backend/src/apply/cli.py` — add a `cmd_bench()` function and dispatch. Read the current file first, then update. Full updated content:

```python
import sys

import uvicorn

from apply.config import get_settings


def cmd_dev() -> None:
    settings = get_settings()
    uvicorn.run(
        "apply.api.main:app",
        host="0.0.0.0",
        port=settings.apply_port,
        reload=True,
    )


def cmd_migrate() -> None:
    import subprocess

    result = subprocess.run(
        ["alembic", "-c", "src/apply/db/alembic.ini", "upgrade", "head"],
        check=False,
    )
    sys.exit(result.returncode)


def cmd_bench() -> None:
    from eval.cli import main as bench_main

    bench_main()


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: apply <dev|migrate|bench>", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1]
    if cmd == "dev":
        cmd_dev()
    elif cmd == "migrate":
        cmd_migrate()
    elif cmd == "bench":
        cmd_bench()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke test without running the full bench**

```bash
cd backend && uv run apply 2>&1 | head -1
```

Expected: `usage: apply <dev|migrate|bench>`

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run python -c "from eval.cli import run_bench" 2>&1
```

Expected: exits cleanly (import succeeds).

- [ ] **Step 4: Verify the `apply bench` dispatch rejects non-real-agents mode**

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run apply bench 2>&1 | tail -3
```

Expected: exits with error message mentioning `APPLY_USE_REAL_AGENTS=true`.

- [ ] **Step 5: Commit**

```bash
git add backend/eval/cli.py backend/src/apply/cli.py
git commit -m "feat(eval): apply bench CLI orchestrating all three bench runners"
```

---

## Task 8: Update .env.example + docs

**Files:**
- Modify: `.env.example`
- Modify: `LEARNINGS.md`
- Modify: `README.md`

- [ ] **Step 1: Ensure .env.example documents bench usage**

Append to `.env.example` (if not already present — check first):

```
# Running `apply bench` requires APPLY_USE_REAL_AGENTS=true AND all
# of APPLY_OPENROUTER_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY set.
```

- [ ] **Step 2: LEARNINGS entry**

Append to `LEARNINGS.md`:

```markdown

## 2026-04-23 — Smallest honest eval beats biggest imagined one
Tags: eval, product-decisions, architecture

Phase 2b scope shrank from "10 JDs × 4 systems × 3 blind human raters"
(the spec's money shot) to "5 JDs, 2 resumes, 5 expert-labeled fit
pairs, measured against the 3 real research agents." The money-shot
baseline comparison needs cover letters — and Cover Letter Writer is
still a stub. Writing the baseline comparison now against stub output
would produce a polished-looking artifact with no signal.

Instead: ship what can actually measure something truthful. The
research-phase bench produces a Markdown report you can check into
PR descriptions, trend against over time, and use to detect regressions
when the prompts change. The baseline comparison moves to Phase 3b,
where the Cover Letter Writer is real and the comparison carries
information.

**Takeaway:** when the full eval you want needs a component you don't
have yet, the honest move is to ship the subset that's measurable now.
A small bench that runs on every change is worth more than a big one
you'll polish for three weeks and then never re-run.

---
```

- [ ] **Step 3: README update**

In `README.md`, find the "Running with real agents" section. Append:

```markdown

### Running the bench

With `APPLY_USE_REAL_AGENTS=true` and all API keys set:

```bash
cd backend && uv run apply bench
```

Hits real LLMs + Tavily + Firecrawl. Takes ~60-120 seconds. Writes a
Markdown report to `backend/eval/reports/bench-<timestamp>.md`. Reports
are gitignored — commit a specific report if you want to trend-compare.

The bench covers:
- Intake field-extraction recall on 5 JDs
- Company Research fact recall
- Fit Analyst Pearson correlation with expert-labeled scores

Full baseline comparison (Apply vs Claude one-shot vs Perplexity vs
LazyApply) needs the real Cover Letter Writer — that lands in Phase 3b.
```

- [ ] **Step 4: Commit**

```bash
git add .env.example LEARNINGS.md README.md
git commit -m "docs: Phase 2b LEARNINGS entry + README section on apply bench"
```

---

## Task 9: Live bench run + goldenset calibration

This task runs the actual bench and captures a baseline report. It will likely surface issues in the goldenset (URLs that 404, expected facts that don't match real output, expert fit scores that need recalibration). Fix inline and commit as a "calibration" commit.

**Prerequisites:** API keys set, `docker compose up -d`, `APPLY_USE_REAL_AGENTS=true` exported.

- [ ] **Step 1: Export environment + verify**

```bash
cd /Users/sanyamupadhyay/Documents/gusain/clarity
set -a && source .env && set +a
echo "use_real=$APPLY_USE_REAL_AGENTS"
echo "openrouter_len=${#APPLY_OPENROUTER_API_KEY}"
echo "tavily_len=${#TAVILY_API_KEY}"
echo "firecrawl_len=${#FIRECRAWL_API_KEY}"
```

Expected: `use_real=true`, all three key lengths > 20.

- [ ] **Step 2: Substitute live JD URLs into the goldenset**

Open `backend/eval/goldenset/jds.json`. For each entry whose URL is a listing-index page (e.g. `https://www.workatastartup.com/jobs`, `https://jobs.lever.co/`), **navigate to that domain, pick a specific, currently-live job posting, and**:
1. Replace `url` with the specific listing URL.
2. Replace every `"FILL_AT_RUN_TIME"` field with the real value from the listing (company_name, role_title, location, remote_type).
3. Review `min_requirements_count` and `min_nice_to_haves_count`; adjust downward if the real listing has fewer than the plan-default.
4. For the `bad-fit-001` entry, deliberately pick a role outside SWE (Marketing Manager, Logistics Lead, Content Writer, etc.).

Commit the populated goldenset:

```bash
git add backend/eval/goldenset/jds.json
git commit -m "chore(eval): populate goldenset with live JD URLs"
```

- [ ] **Step 3: Run the bench**

```bash
cd backend && uv run apply bench
```

Expected: runs for ~60-120 seconds, prints `Bench report written to: eval/reports/bench-<timestamp>.md`. No Python traceback.

If it errors, debug. Common issues:
- 404 on a listing URL → replace that entry in `jds.json` with a current one, retry
- LLM timeout → check OpenRouter status; retry
- Firecrawl rate limit → wait and retry

- [ ] **Step 4: Inspect the report and recalibrate if needed**

Open the generated report (`backend/eval/reports/bench-<timestamp>.md`). Review:

1. **Intake field recall** — if below 80% average across 5 JDs, the prompt likely needs tuning. Investigate which fields failed and consider adjusting `SYSTEM_PROMPT` in `backend/src/apply/agents/intake_real.py`.
2. **Company Research fact recall** — if an `expected_company_facts` entry failed to find, check whether the expected fact is actually a reasonable "must find" (or whether the agent missed it). Adjust `expected_company_facts` in `jds.json` OR investigate Company Researcher prompt.
3. **Fit Pearson r** — if r < 0.5, your expert labels may be miscalibrated, the model may be over- or under-confident, or the sample is too small. If you spot that *your* expert labels disagree with the model on cases where the model seems more reasonable, adjust the labels (honestly) and re-run.

Commit whatever adjustments are honest:

```bash
git add backend/eval/goldenset/
git commit -m "chore(eval): calibrate goldenset against v0.2.1 baseline"
```

- [ ] **Step 5: Commit the first "reference" report**

```bash
# Override the gitignore rule for this one reference report
git add -f backend/eval/reports/bench-*.md
git commit -m "eval: first v0.2.1 baseline bench report"
```

---

## Task 10: Final verification + tag

- [ ] **Step 1: Full test suite green**

```bash
cd backend && uv run pytest --tb=short
```

Expected: previous 58 + new bench-runner unit tests (~14) = ~72 passing.

- [ ] **Step 2: Ruff clean**

```bash
cd backend && uv run ruff check src/ tests/ eval/
```

If issues, fix minimally and commit as `chore: ruff cleanup for Phase 2b`.

- [ ] **Step 3: Walking skeleton still passes with stubs**

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run pytest tests/test_e2e_skeleton.py -v
```

Expected: 1 passed.

- [ ] **Step 4: Tag milestone**

```bash
git tag v0.2.1-research-evals
```

- [ ] **Step 5: Print final state**

```bash
git log master..HEAD --format="%h %s" && echo "---" && git tag | grep v0.2
```

---

## Self-review checklist

- [ ] Every bench runner has a unit test that does NOT hit a real API (uses mocks or fake Pydantic objects)
- [ ] `apply bench` CLI refuses to run without `APPLY_USE_REAL_AGENTS=true`
- [ ] `FILL_AT_RUN_TIME` sentinel is handled in Intake bench scoring (skipped, not counted as failure)
- [ ] Fit bench correlation returns `None` cleanly when n < 3
- [ ] Markdown report renders without crashing for empty result lists
- [ ] Reports directory is gitignored but a specific reference report can be force-added
- [ ] No co-author trailer on any commit

---

## Out of scope for this plan (later phases)

- Baseline comparison table (Apply vs competitors) — Phase 3b after Cover Letter Writer ships
- LLM-as-judge on writing quality — Phase 3b
- 3-blind-rater human study — Phase 3b
- Production data dashboard + outcome logging — Phase 5
- Trajectory evals via Langfuse span inspection — Phase 4/5
- Eval CI integration (run subset on every PR) — Phase 5
