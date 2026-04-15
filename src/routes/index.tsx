import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/')({ component: Home })

function Home() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (email.trim()) {
      setSubmitted(true)
    }
  }

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
            COMING SOON
          </span>
        </div>

        <h1
          className="rise-in mx-auto max-w-[720px] font-serif text-[clamp(2.5rem,7vw,4.5rem)] leading-[1.08] tracking-tight text-[var(--text)]"
          style={{ animationDelay: '80ms' }}
        >
          Research intelligence for decisions that matter.
        </h1>

        <p
          className="rise-in mx-auto mt-6 max-w-lg text-[15px] leading-relaxed text-[var(--text-secondary)] sm:text-base"
          style={{ animationDelay: '160ms' }}
        >
          Tell it a decision you're wrestling with. Six specialist agents
          research in parallel and deliver a citation-backed
          brief&nbsp;&mdash;&nbsp;not a chat response.
        </p>

        <div className="rise-in mt-10" style={{ animationDelay: '240ms' }}>
          {!submitted ? (
            <form
              onSubmit={handleSubmit}
              className="mx-auto flex max-w-md flex-col gap-2.5 sm:flex-row"
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="flex-1 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)] px-4 py-3 text-sm text-[var(--text)] placeholder:text-[var(--text-tertiary)] outline-none transition focus:border-[var(--accent-border)]"
              />
              <button
                type="submit"
                className="cursor-pointer rounded-lg bg-[var(--accent)] px-6 py-3 text-sm font-medium text-white transition hover:bg-[var(--accent-hover)] active:scale-[0.98]"
              >
                Join the waitlist
              </button>
            </form>
          ) : (
            <p className="text-sm font-medium text-[var(--accent)]">
              Thanks&nbsp;&mdash;&nbsp;we'll be in touch.
            </p>
          )}
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
                clarity
              </span>
            </div>

            {/* Terminal body */}
            <div className="overflow-x-auto p-5 font-mono text-[13px] leading-[1.85] text-[#d4d4d4] sm:p-6">
              <Line>
                <Dim>$</Dim> clarity research{' '}
                <Accent>"Should I accept this job offer?"</Accent>
              </Line>

              <Spacer />
              <Line>
                <Dim>[Planning research...]</Dim>
              </Line>
              <Line>
                <Dim>{'  '}→ career decision, compensation, company eval</Dim>
              </Line>
              <Line>
                <Dim>{'  '}→ 6 subtasks assembled</Dim>
              </Line>

              <Spacer />
              <Line>
                <Dim>[Running 4 specialists in parallel...]</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Company Researcher <Dim>47 sources</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Market Analyst{'     '}
                <Dim>23 sources</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Role Analyst{'       '}
                <Dim>12 sources</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> Risk Analyst{'        '}
                <Dim>8 sources</Dim>
              </Line>

              <Spacer />
              <Line>
                <Dim>[Fact-checking...]</Dim>
              </Line>
              <Line>
                {'  '}
                <Green>✓</Green> 94 claims verified
              </Line>
              <Line>
                {'  '}
                <Amber>⚠</Amber> 3 contradictions flagged
              </Line>

              <div className="mt-5 border-t border-[rgba(255,255,255,0.06)] pt-4">
                <Line>
                  Brief saved → <Accent>job-offer-2026-04-12.md</Accent>
                </Line>
                <Line>
                  <Dim>
                    Confidence: <White>0.78</White> │ Sources:{' '}
                    <White>90</White> │ Cost: <White>$0.42</White> │{' '}
                    <White>6m 24s</White>
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
                'Research, not chat',
                'Six specialist agents attack your question from every angle — research, domain expertise, risk analysis, fact-checking.',
              ],
              [
                'Every claim cited',
                'Source URLs and confidence scores on every finding. Verify anything in the brief yourself.',
              ],
              [
                'Contradictions surfaced',
                'When sources disagree, you see both sides with evidence. Nothing silently resolved.',
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
      <section className="page-wrap px-4 pb-32">
        <div className="rise-in mx-auto max-w-xl text-center">
          <h2 className="font-serif text-[clamp(1.4rem,3.5vw,1.75rem)] leading-snug tracking-tight text-[var(--text)]">
            The gap between information and research is where costly mistakes
            happen.
          </h2>
          <p className="mt-5 text-sm leading-relaxed text-[var(--text-secondary)]">
            Google gives you twenty contradictory blog posts. ChatGPT gives
            confident hallucinations with no sources. A professional researcher
            costs $500&nbsp;an&nbsp;hour. Clarity gives you a structured brief
            with citations you can verify.
          </p>
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

function Amber({ children }: { children: React.ReactNode }) {
  return <span className="text-[#fbbf24]">{children}</span>
}

function Accent({ children }: { children: React.ReactNode }) {
  return <span className="text-[#d4956a]">{children}</span>
}

function White({ children }: { children: React.ReactNode }) {
  return <span className="text-[#d4d4d4]">{children}</span>
}
