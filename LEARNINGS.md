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
