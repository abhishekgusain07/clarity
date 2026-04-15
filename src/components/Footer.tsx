export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)] px-4 py-8">
      <div className="page-wrap text-center">
        <p className="m-0 text-xs text-[var(--text-tertiary)]">
          &copy; {new Date().getFullYear()} Clarity
        </p>
      </div>
    </footer>
  )
}
