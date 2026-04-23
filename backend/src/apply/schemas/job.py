from pydantic import BaseModel, HttpUrl

from apply.schemas.enums import JobSource, RemoteType


class JobListing(BaseModel):
    id: str
    source: JobSource
    url: HttpUrl
    application_url: HttpUrl
    company_name: str
    role_title: str
    location: str
    remote_type: RemoteType
    description_markdown: str
    requirements: list[str]
    nice_to_haves: list[str]
    compensation_range: str | None = None
    raw_html_path: str
