import { Link } from '@tanstack/react-router'
import ThemeToggle from './ThemeToggle'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--header-bg)] px-4 backdrop-blur-xl">
      <nav className="page-wrap flex items-center justify-between py-4">
        <Link
          to="/"
          className="font-serif text-xl tracking-tight text-[var(--text)] no-underline"
        >
          Clarity
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/applications" className="text-sm hover:underline">
            Applications
          </Link>
          <Link to="/dashboard" className="text-sm hover:underline">
            Dashboard
          </Link>
          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
