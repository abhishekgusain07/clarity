"""Live Form-Fill test against a local HTML form.

Opt-in: requires APPLY_OPENROUTER_API_KEY. Costs ~$0.10-0.30 per run.
Not run in CI.
"""
import os
from pathlib import Path

import pytest

from apply.agents.form_context import FormFillDeps

REQUIRED = ("APPLY_OPENROUTER_API_KEY",)
_HAS_KEY = all(os.getenv(k) for k in REQUIRED)


@pytest.mark.skipif(not _HAS_KEY, reason="APPLY_OPENROUTER_API_KEY not set")
@pytest.mark.asyncio
async def test_form_fill_local_html(monkeypatch):
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")
    from apply import config as cfg
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]

    from apply.agents import runtime

    form_path = Path(__file__).parent.parent / "fixtures/simple_application_form.html"
    url = f"file://{form_path.resolve()}"

    deps = FormFillDeps(
        application_url=url,
        profile={
            "full_name": "Sanyam Upadhyay",
            "email": "satish@team.galaxy.ai",
            "github_url": "https://github.com/sanyamupadhyay",
        },
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, this is a test cover letter drafted for integration testing.",
        company_name="Test Corp",
        company_brief="A local HTML test form",
        jd_markdown="Test Engineer role.",
        voice_samples=["The discipline that makes good backend code makes good agent code."],
    )

    result = await runtime.form_fill(deps=deps)

    # Core fields the agent should fill
    filled_names = {f.name for f in result.fields_filled}
    assert "full_name" in filled_names or "name" in filled_names, (
        f"expected full_name/name in filled, got {filled_names}"
    )
    assert "email" in filled_names, f"expected email in filled, got {filled_names}"
    assert "cover_letter" in filled_names, f"expected cover_letter in filled, got {filled_names}"

    # The `why_us` screening question should be handled — either answered via
    # the tool (appears in filled_names) or flagged as unknown. Both are OK.
    unknown_names = {u.name for u in result.unknown_fields}
    assert "why_us" in filled_names or "why_us" in unknown_names
