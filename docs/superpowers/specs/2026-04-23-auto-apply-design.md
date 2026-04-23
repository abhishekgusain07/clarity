# Apply — Autonomous Job Application Agent

**Spec date:** 2026-04-23
**Author:** Sanyam Upadhyay
**Project target:** portfolio demonstration for AI Application Engineer / Founding Engineer roles at YC-stage AI companies
**Previous working title:** Clarity (pivoted from research-brief system — see decision log at end)

---

## 1. One-liner

An applications copilot. Paste a job URL, and a 7-agent team produces a recruiter-quality application: company brief, fit analysis, bespoke cover letter, and an auto-filled application form. You approve at 3 checkpoints before anything submits. It learns from what lands replies.

---

## 2. Why this project

### Problem

The AI-auto-apply category in 2026 is crowded with tools (LazyApply, Sonara, LoopCV, AIApply, Simplify, JobRight) that split into two camps: **quantity** (blast 750 generic applications a day) and **"quality"** (shallow match-scoring with generic cover letters). None of them are genuinely agentic — they are LLM-wrapped form-fillers. Recruiters can smell their output and ignore it.

### Wedge

**Recruiter-quality applications, not spray-and-pray.** Five bespoke applications a day you'd be proud to sign your name to, not 500 generic ones. Inverts the category.

### What differentiates this from the existing tools

- Actually reads the company (recent news, founder background, funding stage, their blog)
- Drafts a cover letter that references specific company context, in the user's voice (retrieved from their past writing)
- Reasons explicitly about fit with resume-quote + JD-quote evidence
- Cross-session memory: knows what's landed replies, what hasn't
- Human in the loop before submit (3 architecturally-integrated checkpoints)
- Built on real 2026 primitives: MCP tools, multi-agent orchestration, Claude Agent SDK for computer use

### Target users

Primary: the builder (me, applying to YC AI startups).
Secondary: anyone doing quality-over-quantity job hunting in technical fields.

---

## 3. Core philosophy — "Apply Deliberately"

Every design decision answers to this test: **"Would a thoughtful candidate do this?"**

- A thoughtful candidate researches the company before writing a cover letter → **Company Researcher agent**
- A thoughtful candidate thinks honestly about fit → **Fit Analyst with quote-level evidence**
- A thoughtful candidate writes in their own voice → **Voice-similarity-backed Cover Letter Writer**
- A thoughtful candidate reviews before submitting → **3 HITL checkpoints**
- A thoughtful candidate learns from outcomes → **Memory Curator + memory-mcp**

What we are NOT building:
- Volume auto-apply tool — explicitly the opposite
- LinkedIn scraper — ToS violations, not worth the risk
- "Grade my resume" tool — tangential
- Interview coach — separate product

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER (browser)                                             │
│  Pastes JD URL → watches agents work live → approves at     │
│  3 checkpoints → reviews applied-to history                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS + SSE (streaming)
┌──────────────────────────┴──────────────────────────────────┐
│  FRONTEND — TanStack Start (existing repo)                  │
│  Timeline view, HITL prompts, brief viewer, history         │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + SSE
┌──────────────────────────┴──────────────────────────────────┐
│  BACKEND — FastAPI (Python 3.12)                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ORCHESTRATOR — Pydantic AI                          │   │
│  │                                                      │   │
│  │   1. Intake Agent        (Haiku 4.5)                 │   │
│  │   2. Company Researcher  (Sonnet 4.6 + web MCP)      │   │
│  │   3. Fit Analyst         (Sonnet 4.6) → HITL #1      │   │
│  │   4. Cover Letter Writer (Sonnet + resume-mcp)       │   │
│  │   5. Screening Answerer  (Sonnet + resume-mcp)       │   │
│  │                                      → HITL #2       │   │
│  │   6. Form-Fill Agent  (Claude Agent SDK + browser)   │   │
│  │                                      → HITL #3       │   │
│  │   7. Memory Curator   (Haiku, async post-submit)     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  MCP SERVERS (tools the agents call):                       │
│    • web-search-mcp   (Tavily — off-the-shelf)              │
│    • scrape-mcp       (Firecrawl — off-the-shelf)           │
│    • resume-mcp       (custom — voice corpus + profile)     │
│    • memory-mcp       (custom — past apps + outcomes)       │
│    • playwright-mcp   (Microsoft's official)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│  STORAGE                                                    │
│    • Postgres       — applications, user profile, outcomes  │
│    • ChromaDB       — embeddings (past cover letters, JDs)  │
│    • Filesystem     — resume PDFs, JD HTML, screenshots     │
│    • Langfuse       — traces + cost per agent per run       │
└─────────────────────────────────────────────────────────────┘
```

### Key architectural decisions

1. **Pydantic AI for orchestration, Claude Agent SDK only for Form-Fill.** Pydantic AI gives typed agent hand-offs and multi-provider flexibility; Claude Agent SDK has the deepest computer-use integration and is nested as a sub-agent inside Form-Fill only. Knowing when each is right is the interview signal.
2. **MCP everywhere for tools.** Even if V1 only needs 5 MCP servers, every tool is a reusable, standalone server.
3. **Three HITL checkpoints, each cutting a different cost.** Fit Gate kills bad-fit drafting costs early; Content Approval guards the highest-value artifact; Submission Gate is the hard irreversibility safety.
4. **No LinkedIn.** JD source is user-pasted URL or YC `workatastartup.com`. Clean legally and ethically.
5. **State machine in Postgres, not LangGraph interrupts.** Maps 1:1 to REST semantics, survives page refreshes, doesn't commit us to LangGraph.

---

## 5. The 7-agent pipeline (detailed)

### Agent 1: Intake

**Job:** Parse a JD URL into a typed `JobListing`. Detect which job-board format (YC WaaS / Wellfound / Greenhouse / Lever / Ashby / company page) so downstream agents know what to expect.

**Pattern:** Single-shot structured output.
**Model:** Claude Haiku 4.5.
**Tools:** `scrape-mcp`.
**Output:** `JobListing` (see schemas).

### Agent 2: Company Researcher

**Job:** Gather enough company context to make a cover letter non-generic. Founder backgrounds, funding stage, recent news, blog posts, tech stack hints.

**Pattern:** ReAct loop.
**Model:** Claude Sonnet 4.6.
**Tools:** `web-search-mcp`, `scrape-mcp`.
**Output:** `CompanyResearch` with `signal_score` (how much hook material we found).

### Agent 3: Fit Analyst

**Job:** Produce a structured fit analysis with direct quotes from both the resume and the JD. Explicit matches / stretches / gaps. Recommend PROCEED / PROCEED_WITH_CAUTION / SKIP.

**Pattern:** Single-shot with structured reasoning.
**Model:** Claude Sonnet 4.6.
**Tools:** `resume-mcp` (get resume markdown), `memory-mcp` (check for prior applications to same company).
**Output:** `FitAnalysis`.
**Feeds into:** HITL #1.

### Agent 4: Cover Letter Writer

**Job:** Draft a cover letter that weaves in company research, reasons about fit, and sounds like the user's voice (retrieved from past writing samples).

**Pattern:** RAG-augmented single-shot.
**Model:** Claude Sonnet 4.6.
**Tools:** `resume-mcp` (voice samples, profile), `memory-mcp` (what landed replies).
**Output:** `CoverLetter` with voice-similarity score and list of `references_company_specifics` for HITL verification.
**Feeds into:** HITL #2.

### Agent 5: Screening Question Answerer

**Job:** Answer custom free-text questions ("Why us?", "Tell us about a time when..."). Can be invoked either proactively (if JD lists screening qs) or dynamically by Form-Fill when it encounters an unknown field mid-form-fill. This dynamic multi-agent callback is the strongest "real multi-agent" interview story.

**Pattern:** Single-shot per question.
**Model:** Claude Sonnet 4.6.
**Tools:** `resume-mcp`.
**Output:** `ScreeningAnswer`.
**Feeds into:** HITL #2 (initial) or Form-Fill loop (dynamic).

### Agent 6: Form-Fill

**Job:** Navigate the application page, fill every field, discover and handle screening questions via callback to Agent 5, show the filled form for approval, submit.

**Pattern:** Computer-use ReAct with dynamic sub-agent invocation.
**Model:** Claude Agent SDK (Anthropic's computer-use model).
**Tools:** `playwright-mcp`, callback to Screening Answerer.
**Output:** `FormFillResult` with per-field status, screenshot, any flagged unknowns.
**Feeds into:** HITL #3.

### Agent 7: Memory Curator

**Job:** Async post-submission — embed the artifacts, log the outcome, update memory patterns. Runs as a background task, doesn't block the user-facing pipeline.

**Pattern:** Single-shot.
**Model:** Claude Haiku 4.5.
**Tools:** `memory-mcp`, ChromaDB writes.

---

## 6. Human-in-the-loop checkpoints

### HITL #1 — Fit Gate

Fires after Agents 1–3.

**UI shows:**
- Company one-paragraph + `signal_score`
- Fit score (0–100) + verdict
- Three evidence columns: matches / stretches / gaps with direct quotes
- Memory warning if user already applied here
- Agent's recommendation + cost so far

**User actions:** Proceed | Skip (no draft costs incurred) | Tell writer to emphasize X.

**Saves:** ~$0.20 in drafting costs + ~3 min per obvious bad-fit.

### HITL #2 — Content Approval

Fires after Agents 4–5.

**UI shows:**
- Cover letter in inline editor (TipTap)
- Voice-similarity score with flag if < 0.6
- Company-specifics panel (every research-grounded claim listed so user can verify)
- Each screening question + draft answer
- Cost so far

**User actions:** Approve | Regenerate-with-notes (free-text feedback baked into new draft, logged to memory-mcp) | Edit manually | Skip.

### HITL #3 — Submission Gate

Fires after Agent 6 fills the form.

**UI shows:**
- Screenshot of filled form + structured per-field preview
- Checklist of every filled field
- Unknown fields flagged red with agent's best-guess + "confirm?"
- Total cost

**User actions:** Submit | Edit field | Cancel without submitting (saves as DRAFTING).

### State persistence

FastAPI + Postgres-backed state machine. `PipelineRun.state ∈ {INTAKE_RUNNING, AWAITING_FIT_APPROVAL, DRAFTING, AWAITING_CONTENT_APPROVAL, FILLING_FORM, AWAITING_SUBMIT_APPROVAL, SUBMITTING, COMPLETED, ABANDONED}`. Frontend subscribes to `/runs/{id}/events` via SSE. User clicks approve → `POST /runs/{id}/approve` → backend loads state and resumes the next agent. Survives page refreshes.

---

## 7. Data model

### Storage layers

| Layer | Stores |
|---|---|
| Postgres (SQLAlchemy async) | Users, Resumes, Applications, Outcomes, PipelineRuns, HITL decisions, cost breakdowns |
| ChromaDB (embedded) | Embeddings of past cover letters, past JDs, company research snippets |
| Filesystem + Postgres path-ref | Resume PDFs, JD HTML snapshots, submission confirmations, screenshots |
| Langfuse (self-hosted) | Traces, per-agent costs, per-tool latencies, prompt/response history |

### Core Pydantic schemas

```python
class JobListing(BaseModel):
    id: str
    source: JobSource  # YC_WAAS | WELLFOUND | GREENHOUSE | LEVER | ASHBY | WORKDAY | COMPANY_PAGE | OTHER
    url: HttpUrl
    application_url: HttpUrl
    company_name: str
    role_title: str
    location: str
    remote_type: RemoteType
    description_markdown: str
    requirements: list[str]
    nice_to_haves: list[str]
    compensation_range: str | None
    raw_html_path: Path  # for re-reading during form-fill

class CompanyResearch(BaseModel):
    company_name: str
    funding_stage: str | None
    last_round: Round | None
    team_size: str | None
    founders: list[Founder]
    recent_news: list[NewsItem]
    recent_blog_posts: list[BlogPost]
    tech_stack_hints: list[str]
    signal_score: float  # 0-1
    sources: list[Source]

class FitAnalysis(BaseModel):
    overall_score: int  # 0-100
    verdict: Literal["STRONG", "MODERATE", "STRETCH", "WEAK"]
    matches: list[FitPoint]
    stretches: list[FitPoint]
    gaps: list[FitPoint]
    reasoning: str
    recommended_action: Literal["PROCEED", "PROCEED_WITH_CAUTION", "SKIP"]

class FitPoint(BaseModel):
    dimension: str
    evidence_resume: str | None
    evidence_jd: str
    strength: Literal["strong", "moderate", "weak"]

class CoverLetter(BaseModel):
    id: str
    application_id: str
    draft_version: int
    body_markdown: str
    word_count: int
    references_company_specifics: list[str]
    voice_similarity_score: float
    created_at: datetime

class ScreeningAnswer(BaseModel):
    question: str
    answer: str
    word_count: int
    drafted_by: Literal["PROACTIVE", "FORM_FILL_CALLBACK"]

class Application(BaseModel):
    id: str
    user_id: str
    job_listing: JobListing
    company_research: CompanyResearch
    fit_analysis: FitAnalysis
    cover_letter: CoverLetter | None
    screening_answers: list[ScreeningAnswer]
    status: ApplicationStatus  # DRAFTING | AWAITING_APPROVAL | SUBMITTED | REPLIED | INTERVIEWED | REJECTED | GHOSTED
    hitl_decisions: list[HitlDecision]
    cost_breakdown: CostBreakdown
    submitted_at: datetime | None
    outcome: Outcome | None
```

---

## 8. MCP server breakdown

**Strategy: build 2 custom, use 3 off-the-shelf.** Recruiters care more about meaningful custom MCP servers than rewriting battle-tested ones.

| Server | Build / Buy | Tools | Agents using it |
|---|---|---|---|
| `web-search-mcp` | Off-the-shelf (Tavily MCP) | `search`, `news_search` | Company Researcher |
| `scrape-mcp` | Off-the-shelf (Firecrawl MCP) | `scrape`, `map_site` | Intake, Company Researcher |
| `resume-mcp` | **BUILD** (FastMCP) | `get_resume_markdown`, `get_profile_field`, `find_voice_samples(query, top_k)`, `list_past_writing` | Cover Letter Writer, Screening Answerer |
| `memory-mcp` | **BUILD** (FastMCP) | `already_applied`, `similar_applications`, `what_landed_replies`, `log_outcome` | Fit Analyst, Cover Letter Writer, Memory Curator |
| `playwright-mcp` | Off-the-shelf (Microsoft's official) | `navigate`, `accessibility_snapshot`, `click`, `type`, `upload`, `screenshot` | Form-Fill |

---

## 9. Failure modes & recovery

| Failure | Recovery |
|---|---|
| URL not a job page / 404 / login wall | Intake fails gracefully, prompts user to paste JD text directly |
| Stealth company, low `signal_score` | Cover Letter Writer leans on JD; HITL #2 flags "company research thin" |
| Borderline fit (40–60) | Agent returns `PROCEED_WITH_CAUTION`; HITL #1 shows both sides |
| No voice samples yet | Fall back to resume's prose tone + professional default; edits seed the corpus |
| CAPTCHA / SMS / SSO | Form-Fill pauses, hands control to user, polls for continuation |
| Unknown form field | Flag in HITL #3 with best-guess; log field type to memory-mcp |
| Rate-limit from job board | Exponential backoff; if persistent, halt + schedule retry |
| Submission confirmation not captured | Status = `SUBMITTED_UNCONFIRMED`; user prompted to verify |
| Already applied here | HITL #1 warns before any drafting cost |
| Cost cap exceeded mid-run | Halt at next agent boundary, alert user. Per-app cap: $0.50 |

---

## 10. Evaluation strategy

Three tracks:

### Track 1 — Development-time evals (pytest, runs on every agent change)

| Agent | Metric | Golden set size | Pass bar |
|---|---|---|---|
| Intake | Field-extraction accuracy | 20 JD URLs | ≥ 95% field recall |
| Company Researcher | Fact recall vs ground truth | 10 companies × 5 facts each | ≥ 80% |
| Fit Analyst | Pearson correlation w/ expert label | 10 resume-JD pairs | r ≥ 0.75 |
| Cover Letter Writer | LLM-as-judge on 4-dim rubric | 10 cases × 3 seeds | avg ≥ 7.0/10 |
| Form-Fill | Correct-field rate | 5 Greenhouse/Lever captures | ≥ 95% |

### Track 2 — The baseline comparison (the money shot)

10 JD URLs across YC WaaS, Wellfound, Greenhouse, Lever, Workday, company pages, and 1 deliberately-bad-fit role. For each, generate cover letter via:
- **B1:** Single-shot Claude Sonnet 4.6
- **B2:** ChatGPT with web search
- **B3:** LazyApply / Simplify output
- **S:** Full pipeline

3 blind human raters score on Specificity / Voice / Hook / Would-I-reply. Published as a table in README.

### Track 3 — Production data (ongoing)

Every real application logs outcome. Dashboard shows reply rate by fit-score bucket, cost efficiency over time, regenerate-notes patterns that landed replies, voice drift.

### LLM-as-judge rubric (4 dimensions, 0–10 each with rubric anchors)

Specificity / Voice match / Hook strength / Professionalism. Judge uses a different model (GPT-4.1) than the writer (Claude) to reduce self-grading bias. Judge also outputs `specifics_cited` for hallucination check.

### Trajectory evals

Weekly manual inspection of 10 random traces + all failed traces via Langfuse. Notes to `LEARNINGS.md`.

### V1 ship bar

| Metric | Target | Stretch |
|---|---|---|
| Company Research fact recall | 0.80 | 0.90 |
| Fit Analyst Pearson correlation | 0.75 | 0.85 |
| Cover letter specificity (judge avg) | 7.0 | 8.0 |
| Cover letter voice similarity | 0.65 | 0.75 |
| Form-Fill correct-field rate | 95% | 99% |
| End-to-end latency | < 5 min | < 3 min |
| Per-application cost | < $0.50 | < $0.30 |
| Baseline comparison reply-rate lift (S vs best baseline) | +20pp | +40pp |

---

## 11. Build phases (6 calendar weeks, ~140 engineering hours)

### Phase 0 — Bootstrap (weekend, ~6 hrs)
Docker compose brings Postgres + ChromaDB + Langfuse. `uv` env. FastAPI `/health`. TanStack frontend calling it. All API keys in `.env`.

### Phase 1 — Walking skeleton (Week 1, ~20 hrs)
End-to-end pipeline with 7 stub agents returning fake data. State machine works, SSE streams, all 3 HITL checkpoints fire, Langfuse captures traces. Zero real AI yet — the hard architecture questions are answered before a single LLM call.

### Phase 2 — Research & Fit (Week 2, ~25 hrs)
Replace stubs 1–3 with real agents. Intake + Company Researcher (ReAct) + Fit Analyst. Wire tavily-mcp + firecrawl-mcp. HITL #1 renders real data. Unit evals pass on 5-case starter goldenset.

### Phase 3 — Writing & memory (Week 3, ~25 hrs)
Build `resume-mcp` and `memory-mcp` as FastMCP servers. Cover Letter Writer uses voice samples via RAG. Screening Question Answerer. HITL #2 with inline editor + regenerate-with-notes loop. LLM-as-judge operational.

### Phase 4 — Form-Fill & submission (Week 4, ~30 hrs — hardest week)
Claude Agent SDK nested sub-agent. Playwright MCP. Handles YC WaaS + Greenhouse + Lever forms. Dynamic callback to Screening Answerer. HITL #3. Memory Curator async. **End of Week 4: you can apply to real YC jobs through it.**

### Phase 5 — Polish, evals, publish (Weeks 5–6, ~40 hrs)
Baseline comparison with 3 blind raters. README with architecture diagram + Loom GIF + baseline table. Blog post. `LEARNINGS.md` synthesis. Dashboard. Cutline: Ashby + Workday slip to V2; inbox integration for outcomes slips to V2.

---

## 12. Tech stack (pinned)

**Backend (Python 3.12+, `uv`):**
FastAPI 0.115+, Pydantic AI, Pydantic v2, Claude Agent SDK (Python), SQLAlchemy 2.0 async + Alembic, asyncpg, ChromaDB (embedded), FastMCP, anthropic + openai SDKs, Langfuse, pytest + pytest-asyncio + vcrpy.

**Frontend:**
TanStack Start (existing), React 19, Tailwind 4, shadcn/ui, native EventSource for SSE, TipTap (inline editor), react-markdown.

**Infra:**
Docker Compose locally. Deployment deferred to V2 — V1 demo is Loom + local screen recording.

---

## 13. Repo layout

```
apply/
├── frontend/                         existing TanStack repo
├── backend/
│   ├── pyproject.toml
│   ├── src/apply/
│   │   ├── api/                      FastAPI + SSE
│   │   ├── agents/                   7 agent files
│   │   ├── orchestrator/             graph + state machine
│   │   ├── schemas/                  Pydantic models
│   │   ├── db/                       SQLAlchemy + alembic
│   │   ├── storage/                  Chroma + files
│   │   ├── mcp_servers/
│   │   │   ├── resume_mcp/
│   │   │   └── memory_mcp/
│   │   ├── observability/
│   │   └── cli.py
│   ├── tests/
│   └── eval/
│       ├── goldenset/
│       ├── run_bench.py
│       ├── llm_judge.py
│       └── baseline_comparison.md
├── docs/superpowers/specs/
├── LEARNINGS.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 14. `LEARNINGS.md` structure

Single chronological file, tagged entries, lives at repo root. Written for future self + for interview answers.

```
# Learnings — Apply

## Top 5 lessons (synthesized, updated as I go)
1. ...

## Index by tag
- agent-design, prompt-engineering, mcp, tooling,
  debugging, architecture, product-decisions, eval

## YYYY-MM-DD — [entry title]
Tags: [...]
[Context: what I was doing]
[What happened / what I found]
[Takeaway — the insight, not the event]
```

**Cadence:** ≥ 2 entries/week. Every "huh, that's weird" during debugging → entry. Every product decision with a real tradeoff → entry. End of each week, synthesize patterns into Top 5.

---

## 15. V1 "done" checklist

**Functional:**
- [ ] All 7 agents implemented against real LLM calls
- [ ] 3 HITL checkpoints fire with correct data; state survives page refresh
- [ ] YC WaaS + Greenhouse + Lever form formats supported end-to-end
- [ ] Memory Curator async task works; memory-mcp returns real hits on 2nd+ run
- [ ] Form-Fill → Screening Answerer dynamic callback wired + tested
- [ ] Cost cap enforced at $0.50/application

**Evals:**
- [ ] Unit-eval goldenset with ≥ 5 cases per agent, meeting all pass bars
- [ ] Baseline comparison table in README (10 JDs × 3 blind raters)
- [ ] Reply-rate advantage over best baseline: +20pp absolute
- [ ] Langfuse traces captured for every run, cost attributed per agent

**Portfolio:**
- [ ] README: pitch, architecture diagram, baseline table, Loom GIF, quickstart
- [ ] 2–3 min Loom demo
- [ ] Blog post published
- [ ] `LEARNINGS.md` with ≥ 20 entries and Top-5 synthesis
- [ ] Repo clean + public

**Operational:**
- [ ] ≥ 10 real applications submitted through the tool by end of Week 6
- [ ] Dashboard with reply rate / cost / fit-score distribution
- [ ] ≥ 1 real reply received (existence proof)

---

## 16. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Claude Agent SDK + Playwright MCP integration gotchas | Walking skeleton in Week 1 surfaces issues early; 30 hrs budgeted for Phase 4 |
| ATS form quirks (shadow DOM, hidden required fields) | Test on 5 real listings per ATS before assuming it works; cut to V2 any ATS < 95% fill rate |
| Cover letter quality plateaus < 7.0 | Voice corpus seeded early; Week 3.5 buffer for prompt iteration |
| LLM rate limits / cost overruns in eval | VCR for recorded LLM replay in tests; Anthropic org-level daily caps |
| Running out of hours | V1 Lite fallback: drop Screening-Question-as-separate-agent and memory-mcp to V2 without re-architecting |

---

## 17. V1 Lite fallback (contingency only)

If Week 4 is hurting: cut to 4 agents (merge Researcher+Fit, merge Writer+Screening, drop Memory Curator), 1 custom MCP (resume-mcp), 2 HITL checkpoints, YC WaaS only. Preserves all resume-critical signals. Gets to shippable in 4 weeks.

**Use only as rescue valve. Default plan is full 7-agent V1.**

---

## 18. Decision log

**Pivoted from Clarity (research-brief system) on 2026-04-23.** Clarity's 6-agent research pipeline technically covered every AI-engineering skill but competed directly with Google Gemini Deep Research, OpenAI Deep Research, and Perplexity Pro — all shipped in 2025. A recruiter skimming the resume would pattern-match it as "another Perplexity clone" regardless of the technical depth. Auto-Apply solves a real problem the builder has, uses the full agent stack meaningfully, and carries a unique meta-hook for the target audience (YC AI company recruiters): *"the agent I built to apply to your company."*

**Chose Pydantic AI + Claude Agent SDK combo over pure LangGraph.** LangGraph is fine, but ubiquitous on AI resumes in 2026. Knowing *when* each framework is right (Pydantic AI for typed orchestration, Claude Agent SDK for computer-use depth) is a stronger signal than depth in one.

**No LinkedIn support.** hiQ v. LinkedIn (2019) says public scraping isn't a CFAA crime, but LinkedIn's ToS bans bots — real account risk, not worth it. User pastes the URL directly.

**State machine in Postgres, not LangGraph interrupts.** Cleaner REST semantics, survives page refreshes, keeps the stack out of LangGraph entirely.

**Three HITL checkpoints, not one.** Each cuts a different cost (research/drafting/submission). Fewer checkpoints would feel more automated but weaken the "deliberate application" product story.

**No hosted deployment in V1.** Demo is Loom + screen record. Local Docker Compose is sufficient for the portfolio signal; deployment cost and DevOps overhead don't buy additional interview credit.

---

## 19. Out of scope (explicit V2+)

- LinkedIn integration
- Ashby, Workday form support
- Inbox integration for automatic outcome tracking
- Resume tailoring per application
- Multi-user / hosted SaaS
- Mobile app / browser extension
- Interview prep features
- Salary negotiation assistance
- Outcome prediction models
- Neo4j knowledge graph across companies
