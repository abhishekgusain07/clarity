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
