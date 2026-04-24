import { Link } from '@tanstack/react-router'
import { Github } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

const REPO_URL = 'https://github.com/abhishekgusain07/clarity'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--header-bg)] px-4 backdrop-blur-xl">
      <nav className="page-wrap flex items-center justify-between py-4">
        <Link
          to="/"
          className="font-serif text-xl tracking-tight text-[var(--text)] no-underline"
        >
          Apply
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/applications" className="text-sm hover:underline">
            Applications
          </Link>
          <Link to="/dashboard" className="text-sm hover:underline">
            Dashboard
          </Link>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer noopener"
            aria-label="View source on GitHub"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[var(--text-secondary)] transition hover:bg-[var(--bg-elevated)] hover:text-[var(--text)]"
          >
            <Github className="h-4 w-4" />
          </a>
          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
