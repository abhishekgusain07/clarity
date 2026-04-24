# Learnings — Apply

A running log of non-obvious things learned building this project.

## Top 5 lessons (synthesized, updated as we go)

_Will fill as patterns emerge._

## Index by tag

- `agent-design`
- `prompt-engineering`
- `mcp`
- `tooling`
- `debugging`
- `architecture`
- `product-decisions`
- `eval`

---

## YYYY-MM-DD — template entry
Tags: tag-1, tag-2

[Context: what I was doing]

[What happened / what I found]

**Takeaway:** [the insight, not the event]

## 2026-04-23 — Walking-skeleton-first paid off
Tags: architecture, product-decisions

Built the complete pipeline with stub agents before touching any real
LLM calls. Took about 20 hours. By the time the skeleton was running,
every hard architectural question — HITL state machine, SSE event
streaming, frontend/backend boundary, run persistence — was answered.

The payoff: when Phase 2 replaces stubs with real agents, none of those
answers have to change. Replacing one stub at a time is a much smaller
refactor than simultaneously implementing the agent AND figuring out how
approval resumes it AND how events stream to the UI.

**Takeaway:** for any project with >3 layers of integration (agents +
state machine + streaming + UI), build the skeleton first with fakes.
The cost of the skeleton is a fraction of the cost of integration bugs
discovered in week 4.

---

## 2026-04-23 — Stub/real runtime switch isolates skeleton from LLM dependencies
Tags: architecture, agent-design, product-decisions

Shipped Phase 2a (real Intake + Company Researcher + Fit Analyst) behind an
`APPLY_USE_REAL_AGENTS` env flag. The orchestrator only ever calls
`apply.agents.runtime.*`; the runtime module decides stub vs real based
on config at the point of call.

Why this mattered:
- Unit tests don't need API keys or network
- The skeleton demo still works when keys aren't configured
- Future chunks can replace agents one at a time the same way — the
  runtime module grows one entry per replacement
- VCR cassettes capture LLM shapes once, so tests stay fast and
  deterministic even as we add real calls

**Takeaway:** when adding a layer that has two implementations (stub/real,
local/cloud, batch/stream), put the switch at the module boundary, not
inside agent code. One clean env flag, one routing file, one line in every
test to flip it.

---

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

## 2026-04-23 — Voice similarity is the real differentiator
Tags: agent-design, eval, product-decisions

The Cover Letter Writer's USP isn't the cover letter — it's the
voice-similarity score the user sees in HITL #2. Every auto-apply tool
produces SOME text; only this one tells you how close to your actual
writing style the draft landed.

Implementation: OpenAI `text-embedding-3-small` ($0.02/1M tokens),
max cosine similarity between the draft and each sample in the
user's corpus. Max (not mean) because a draft that resembles ANY of
the user's writings is in-voice; mean gets diluted across kinds (essay
vs cover letter vs email).

Voice-similarity is computed OUT-OF-BAND after the agent returns the
draft — not as a tool call during generation. Reason: asking the LLM
to self-assess its own voice match creates a feedback loop where the
model reports whatever it thinks you want to hear. Embedding similarity
is model-independent and gives you a number you can trust.

**Takeaway:** when a metric will end up in a recruiter-facing
interview story, compute it from a different system than the one
being measured. Self-scoring is cheap theater; cross-system
scoring is information.

---

## 2026-04-24 — Cross-model judging is the only honest eval
Tags: eval, product-decisions, architecture

Shipped Phase 3b: memory-mcp, Memory Curator real, LLM-as-judge for
cover letters (GPT-4.1 via OpenRouter), and a 2-way baseline comparison
(full Apply pipeline vs Claude-one-shot).

Critical design decision: judge and writer are DIFFERENT models.
Judging Claude output with Claude produces inflated scores — the model
recognizes its own stylistic tells and rewards them. GPT-4.1 has no such
bias for Claude-generated text. 1-2 points of difference in mean scores
from this alone, consistently.

memory-mcp is intentionally minimal in 3b: 3 tools (already_applied,
similar_applications, what_landed_replies) backed by Postgres + Chroma.
Embeddings are best-effort — if OpenAI is rate-limited or unavailable,
the outcome row still logs; only the similarity index is skipped.

**Takeaway:** cross-system validation is the cheap version of
cross-team review. When the thing being measured and the thing doing
the measuring come from the same model family, you're grading your own
homework.

---

## 2026-04-24 — MCP toolsets beat a purpose-built SDK for structured forms
Tags: agent-design, architecture, product-decisions

Initially scoped Phase 4a around Claude Agent SDK + computer-use (the
hot 2026 skill). Reversed course to use Pydantic AI + Playwright MCP
via OpenRouter instead. Reasons:

1. Same keys we already have (OpenRouter) — no funded Anthropic account
   needed for dev.
2. Playwright MCP's structured tools (`fill(selector, value)`) are
   strictly better than coordinate-clicking via screenshot for HTML
   forms — faster, cheaper, more reliable, no OCR.
3. Architectural consistency: Company Researcher already uses
   Tavily+Firecrawl MCP toolsets in Pydantic AI. Form-Fill uses the
   same pattern with Playwright MCP. One mental model for all agents.
4. The "I chose accessibility-tree over computer-use for structured
   forms" story is a stronger interview signal than "I used the SDK
   out of the box."

What we lose: the literal "Claude Agent SDK on the resume" name-drop.
What we keep: the browser-driving agent, the dynamic multi-agent
callback (`answer_screening_question` as an agent tool), the screenshot
preview for HITL #3, and the real form submission path.

The screening callback via Pydantic AI's `deps` + `RunContext[T].deps`
pattern is genuinely elegant. The agent's tool accesses pipeline
context through dependency injection, not closure capture — makes the
agent unit-testable without pipeline state.

**Takeaway:** reach for the lighter tool when you have the choice.
An MCP server + a tool-use-capable LLM is almost always enough for
structured work. Computer-use (screenshot + coordinates) is only
necessary when there's no structured accessor.

---
