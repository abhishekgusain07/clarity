from pydantic import BaseModel


class FilledField(BaseModel):
    name: str
    value: str
    field_type: str  # "text" | "textarea" | "file" | "select"


class UnknownField(BaseModel):
    name: str
    field_type: str
    best_guess: str | None = None
    reason_flagged: str


class FormFillResult(BaseModel):
    fields_filled: list[FilledField]
    unknown_fields: list[UnknownField]
    screenshot_path: str
    submission_url: str | None = None
    success: bool


async def form_fill_stub(
    application_url: str,
    cover_letter_body: str,
) -> FormFillResult:
    """Phase 1 stub: pretends to fill a YC WaaS application form."""
    return FormFillResult(
        fields_filled=[
            FilledField(name="full_name", value="Sanyam Upadhyay", field_type="text"),
            FilledField(name="email", value="you@example.com", field_type="text"),
            FilledField(name="linkedin", value="https://linkedin.com/in/...", field_type="text"),
            FilledField(name="resume", value="resume-v3.pdf", field_type="file"),
            FilledField(name="cover_letter", value=cover_letter_body, field_type="textarea"),
        ],
        unknown_fields=[
            UnknownField(
                name="salary_expectation",
                field_type="text",
                best_guess="$180k-$220k",
                reason_flagged="salary range varies by role seniority",
            ),
        ],
        screenshot_path="/tmp/apply/stub-screenshot.png",
        submission_url=None,  # not yet submitted
        success=True,
    )
