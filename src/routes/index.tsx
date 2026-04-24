import { createFileRoute, Link } from '@tanstack/react-router'
import { Github, GitCommitHorizontal } from 'lucide-react'

export const Route = createFileRoute('/')({ component: Home })

const REPO_URL = 'https://github.com/abhishekgusain07/clarity'

const STACK: ReadonlyArray<{
  group: string
  items: ReadonlyArray<string>
}> = [
  {
    group: 'Frontend',
    items: [
      'TanStack Start',
      'React 19',
      'TypeScript',
      'Tailwind v4',
      'Vite',
      'Lucide',
    ],
  },
  {
    group: 'Backend',
    items: [
      'FastAPI',
      'Pydantic AI',
      'SQLAlchemy + asyncpg',
      'Alembic',
      'SSE streaming',
      'FastMCP',
    ],
  },
  {
    group: 'Agents & infra',
    items: [
      'Claude Haiku + Sonnet (OpenRouter)',
      'GPT-4.1 judge (OpenRouter)',
      'Tavily MCP',
      'Firecrawl MCP',
      'Playwright MCP',
      'Chroma + Postgres memory',
      'Langfuse traces',
    ],
  },
]

const CHANGELOG: ReadonlyArray<{
  date: string
  phase: string
  title: string
  body: string
}> = [
  {
    date: '2026-04-24',
    phase: 'V1',
    title: 'Frontend rebrand — Clarity → Apply',
    body: 'Front page, header, and footer aligned with the new product. GitHub source link surfaced.',
  },
  {
    date: '2026-04-24',
    phase: 'Phase 5a',
    title: 'Dashboard + outcome logging',
    body: 'Applications list, detail view, outcome marking, and aggregated stats — all wired to real APIs (`GET /applications`, `PATCH /applications/{id}/outcome`, `GET /dashboard/stats`).',
  },
  {
    date: '2026-04-24',
    phase: 'Phase 4a',
    title: 'Form-Fill agent',
    body: 'Real Form-Fill via Pydantic AI + Playwright MCP routed through OpenRouter. Typed FormFillDeps run-time context, opt-in integration test against a local HTML form.',
  },
  {
    date: '2026-04-24',
    phase: 'Phase 3b',
    title: 'memory-mcp + cross-model judge',
    body: 'memory-mcp FastMCP server (Postgres + Chroma) with Memory Curator agent. Cover-letter bench (S vs B1) scored by GPT-4.1 judge via OpenRouter on a 4-dimension rubric.',
  },
  {
    date: '2026-04-23',
    phase: 'Phase 3a',
    title: 'Cover Letter Writer + Screening Answerer',
    body: 'Voice-profiled cover letters and screening-question answers, routed through the orchestrator with a real voice corpus loader.',
  },
  {
    date: '2026-04-23',
    phase: 'Phase 1–2',
    title: 'Walking skeleton',
    body: 'Spec, FastAPI scaffolding, Pydantic AI orchestrator, and the first three agents (Intake, Company Researcher, Fit Analyst) under a stub/real runtime switch.',
  },
]

function Home() {
  return (
    <main className="relative z-10">
      {/* ── Hero ── */}
      <section className="page-wrap px-4 pt-24 pb-20 text-center sm:pt-36 sm:pb-28">
        <div className="rise-in mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--accent-border)] bg-[var(--accent-soft)] px-4 py-1.5">
          <span
            className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]"
            style={{ animation: 'pulse-dot 2.5s ease-in-out infinite' }}
          />
          <span className="text-[11px] font-medium tracking-[0.14em] text-[var(--accent)]">
            V1 — LIVE
          </span>
        </div>

        <h1
          className="rise-in mx-auto max-w-[780px] font-serif text-[clamp(2.5rem,7vw,4.5rem)] leading-[1.08] tracking-tight text-[var(--text)]"
          style={{ animationDelay: '80ms' }}
        >
          Recruiter-quality applications. One URL at a time.
        </h1>

        <p
          className="rise-in mx-auto mt-6 max-w-xl text-[15px] leading-relaxed text-[var(--text-secondary)] sm:text-base"
          style={{ animationDelay: '160ms' }}
        >
          Paste a job link. Seven specialist agents research the company,
          build a quote-backed fit analysis, draft a cover letter in your
          voice, and fill the form&nbsp;&mdash;&nbsp;with your approval at
          three checkpoints before anything submits.
        </p>

        <div
          className="rise-in mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row"
          style={{ animationDelay: '240ms' }}
        >
          <Link
            to="/applications/new"
            className="cursor-pointer rounded-lg bg-[var(--accent)] px-6 py-3 text-sm font-medium text-white! no-underline transition hover:bg-[var(--accent-hover)] hover:text-white! active:scale-[0.98]"
          >
            Start an application
          </Link>
          <Link
            to="/dashboard"
            className="cursor-pointer rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)] px-6 py-3 text-sm font-medium text-[var(--text)]! no-underline transition hover:border-[var(--accent-border)]"
          >
            View dashboard
          </Link>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium text-[var(--text-secondary)]! no-underline transition hover:text-[var(--text)]!"
          >
            <Github className="h-4 w-4" />
            Source on GitHub
          </a>
        </div>
      </section>

      {/* ── Terminal Demo ── */}
      <section className="page-wrap px-4 pb-28">
        <div
          className="rise-in mx-auto max-w-2xl"
          style={{ animationDelay: '320ms' }}
        >
          <div className="overflow-hidden rounded-xl bg-[#0c0c0c] shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_32px_64px_rgba(0,0,0,0.32),0_8px_20px_rgba(0,0,0,0.18)]">
            {/* Window chrome */}
            <div className="flex items-center gap-1.5 border-b border-[rgba(255,255,255,0.06)] px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-[rgba(255,255,255,0.08)]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[rgba(255,255,255,0.08)]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[rgba(255,255,255,0.08)]" />
              <span className="ml-3 font-mono text-[11px] text-[rgba(255,255,255,0.2)]">
                apply
              </span>
            </div>

            {/* Terminal body */}
            <div className="overflow-x-auto p-5 font-mono text-[13px] leading-[1.85] text-[#d4d4d4] sm:p-6">
              <Line>
                <Dim>$</Dim> apply submit{' '}
                <Accent>https://jobs.ycombinator.com/founding-engineer</Accent>
              </Line>

              <Spacer />
              <Line>
                <Dim>[Intake — parsing JD...]</Dim>
              </Line>
              <Line>
                <Dim>{'  '}→ Founding Engineer, AI · Seed · $180k–$220k</Dim>
              </Line>
              <Line>
                <Dim>{'  '}→ 14 requirements extracted</Dim>
              </Line>

              <Spacer />
              <Line>
                <Dim>[Dispatching 7 agents...]</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Company Researcher{'    '}
                <Dim>31 sources</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Fit Analyst{'           '}
                <Dim>12 JD quotes matched</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Voice Profiler{'        '}
                <Dim>4 writing samples</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Cover Letter Writer{'   '}
                <Dim>draft v2 · 312 words</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Form Filler{'           '}
                <Dim>18 fields mapped</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Memory Curator{'        '}
                <Dim>2 similar past outcomes</Dim>
              </Line>

              <Spacer />
              <Line>
                <Dim>[Human-in-the-loop checkpoints]</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Fit gate{'       '}
                <Dim>approved</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Content review{' '}
                <Dim>approved</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Submit{'         '}
                <Dim>approved</Dim>
              </Line>

              <div className="mt-5 border-t border-[rgba(255,255,255,0.06)] pt-4">
                <Line>
                  Application submitted →{' '}
                  <Accent>/applications/a7f3…</Accent>
                </Line>
                <Line>
                  <Dim>
                    Fit: <White>0.81</White> │ Sources:{' '}
                    <White>31</White> │ Cost: <White>$0.64</White> │{' '}
                    <White>4m 12s</White>
                  </Dim>
                </Line>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="page-wrap px-4 pb-28">
        <div className="mx-auto grid max-w-3xl gap-12 sm:grid-cols-3">
          {(
            [
              [
                'Researches the company',
                'Recent news, founder background, funding stage, their own blog. A 30-source brief before a single word of the cover letter is written.',
              ],
              [
                'Your voice, not ChatGPT’s',
                'Cover letters voice-profiled from your past writing. Fit reasoning backed by resume + JD quotes — not vibes.',
              ],
              [
                'Three checkpoints before submit',
                'Fit gate, content review, submit approval. Nothing leaves your machine without your yes. Learns from what lands replies.',
              ],
            ] as const
          ).map(([title, desc], i) => (
            <div
              key={title}
              className="rise-in"
              style={{ animationDelay: `${i * 100 + 100}ms` }}
            >
              <div className="mb-4 h-px w-8 bg-[var(--accent)] opacity-40" />
              <h3 className="mb-2 text-[15px] font-semibold text-[var(--text)]">
                {title}
              </h3>
              <p className="m-0 text-sm leading-relaxed text-[var(--text-secondary)]">
                {desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Manifesto ── */}
      <section className="page-wrap px-4 pb-28">
        <div className="rise-in mx-auto max-w-xl text-center">
          <h2 className="font-serif text-[clamp(1.4rem,3.5vw,1.75rem)] leading-snug tracking-tight text-[var(--text)]">
            Apply deliberately.
          </h2>
          <p className="mt-5 text-sm leading-relaxed text-[var(--text-secondary)]">
            The category is a race to the bottom — blast 750 generic
            applications a day and hope one sticks. Recruiters smell that
            output and ignore it. Five bespoke applications you&rsquo;d
            sign your name to beat five hundred you wouldn&rsquo;t.
          </p>
        </div>
      </section>

      {/* ── Built on ── */}
      <section className="page-wrap px-4 pb-28">
        <div className="mx-auto max-w-3xl">
          <div className="rise-in mb-10 text-center">
            <p className="island-kicker mb-2 text-[11px] font-medium tracking-[0.14em] text-[var(--accent)]">
              BUILT ON
            </p>
            <h2 className="font-serif text-[clamp(1.4rem,3.5vw,1.75rem)] leading-snug tracking-tight text-[var(--text)]">
              Real 2026 primitives. No magic.
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-[var(--text-secondary)]">
              Pydantic AI for orchestration. MCP servers for every tool.
              OpenRouter so we can swap models. Langfuse so we can see
              every call.
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {STACK.map((col, i) => (
              <div
                key={col.group}
                className="rise-in"
                style={{ animationDelay: `${i * 100 + 100}ms` }}
              >
                <div className="mb-4 h-px w-8 bg-[var(--accent)] opacity-40" />
                <h3 className="mb-3 text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--text)]">
                  {col.group}
                </h3>
                <ul className="m-0 flex flex-wrap gap-1.5 p-0">
                  {col.items.map((tech) => (
                    <li
                      key={tech}
                      className="list-none rounded-md border border-[var(--border)] bg-[var(--bg-elevated)] px-2.5 py-1 text-[12px] text-[var(--text-secondary)]"
                    >
                      {tech}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Changelog ── */}
      <section className="page-wrap px-4 pb-32">
        <div className="mx-auto max-w-2xl">
          <div className="rise-in mb-10 flex items-end justify-between gap-4">
            <div>
              <p className="island-kicker mb-2 text-[11px] font-medium tracking-[0.14em] text-[var(--accent)]">
                CHANGELOG
              </p>
              <h2 className="font-serif text-[clamp(1.4rem,3.5vw,1.75rem)] leading-snug tracking-tight text-[var(--text)]">
                How we got here.
              </h2>
            </div>
            <a
              href={`${REPO_URL}/commits/master`}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex shrink-0 items-center gap-1.5 text-xs text-[var(--text-secondary)] no-underline transition hover:text-[var(--text)]"
            >
              <Github className="h-3.5 w-3.5" />
              Full history
            </a>
          </div>

          <ol className="relative m-0 list-none border-l border-[var(--border)] p-0 pl-6">
            {CHANGELOG.map((entry, i) => (
              <li
                key={`${entry.date}-${entry.phase}`}
                className="rise-in relative pb-8 last:pb-0"
                style={{ animationDelay: `${i * 60 + 80}ms` }}
              >
                <span className="absolute -left-[31px] top-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full border border-[var(--accent-border)] bg-[var(--bg)] text-[var(--accent)]">
                  <GitCommitHorizontal className="h-3 w-3" />
                </span>
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <time className="font-mono text-[11px] text-[var(--text-tertiary)]">
                    {entry.date}
                  </time>
                  <span className="rounded-md border border-[var(--accent-border)] bg-[var(--accent-soft)] px-1.5 py-0.5 text-[10px] font-medium tracking-[0.08em] text-[var(--accent)]">
                    {entry.phase}
                  </span>
                </div>
                <h3 className="mb-1 text-[14px] font-semibold text-[var(--text)]">
                  {entry.title}
                </h3>
                <p className="m-0 text-[13px] leading-relaxed text-[var(--text-secondary)]">
                  {entry.body}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </main>
  )
}

/* ── Tiny helper components for terminal readability ── */

function Line({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>
}

function Spacer() {
  return <div className="mt-5" />
}

function Dim({ children }: { children: React.ReactNode }) {
  return <span className="text-[#555]">{children}</span>
}

function Green({ children }: { children: React.ReactNode }) {
  return <span className="text-[#4ade80]">{children}</span>
}

function Accent({ children }: { children: React.ReactNode }) {
  return <span className="text-[#d4956a]">{children}</span>
}

function White({ children }: { children: React.ReactNode }) {
  return <span className="text-[#d4d4d4]">{children}</span>
}
