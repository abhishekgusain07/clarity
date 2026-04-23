this i# Clarity — Multi-Agent Personal Research Intelligence System

**One-liner:** Tell it a decision you're wrestling with → 6 specialist agents run a research pipeline and produce a citation-backed brief with fact-checked claims, flagged contradictions, and multiple perspectives.

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [What We're Building](#2-what-were-building)
3. [Core Philosophy — "Research, Don't Chat"](#3-core-philosophy)
4. [Who It's For & Use Cases](#4-use-cases)
5. [Architecture Overview](#5-architecture-overview)yes 
6. [The 6-Agent Pipeline](#6-the-6-agent-pipeline)
7. [Phase-by-Phase Build Plan](#7-build-plan)
8. [Tech Stack](#8-tech-stack)
9. [Concepts & Skills Covered](#9-concepts--skills-covered)
10. [Example — End-to-End Walkthrough](#10-example-walkthrough)
11. [Evaluation](#11-evaluation)how
12. [Week-by-Week Build Schedule](#12-schedule)
13. [Resume Bullets](#13-resume-bullets)

---

## 1. The Problem

### The Pain

Every year, every person faces a handful of decisions that genuinely matter:
- "Should I take this job offer?"
- "My insurance claim got denied. Do I have a case?"
- "Is this investment opportunity real or a scam?"
- "My doctor recommended treatment X. Is this the standard of care?"
- "I got sued in small claims court. What are my rights?"
- "Should I contest this property tax assessment?"
- "Is this apartment lease clause legal in my state?"

These decisions can change your life by tens of thousands of dollars, years of your career, or your health. And yet — how do we make them?

- Google search → 20 contradictory blog posts
- Reddit → anecdotes from strangers
- ChatGPT → confident hallucinations with no sources
- Ask a friend → who has no expertise
- Hire a professional → $500/hour, unaffordable

### The Gap

There is a massive difference between **information** (which is everywhere) and **research** (which requires structure, verification, and perspective). A professional researcher spends hours:
1. Gathering information from authoritative sources
2. Cross-referencing contradictory claims
3. Identifying source bias
4. Building a structured summary with citations
5. Flagging what's uncertain vs settled

An LLM chatbot does none of this reliably. It makes confident claims with no verifiable sources, doesn't distinguish perspectives, and has no structured quality guarantees.

### Why Now

- Perplexity proved the market for "research > chatbot" ($18B valuation)
- But Perplexity is still fundamentally a chat interface, not a structured research system
- Multi-agent orchestration (LangGraph, etc.) is mature enough to build real research pipelines
- The "agent" vs "chatbot" distinction is the #1 differentiator on AI resumes right now

---

## 2. What We're Building

A CLI + web app that takes a decision question, runs a multi-agent research pipeline, and produces a structured research brief.

```bash
$ clarity research "Should I accept this job offer? (details attached)" \
    --context offer-letter.pdf \
    --depth thorough

[Planning research...]
  → Identified: career decision, compensation analysis, company evaluation
  → Assembled research plan (6 subtasks)
  → Awaiting your approval of plan... [approve / edit / reject]

[Running 4 specialist agents in parallel...]
  ✓ Company Researcher (Glassdoor, Blind, news): 47 sources analyzed
  ✓ Market Analyst (salary benchmarks, role trends): 23 sources
  ✓ Role Analyst (JD analysis, team assessment): 12 sources  
  ✓ Risk Analyst (red flags, contract terms): 8 sources

[Fact-checking claims across sources...]
  ✓ 94 claims verified
  ⚠ 3 contradictions flagged for your review

[Generating brief...]

Brief saved to: ./clarity-briefs/job-offer-2026-04-12.md

Executive Summary: Moderate confidence recommendation — take with negotiations
Confidence: 0.78 | Sources: 90 | Cost: $0.42 | Time: 6m 24s
```

### Output: A Structured Research Brief

Not a chat response. A structured document with:
- **Executive Summary** (confidence-scored)
- **Key Facts** (each with citation + confidence level)
- **Multiple Perspectives** (optimist/pessimist/neutral views with source attribution)
- **Contradictions** (where sources disagree, with both sides)
- **Unknowns** (questions the research couldn't answer)
- **Risks & Red Flags** (explicit warnings)
- **Recommended Next Steps** (specific actions)
- **Sources** (every cited source with URL and trust score)

---

## 3. Core Philosophy — "Research, Don't Chat"

This is the single most important design principle.

### Research (what we build)
- Multiple specialist agents attacking the problem from different angles
- Every claim backed by a specific source with a URL
- Contradictions flagged, not silently resolved
- Confidence levels on every claim
- Structured output you can reference later
- Human-in-the-loop checkpoints at high-stakes moments
- Focused on one question, deeply answered

### Chat (what everyone else builds)
- One LLM, one response, vibes-based
- Confident claims with no verifiable sources
- Silently picks one side when sources disagree
- No confidence signaling
- Ephemeral text you can't cite or trust
- Zero oversight, just "trust the AI"
- Tries to be a conversational generalist

### The Test

For every feature, ask: **"Would a professional researcher/analyst do this?"** If yes, include it. If it's only a chatbot feature, leave it out. We're building a research assistant, not a conversational bot.

---

## 4. Who It's For & Use Cases

### Target Users

- Professionals facing high-stakes decisions without domain expertise
- Consumers dealing with disputes (insurance, landlord, employer)
- People making major purchases (house, car, medical treatment)
- Anyone who says "I don't know what to do about X" and spends hours Googling

### Use Cases (Demo-able)

| Category | Example Question | Specialist Agents |
|----------|-----------------|-------------------|
| **Career** | "Should I accept this job offer at $X with equity Y at stage-Z company?" | Company Researcher, Market Analyst, Role Analyst, Risk Analyst |
| **Consumer Rights** | "My insurance claim was denied. The denial letter is attached. Do I have a case?" | Policy Researcher, Regulation Researcher, Precedent Finder, Appeal Drafter |
| **Financial** | "Is this investment opportunity real or a scam? Here's the pitch deck." | Background Researcher, Regulatory Researcher, Red Flag Detector, Alternative Finder |
| **Legal** | "I got a small claims court summons. What are my rights and options?" | Law Researcher, Procedure Researcher, Defense Analyst, Risk Assessor |
| **Medical** | "My doctor recommended treatment X. What does the evidence say?" | Evidence Researcher, Alternative Finder, Side Effect Analyst, Guideline Researcher |
| **Real Estate** | "Is this apartment lease clause legal in California?" | Law Researcher, Precedent Finder, Tenant Rights Analyst |
| **Education** | "Is this online course/bootcamp worth $5000?" | Review Researcher, Outcome Researcher, Alternative Finder, Cost Analyst |

### Explicitly NOT What We're Building

- ❌ Medical diagnosis ("what disease do I have")
- ❌ Legal advice ("sue person X")
- ❌ Financial advice ("buy stock Y")
- ❌ Prescriptive recommendations without disclaimers

We produce INFORMATION briefs with citations. We do NOT give professional advice. Every brief includes a "This is research, not professional advice — consult a [lawyer/doctor/advisor] for X" footer.

---

## 5. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                          INPUT                                    │
│  Question + optional context (PDFs, screenshots, URLs)            │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   PHASE 1: UNDERSTAND                             │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐    │
│  │ Intent Parser   │  │ Context Loader  │  │ Classifier      │    │
│  │ (Gemini Flash)  │  │ (PDF, images,   │  │ → decision type │    │
│  │                 │  │  URLs)          │  │ → urgency       │    │
│  └─────────────────┘  └─────────────────┘  └────────────────┘    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                  PHASE 2: PLAN (Supervisor Agent)                 │
│                                                                   │
│  Plan-and-execute pattern:                                        │
│  → Decomposes question into research subtasks                     │
│  → Assigns subtasks to specialist agents                          │
│  → Sets success criteria per subtask                              │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           HUMAN CHECKPOINT #1: Plan Approval              │    │
│  │  User reviews plan, can edit/approve/reject               │    │
│  │  LangGraph interrupt + resume on approval                 │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌══════════════════════════════════════════════════════════════════╗
║               PHASE 3: RESEARCH (Parallel Specialists)             ║
║                                                                    ║
║  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  ║
║  │ Primary         │  │ Domain          │  │ Risk &           │  ║
║  │ Researcher      │  │ Expert          │  │ Red Flag         │  ║
║  │                 │  │                 │  │ Analyst          │  ║
║  │ ReAct loop:     │  │ ReAct loop:     │  │ ReAct loop:      │  ║
║  │ search → scrape │  │ RAG over        │  │ searches for     │  ║
║  │ → extract facts │  │ authoritative   │  │ scams, warnings, │  ║
║  │                 │  │ sources         │  │ lawsuits         │  ║
║  │                 │  │ (gov, academic) │  │                  │  ║
║  └─────────────────┘  └─────────────────┘  └──────────────────┘  ║
║                                                                    ║
║  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  ║
║  │ Perspective     │  │ Alternatives    │  │ Fact-Check       │  ║
║  │ Analyst         │  │ Finder          │  │ Agent            │  ║
║  │                 │  │                 │  │                  │  ║
║  │ Searches for    │  │ Identifies      │  │ Verifies each    │  ║
║  │ pro/con         │  │ options user    │  │ claim against    │  ║
║  │ viewpoints,     │  │ didn't consider │  │ source docs,     │  ║
║  │ source bias     │  │                 │  │ flags contra-    │  ║
║  │                 │  │                 │  │ dictions         │  ║
║  └─────────────────┘  └─────────────────┘  └──────────────────┘  ║
║                                                                    ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │  All specialists write findings to SHARED STATE           │    ║
║  │  (LangGraph state = workspace for multi-agent coordination)│   ║
║  │                                                           │    ║
║  │  Findings stored in:                                      │    ║
║  │  • ChromaDB (for retrieval by later agents)               │    ║
║  │  • Knowledge graph (entity & relationship tracking)       │    ║
║  │  • PostgreSQL (for persistence across sessions)           │    ║
║  └──────────────────────────────────────────────────────────┘    ║
║                                                                    ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │           HUMAN CHECKPOINT #2: Risk Flags Review          │    ║
║  │  Red flags from Risk Analyst are shown for user approval  │    ║
║  │  before inclusion in the brief                            │    ║
║  └──────────────────────────────────────────────────────────┘    ║
╚════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│            PHASE 4: SYNTHESIZE & EVALUATE                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Synthesis Agent (Claude Sonnet)                          │    │
│  │  → Combines all findings into structured brief             │    │
│  │  → Groups claims by confidence level                       │    │
│  │  → Attributes every claim to source(s)                     │    │
│  │  → Surfaces contradictions explicitly                      │    │
│  └────────────────────────┬─────────────────────────────────┘    │
│                           │                                       │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Quality Evaluator (LLM-as-Judge)                         │    │
│  │  Scores on 4 dimensions:                                  │    │
│  │  • Citation Coverage — every claim has a source?          │    │
│  │  • Factual Consistency — no internal contradictions?      │    │
│  │  • Completeness — all plan subtasks covered?              │    │
│  │  • Actionability — can the user make a decision?          │    │
│  │                                                           │    │
│  │  Score < 0.85 → loop back to specialist agents to         │    │
│  │  re-research the weak sections (ReAct re-entry)           │    │
│  └────────────────────────┬─────────────────────────────────┘    │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│             HUMAN CHECKPOINT #3: Final Brief Review               │
│  User reviews brief, can request follow-up research or approve    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       PHASE 5: OUTPUT                             │
│                                                                   │
│  Brief saved to:                                                  │
│  • Markdown file (human-readable)                                 │
│  • JSON (structured data for programmatic access)                 │
│  • PostgreSQL session record (for future follow-ups)              │
│                                                                   │
│  Knowledge graph persists — subsequent briefs can build on        │
│  earlier research. Memory accumulates across sessions.            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. The 6-Agent Pipeline (Detailed)

### Agent 1: Supervisor (Plan-and-Execute)

**Job:** Decompose the user's question into a research plan with specific subtasks for specialist agents.

**Inputs:**
- User's question
- Optional context (PDFs, images, URLs)
- Classification output (decision type, urgency)

**Process:**
1. Parse the question — what is the user actually trying to decide?
2. Identify the domains involved (career, legal, medical, financial, etc.)
3. Generate a research plan: ordered list of subtasks
4. Assign each subtask to a specialist agent
5. Set success criteria for each subtask (e.g., "find 3+ authoritative sources")
6. Present plan to user for approval (Checkpoint #1)

**Output Schema (Pydantic):**
```python
class ResearchPlan(BaseModel):
    question: str
    decision_type: DecisionType
    subtasks: list[Subtask]
    estimated_cost: float
    estimated_time_minutes: int
    
class Subtask(BaseModel):
    id: str
    agent_type: AgentType  # PRIMARY_RESEARCH | DOMAIN_EXPERT | RISK | etc.
    objective: str
    success_criteria: list[str]
    dependencies: list[str]  # IDs of subtasks that must complete first
```

**LLM:** Claude Sonnet 4.6 (needs strong reasoning to decompose complex questions well)

---

### Agent 2: Primary Researcher

**Job:** Gather factual information from the web using a ReAct loop (Reason → Act → Observe → repeat).

**Inputs:**
- Subtask from Supervisor
- Shared state (for reading other agents' findings)

**Tools:**
- `web_search(query)` — Tavily or Serper API
- `web_scrape(url)` — Firecrawl for clean content extraction
- `read_pdf(file)` — user-uploaded documents
- `write_finding(finding)` — save to shared state + knowledge graph

**Process (ReAct loop):**
```
1. Think: "I need to find salary data for senior engineers at Series B startups"
2. Act: web_search("senior engineer salary Series B startup 2026")
3. Observe: 10 results
4. Think: "Levels.fyi has specific data. Let me scrape it."
5. Act: web_scrape("levels.fyi/senior-eng-series-b")
6. Observe: structured salary data
7. Think: "I also need equity benchmarks"
8. Act: web_search("equity compensation Series B 0.1%-0.5% benchmark")
...
N. Done: I have 4 authoritative sources. Write findings.
```

**Output:**
```python
class Finding(BaseModel):
    claim: str
    source_url: str
    source_title: str
    source_trust_score: float  # 0-1, heuristic based on domain
    quote: str  # direct quote supporting the claim
    confidence: float  # 0-1, how confident the agent is
    subtask_id: str
```

**LLM:** Claude Sonnet 4.6

---

### Agent 3: Domain Expert

**Job:** Go deeper than generic web search — use RAG over authoritative, curated sources (government sites, academic databases, official documentation).

**Inputs:**
- Subtask from Supervisor
- Shared state
- Domain-specific RAG collections (pre-built indexes of authoritative sources)

**Pre-built RAG Collections:**
- **Legal:** Federal/state law (Justia, Cornell LII), case law (CourtListener)
- **Medical:** PubMed, Cleveland Clinic, Mayo Clinic, CDC, FDA
- **Financial:** SEC EDGAR, FINRA, Federal Reserve
- **Consumer:** FTC, CFPB, state AG offices, BBB
- **Career:** BLS (Bureau of Labor Statistics), O*NET

**Process:**
1. Classify the question by domain
2. Query the corresponding RAG collection
3. Extract authoritative claims with source attribution
4. Cross-reference with Primary Researcher's findings

**Output:** Same `Finding` schema as Primary Researcher, but with higher `source_trust_score` (authoritative sources get 0.9-1.0).

**LLM:** Claude Sonnet 4.6

---

### Agent 4: Risk & Red Flag Analyst

**Job:** Specifically search for warnings, red flags, scams, lawsuits, negative experiences, and things that could go wrong.

**Inputs:**
- Subtask from Supervisor
- Shared state (reads findings from other agents)

**Process (ReAct):**
- Searches like: "{entity} lawsuit", "{entity} scam", "{entity} complaints", "{entity} class action"
- Looks on sites like: BBB, Reddit r/legaladvice, RipoffReport, state AG filings
- Cross-references with regulatory databases
- Assigns severity scores (low/medium/high/critical) to each red flag

**Output:**
```python
class RedFlag(BaseModel):
    severity: Severity  # LOW | MEDIUM | HIGH | CRITICAL
    description: str
    evidence: list[Finding]
    recommended_action: str
```

**LLM:** Claude Sonnet 4.6 (needs nuance — not every complaint is a red flag)

**Integration with Human-in-the-Loop:** Critical and High severity red flags trigger Checkpoint #2 — user reviews before brief generation.

---

### Agent 5: Perspective & Alternatives Analyst

**Job:** Find different viewpoints, counter-arguments, and alternatives the user hadn't considered.

**Process:**
1. For each key claim, search for counter-claims
2. Identify source bias (paid promotion, competitor content, anonymous reviews)
3. Find 3+ alternatives to whatever the user is considering
4. Analyze "the opposite case" — what would a skeptic say?

**Output:**
```python
class Perspective(BaseModel):
    stance: Stance  # SUPPORTING | OPPOSING | NEUTRAL
    summary: str
    source_type: SourceType  # ACADEMIC | JOURNALISM | OPINION | UGC | INDUSTRY
    bias_notes: str  # "paid content", "competitor", "anonymous", etc.
    evidence: list[Finding]

class Alternative(BaseModel):
    description: str
    why_consider: str
    tradeoffs: list[str]
    evidence: list[Finding]
```

**LLM:** Claude Sonnet 4.6

---

### Agent 6: Fact-Check Agent

**Job:** Verify every claim against its cited source. Flag contradictions between findings. Assign final confidence scores.

**Inputs:**
- All findings from other agents
- Original source documents (cached during scraping)

**Process:**
1. For each `Finding`: re-read the source, verify the claim is accurately represented
2. For each pair of contradictory findings: flag explicitly
3. Recompute confidence scores based on:
   - Source trust score
   - Number of corroborating sources
   - Source independence (not just repeating each other)
4. Detect "echo chambers" — multiple sources citing the same original

**Output:**
```python
class FactCheckResult(BaseModel):
    verified_findings: list[Finding]
    contradictions: list[Contradiction]
    unverifiable_findings: list[Finding]  # couldn't be verified
    corroboration_graph: dict  # finding_id → list of supporting finding_ids

class Contradiction(BaseModel):
    topic: str
    position_a: Finding
    position_b: Finding
    resolution: Literal["unresolved", "position_a_stronger", "position_b_stronger"]
    reasoning: str
```

**LLM:** GPT-4.1 (different model than the researchers — reduces systematic bias)

---

### Synthesis & Evaluation

After all 6 agents complete:

**Synthesis Agent (Claude Sonnet):**
- Combines findings into structured brief
- Groups claims by confidence tier (high/medium/low)
- Attributes every claim to source(s)
- Surfaces contradictions explicitly (doesn't silently resolve)
- Writes executive summary

**Quality Evaluator (LLM-as-Judge, Claude Sonnet):**
- Scores brief on 4 dimensions:
  - **Citation Coverage** — every claim has a source URL?
  - **Factual Consistency** — no internal contradictions?
  - **Completeness** — all plan subtasks covered?
  - **Actionability** — clear enough for user to act on?
- If any dimension < 0.85 → sends back to the responsible specialist for re-research (ReAct re-entry with specific gaps to fill)
- Max 2 re-research cycles

---

## 7. Phase-by-Phase Build Plan

### Phase 1: Foundation & Tools (Week 1)

**What we build:**
- Tool layer: web search wrapper (Tavily), web scraper (Firecrawl), PDF parser
- Data layer: ChromaDB for findings, Neo4j for knowledge graph, PostgreSQL for sessions
- Pydantic schemas for all agent inputs/outputs
- Pre-built RAG collections for 2-3 domains (legal, consumer) — start with Cornell LII + FTC

**Deliverable:** Given a URL, scrape it, extract text, embed it, store in ChromaDB. Given a query, retrieve relevant chunks.

---

### Phase 2: Supervisor + 3 Specialists (Week 2)

**What we build:**
- Supervisor Agent with plan-and-execute pattern
- Primary Researcher with ReAct loop + web search + scraping tools
- Domain Expert with RAG over pre-built collections
- Risk & Red Flag Analyst with red flag detection heuristics
- LangGraph wiring: parallel execution of 3 specialists after supervisor

**Deliverable:** Given a question, run 3 specialists in parallel, collect findings to shared state.

---

### Phase 3: Fact-Check, Synthesis, Evaluation (Week 2-3)

**What we build:**
- Perspective & Alternatives Analyst
- Fact-Check Agent
- Synthesis Agent
- LLM-as-Judge evaluator with 4-dimension scoring
- Re-research loop for low-scoring sections

**Deliverable:** Given parallel findings, fact-check, synthesize into a structured brief, score it, loop if needed.

---

### Phase 4: Human-in-the-Loop & UI (Week 3)

**What we build:**
- LangGraph interrupt nodes for 3 checkpoints
- LangGraph checkpointing (save state, resume later)
- CLI interface with Typer + Rich (approval prompts, progress bars)
- Optional web UI with Next.js + SSE for live progress streaming
- Brief rendering (Markdown + JSON output)

**Deliverable:** Full pipeline with 3 user approval points. User can approve/edit/reject plan, review red flags, review final brief.

---

### Phase 5: Memory, Evaluation, Polish (Week 4)

**What we build:**
- Knowledge graph accumulates entities across sessions (Company X researched before → reuse context)
- PostgreSQL memory store for past briefs (user can ask follow-ups)
- Eval benchmark: 10 test questions with expected characteristics
- Langfuse tracing for all LLM calls and cost tracking
- README with architecture diagram, demo video, benchmark results

**Deliverable:** Published tool with evaluation suite, demo video, and cost metrics.

---

## 8. Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Language** | Python 3.12+ | LangGraph is Python-first, ecosystem fit |
| **CLI Framework** | Typer + Rich | Type-annotated CLI, pretty terminal output |
| **Web UI** (optional) | Next.js + TypeScript | SSE streaming for live agent activity |
| **Backend API** | FastAPI | Async-native, works well with LangGraph |
| **Agent Orchestrator** | LangGraph | State machines, parallel branches, human-in-the-loop interrupts, persistence |
| **Primary LLM** | Claude Sonnet 4.6 | Nuanced reasoning for research tasks |
| **Secondary LLM** | GPT-4.1 | Fact-check agent (different model = reduces systematic bias) |
| **Routing LLM** | Gemini 2.5 Flash | Intent parsing, classification (cheap) |
| **Web Search** | Tavily API (primary) + Serper (fallback) | Tavily is purpose-built for AI agents; returns clean content |
| **Web Scraping** | Firecrawl API | Handles JS-rendered pages, returns clean markdown |
| **PDF Parsing** | PyMuPDF + LlamaParse (fallback for complex PDFs) | Local-first for simple cases, LLM-powered for complex layouts |
| **Vector Store** | ChromaDB | Local, simple, metadata filtering |
| **Knowledge Graph** | Neo4j (Community Edition) | Persistent entity/relationship tracking across sessions |
| **Relational DB** | PostgreSQL | Sessions, briefs, user context, agent memory |
| **Observability** | Langfuse (self-hosted) | Multi-agent trace visualization, cost tracking |
| **Evaluation** | Custom framework + Langfuse | LLM-as-judge with 4 dimensions |
| **Deployment** | Docker Compose | One-command local setup |

---

## 9. Concepts & Skills Covered

### Tier 1 — Must-Have (every AI job posting)

| Skill | Where in the project |
|-------|---------------------|
| **LLM Integration** | 3 providers (Claude, GPT-4.1, Gemini) with role-based routing |
| **RAG** | Pre-built domain collections (legal, medical, financial, consumer) + dynamic retrieval from scraped content |
| **Vector Databases** | ChromaDB for findings storage, metadata filtering |
| **Agentic Workflows** | 6-agent LangGraph pipeline with parallel execution and cycles |
| **Prompt Engineering** | Different system prompts per agent role, few-shot examples, ReAct pattern |
| **Tool Use / Function Calling** | Web search, scraping, PDF parsing, knowledge graph writes |
| **Python + TypeScript** | Python backend, optional TS/Next.js frontend |
| **Structured Outputs** | Pydantic validation on every agent input/output |

### Tier 2 — Strong Differentiators

| Skill | Where in the project |
|-------|---------------------|
| **Multi-Agent Collaboration** | 6 specialized agents with shared state + cross-agent reads |
| **ReAct Loops** | Each researcher agent iteratively reasons about what to search next |
| **Plan-and-Execute** | Supervisor decomposes question into dependency-ordered subtasks |
| **Human-in-the-Loop** | 3 checkpoints using LangGraph interrupt/resume |
| **Agent Memory** | Neo4j knowledge graph accumulates across sessions + PostgreSQL session history |
| **LLM-as-Judge Evaluation** | 4-dimension scoring (coverage, consistency, completeness, actionability) |
| **Compound AI Systems** | Multi-model routing, different models for different tasks |
| **AI Observability** | Langfuse tracing with per-agent cost attribution |
| **Contradiction Detection** | Fact-Check agent surfaces cross-source disagreements explicitly |
| **Source Bias Analysis** | Perspective Agent assesses and tags source trust/bias |

### Tier 3 — Emerging / Rare

| Skill | Where in the project |
|-------|---------------------|
| **Citation Tracking** | Every claim in the brief has a source URL and quote |
| **Confidence Calibration** | Explicit confidence scores, not just "the AI said so" |
| **Corroboration Graph** | Multi-source verification (independent sources, not echo chambers) |
| **Cost-Aware Model Routing** | Intent parsing on Flash ($0.001), reasoning on Sonnet ($0.18), fact-check on GPT-4.1 ($0.06) |

---

## 10. Example — End-to-End Walkthrough

### User input:
> "My car insurance claim was denied. They said the damage was 'pre-existing.' I've attached the denial letter. Do I have a case?"
> 
> `--context denial-letter.pdf`

### Phase 1: Understand
- Gemini Flash parses intent: consumer rights / insurance dispute
- Context loader extracts text from denial letter (PDF)
- Classifier: decision_type = "consumer_dispute", urgency = "high" (30-day appeal window)

### Phase 2: Plan (Supervisor)
```
Research Plan:
1. [DOMAIN_EXPERT] Research insurance dispute procedures and my state's regulations
2. [PRIMARY_RESEARCH] Find precedents for "pre-existing damage" denials
3. [RISK] Check if this insurer has complaint patterns on BBB, state DOI
4. [PERSPECTIVE] Find both insurer and consumer perspectives on pre-existing damage claims
5. [FACT_CHECK] Verify all claims and identify the strongest arguments

Estimated cost: $0.45
Estimated time: 8 minutes
```

**Checkpoint #1:** User reviews plan. Adds: "I'm in California." Approves.

### Phase 3: Research (Parallel)

**Domain Expert** runs RAG over California Department of Insurance + Cornell LII:
- Found: California Insurance Code §790.03 (unfair claims settlement practices)
- Found: CA DOI complaint procedure (online form, 30-day response)
- Found: "Pre-existing damage" must be documented BEFORE policy inception to be excluded

**Primary Researcher** runs ReAct loop:
- Searches "car insurance pre-existing damage denial California"
- Finds 3 consumer protection articles, 1 law firm blog, 1 forum discussion
- Searches for specific insurer ("Geico pre-existing damage complaints")
- Finds BBB complaint database with 23 similar cases

**Risk Analyst** searches for red flags:
- No lawsuits against this insurer for this specific practice
- Found: CA DOI has sanctioned this insurer 2x for bad-faith denials
- Moderate severity flag

**Checkpoint #2:** Red flags shown. User approves inclusion.

### Phase 4: Synthesis

**Synthesis Agent** produces:

```markdown
# Research Brief: Insurance Claim Denial — "Pre-existing Damage"

## Executive Summary
**Moderate confidence you have grounds for an appeal.** The denial letter cites 
"pre-existing damage" but does not provide evidence that the damage existed 
before policy inception. Under California law, the burden of proof for 
pre-existing damage exclusions is on the insurer.

**Confidence:** 0.82 | **Sources:** 18 | **Strongest argument:** CA Insurance Code §790.03(h)(4)

## Key Facts

### Legal Framework (High Confidence)
- Under CA Insurance Code §790.03, insurers must "attempt in good faith to 
  effectuate prompt, fair, and equitable settlements of claims." [Source: Cornell LII]
- Pre-existing damage exclusions require DOCUMENTATION from before policy 
  start. Mere visual assessment after a claim is insufficient. 
  [Source: CA DOI Guidance Bulletin 2019-03]
- You have 30 days from denial to file an internal appeal; 1 year to file 
  with CA DOI. [Source: CA DOI Consumer Guide]

### This Insurer's Record (Medium Confidence)
- ⚠ Sanctioned 2x by CA DOI for bad-faith denials (2022, 2024)
- BBB complaint database: 23 complaints for similar "pre-existing" denials
- [Source: CA DOI Enforcement Actions, BBB.org]

### Contradiction ⚠
Two sources disagree on appeal deadline:
- Source A (law firm blog): "60 days to appeal"
- Source B (CA DOI official guide): "30 days for internal appeal"
- **Resolution:** Source B (DOI) is authoritative. Use 30 days.

## Perspectives
- **Insurer position:** Assessment by their adjuster is sufficient evidence
- **Consumer position:** Burden of proof is on insurer per state regulation
- **Neutral:** Courts have ruled against insurers in ~65% of bad-faith cases 
  (no recent California-specific statistic available)

## Recommended Next Steps
1. File internal appeal within 30 days. Request the insurer's evidence of 
   pre-existing damage (specifically: documentation dated BEFORE your policy 
   start date).
2. If denied, file complaint with CA DOI online at insurance.ca.gov
3. If claim > $10,000, consult a consumer rights attorney (many work on 
   contingency)

## Unknowns
- Your specific policy terms (we couldn't analyze the full policy)
- Whether the adjuster's notes contain admissible evidence
- Any communications you had with the insurer about damage before claim

## Disclaimer
This is research, not legal advice. For a consultation on your specific 
situation, contact a California insurance dispute attorney.

---
Sources: [18 sources with URLs]
```

**Quality Evaluator scores:**
- Citation Coverage: 0.94 ✓
- Factual Consistency: 0.88 ✓
- Completeness: 0.91 ✓
- Actionability: 0.89 ✓

**Checkpoint #3:** User reviews brief. Approves. Done.

**Total:** $0.43, 7m 12s, 18 sources, brief saved.

---

## 11. Evaluation

### Automated Metrics (per brief)

1. **Citation Coverage**: `claims_with_source / total_claims`
2. **Source Diversity**: unique domains / total sources (higher = less echo chamber)
3. **Confidence Calibration**: for claims we can verify, does high-confidence = actually true?
4. **Contradiction Detection**: number of cross-source contradictions flagged
5. **Cost per brief**: target < $0.50 per typical question
6. **Time per brief**: target < 10 minutes

### Benchmark Suite

Create 10 test questions across diverse domains, each with ground-truth expected facts:

| # | Question | Domain | Expected findings |
|---|---------|--------|-------------------|
| 1 | Is this MLM pitch a scam? (with specific brand) | Financial | Documented FTC case, specific red flags |
| 2 | My landlord kept my security deposit. Rights in Texas? | Legal | Texas Property Code §92.103 (30-day rule) |
| 3 | Is this online bootcamp ($8K) worth it? (with specific brand) | Education | Outcomes data, alternative free resources |
| 4 | Should I accept this startup equity (0.3% at $20M valuation)? | Career | Market benchmarks, dilution risk |
| 5 | My flight was cancelled. Am I entitled to compensation in EU? | Consumer | EU Regulation 261/2004 specifics |
| ... | | | |

For each: run Clarity, compare output to ground truth, measure recall/precision of key facts.

### Human Evaluation

- 5 test users run 2 questions each
- Rate usefulness 1-10
- Compare to "what would you have done without Clarity?" (usually: 2 hours of Googling)
- Target: 8+ avg rating, 90%+ would use again

---

## 12. Week-by-Week Build Schedule

### Week 1: Foundation
- **Day 1-2:** Pydantic schemas, Typer CLI skeleton, PostgreSQL + Neo4j + ChromaDB setup
- **Day 3-4:** Tool layer (Tavily/Serper wrapper, Firecrawl wrapper, PDF parser)
- **Day 5:** Pre-built RAG collection for 1 domain (start with legal: Cornell LII)

### Week 2: Core Agents
- **Day 1:** LangGraph state + Supervisor Agent with plan-and-execute
- **Day 2:** Primary Researcher with ReAct loop + tools
- **Day 3:** Domain Expert with RAG
- **Day 4:** Risk & Red Flag Analyst
- **Day 5:** Wire up parallel execution, test with 1 real question end-to-end

### Week 3: Quality Layer
- **Day 1:** Perspective Analyst + Alternatives
- **Day 2:** Fact-Check Agent (with GPT-4.1 — different model for bias reduction)
- **Day 3:** Synthesis Agent + Brief rendering
- **Day 4:** LLM-as-Judge evaluator + re-research loop
- **Day 5:** Langfuse tracing, cost tracking

### Week 4: Human-in-the-Loop, Memory, Ship
- **Day 1:** LangGraph interrupts for 3 checkpoints
- **Day 2:** Knowledge graph persistence across sessions
- **Day 3:** Benchmark suite (10 test questions), run evals
- **Day 4:** README, architecture diagram, demo Loom video
- **Day 5:** Polish, publish to GitHub, write launch post

---

## 13. Resume Bullets

- Built a multi-agent personal research intelligence system with 6 specialized LangGraph agents (Supervisor, Primary Researcher, Domain Expert, Risk Analyst, Perspective Analyst, Fact-Check) that produces citation-backed research briefs for high-stakes personal decisions (career, legal, financial, consumer disputes).

- Implemented plan-and-execute orchestration with ReAct reasoning loops, 3 human-in-the-loop checkpoints (plan approval, risk review, final brief sign-off), and LangGraph interrupt/resume persistence for asynchronous user decisions without losing agent state.

- Designed a compound AI evaluation system using LLM-as-judge scoring across 4 quality dimensions (citation coverage, factual consistency, completeness, actionability), automatic contradiction detection across multi-source findings, and source bias analysis.

- Engineered cost-optimized multi-LLM workflows routing intent parsing to Gemini Flash ($0.001/query), research/reasoning to Claude Sonnet ($0.18/query), and fact-checking to GPT-4.1 ($0.06/query) with full per-agent cost attribution via Langfuse tracing.

- Built a persistent knowledge graph (Neo4j) that accumulates entity relationships across research sessions, enabling subsequent briefs to build on prior research with lower cost and higher context.

---

## Why This Project Stands Out

1. **Not a chatbot** — it's a structured research system that produces a citation-backed deliverable, not chat messages. This is the single biggest differentiator from every Perplexity/ChatGPT wrapper.

2. **Real human-in-the-loop** — 3 architecturally-integrated checkpoints using LangGraph interrupts, not fake "are you sure?" prompts. Shows you understand high-stakes AI workflows.

3. **Genuinely useful** — everyone has at least one "I don't know what to do" decision per year. You can demo this live with a real decision the interviewer has.

4. **Full AI concept coverage** — every Tier 1 and Tier 2 skill on AI job postings is demonstrated in a single project.

5. **Not code-heavy** — unlike the Codebase Tribal Knowledge Extractor, this project has zero code analysis. It demonstrates versatility across problem domains.

6. **Production thinking** — contradictions flagged (not silently resolved), confidence scores (not vibes), cost tracking (not "it just works"), cross-model bias reduction (Claude + GPT-4.1).

7. **Conversation starters for interviews:**
   - "Why use different models for research vs fact-check?"
   - "How do you detect contradictions across sources?"
   - "What happens when the Fact-Check agent can't verify a claim?"
   - "How do you prevent echo chambers where 5 sources all cite the same original?"
   - "Why 3 human checkpoints instead of full automation?"

Each is a 5-minute deep-dive that proves real AI engineering understanding.
