from apply.agents.form_context import FormFillDeps


def test_form_fill_deps_fields():
    deps = FormFillDeps(
        application_url="https://example.com/apply",
        profile={"full_name": "Sanyam Upadhyay", "email": "e@x.co"},
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear team, …",
        company_name="Acme AI",
        company_brief="Series A agent startup",
        jd_markdown="Engineer role",
        voice_samples=["Sample."],
    )
    assert deps.profile["full_name"] == "Sanyam Upadhyay"
    assert deps.company_name == "Acme AI"
    assert deps.resume_pdf_path == "/tmp/resume.pdf"


def test_form_fill_deps_is_frozen():
    """Deps should be safe to share across tool invocations — immutable."""
    import dataclasses

    from apply.agents.form_context import FormFillDeps
    assert dataclasses.is_dataclass(FormFillDeps)
