"""Typed dependency bundle injected into the Form-Fill agent at run time.

Pydantic AI's `deps` pattern lets the agent's custom tools access this
context via `RunContext[FormFillDeps].deps`. Frozen to prevent mutation
mid-run.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormFillDeps:
    application_url: str
    profile: dict[str, str]
    resume_pdf_path: str
    cover_letter_text: str
    company_name: str
    company_brief: str
    jd_markdown: str
    voice_samples: list[str]
