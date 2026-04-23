import uuid
from datetime import datetime

from apply.schemas.writing import CoverLetter


async def cover_letter_writer_stub(application_id: str, company_name: str) -> CoverLetter:
    """Phase 1 stub: returns a believable fake cover letter."""
    body = (
        f"Dear {company_name} team,\n\n"
        f"I read your recent Series A announcement and the blog post on "
        f"long-running agents with a lot of interest. The framing of "
        f"treating agents as products rather than features resonates with "
        f"work I've been doing independently.\n\n"
        f"Over the last five years I've been a Python engineer focused on "
        f"async systems and, more recently, multi-agent orchestration. "
        f"I'm currently building an applications copilot that uses Pydantic "
        f"AI and Claude Agent SDK — the same stack your job description "
        f"implies. I'd love to talk.\n\n"
        f"Thanks for your time,\nSanyam"
    )
    return CoverLetter(
        id=f"cl-{uuid.uuid4().hex[:8]}",
        application_id=application_id,
        draft_version=1,
        body_markdown=body,
        word_count=len(body.split()),
        references_company_specifics=[
            "Series A announcement",
            "long-running agents blog post",
            "agent-product framing",
        ],
        voice_similarity_score=0.71,
        created_at=datetime.utcnow(),
    )
