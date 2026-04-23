"""`apply bench` orchestrator — runs all three bench runners and writes a report."""
import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx

from apply.agents.runtime import company_researcher, fit_analyst, intake
from apply.config import get_settings
from eval.reports.markdown import render_bench_report
from eval.runners.company_research_bench import run_company_research_bench
from eval.runners.fit_bench import run_fit_bench
from eval.runners.intake_bench import run_intake_bench

GOLDENSET_DIR = Path("eval/goldenset")
REPORTS_DIR = Path("eval/reports")


async def _fetch_jd_text(url: str) -> str:
    """Fetch JD markdown via Firecrawl; fall back to raw HTTP."""
    settings = get_settings()
    if settings.firecrawl_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
                    json={"url": url, "formats": ["markdown"]},
                )
                if resp.status_code == 200:
                    md = resp.json().get("data", {}).get("markdown")
                    if md:
                        return md
        except Exception:
            pass
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            return resp.text[:50_000]
    except Exception:
        return ""


async def _company_brief(jd_id: str, company_name: str) -> str:
    """Simple company brief for fit analysis — one line."""
    return f"Company under consideration: {company_name} (JD: {jd_id})"


async def run_bench() -> Path:
    """Run all three benches and write a Markdown report. Returns report path."""
    settings = get_settings()
    if not settings.apply_use_real_agents:
        raise RuntimeError(
            "apply bench requires APPLY_USE_REAL_AGENTS=true and real API keys. "
            "Export them from .env first."
        )

    intake_results = await run_intake_bench(
        goldenset_path=GOLDENSET_DIR / "jds.json",
        intake_fn=intake,
        jd_fetch_fn=_fetch_jd_text,
    )
    company_results = await run_company_research_bench(
        goldenset_path=GOLDENSET_DIR / "jds.json",
        researcher_fn=company_researcher,
    )
    fit_results, fit_stats = await run_fit_bench(
        jds_path=GOLDENSET_DIR / "jds.json",
        resumes_path=GOLDENSET_DIR / "resumes.json",
        fit_pairs_path=GOLDENSET_DIR / "fit_pairs.json",
        fit_fn=fit_analyst,
        company_brief_fn=_company_brief,
    )

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    md = render_bench_report(
        intake=intake_results,
        company=company_results,
        fit=fit_results,
        fit_stats=fit_stats,
        run_timestamp=ts,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"bench-{ts}.md"
    out_path.write_text(md)
    return out_path


def main() -> None:
    path = asyncio.run(run_bench())
    print(f"Bench report written to: {path}")


if __name__ == "__main__":
    main()
